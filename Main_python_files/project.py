import streamlit as st
import json
import boto3
import time

from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from langchain_community.retrievers import AmazonKendraRetriever

from TextExtract.text_extract import extract_text_from_pdf
from Tabular_processing.table_to_text import table_to_readable_paragraph
from Translation.translate import translate_text_with_aws
from TextExtract import extract_image 
##main project file   
# AWS S3 Configuration
S3_BUCKET = 'idpproject'       # Replace with your bucket name
S3_REGION = 'us-east-1'        # e.g., 'us-east-1'
AWS_ACCESS_KEY = '##'   # Replace with your AWS access key
 # Replace with your AWS access key
AWS_SECRET_KEY = '##'  # Replace with your AWS secret key'

# Initialize AWS Clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)
boto3_bedrock = boto3.client('bedrock-runtime',region_name='us-east-1',aws_access_key_id='##',aws_secret_access_key='##')

kendra_client=boto3.client('kendra',region_name='us-east-1',aws_access_key_id='##',aws_secret_access_key='##')
from langchain_community.retrievers import AmazonKendraRetriever

retriever = AmazonKendraRetriever(index_id="##",client =kendra_client,min_score_confidence=0.5)

textract_client = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)

kendra_client = boto3.client(
    'kendra',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)
st.title("MultiLingual Document Processing")

# Full list of languages supported by Tesseract
languages = {
    "Afrikaans": "afr",
    "Albanian": "sqi",
    "Amharic": "amh",
    "Arabic": "ara",
    "Armenian": "hye",
    "Azerbaijani": "aze",
    "Basque": "eus",
    "Belarusian": "bel",
    "Bengali": "ben",
    "Bosnian": "bos",
    "Breton": "bre",
    "Bulgarian": "bul",
    "Catalan": "cat",
    "Cebuano": "ceb",
    "Cherokee": "chr",
    "Chinese (Simplified)": "chi_sim",
    "Chinese (Traditional)": "chi_tra",
    "Corsican": "cos",
    "Croatian": "hrv",
    "Czech": "ces",
    "Danish": "dan",
    "Dutch": "nld",
    "English": "eng",
    "Esperanto": "epo",
    "Estonian": "est",
    "Finnish": "fin",
    "French": "fra",
    "Galician": "glg",
    "Georgian": "kat",
    "German": "deu",
    "Greek": "ell",
    "Gujarati": "guj",
    "Haitian Creole": "hat",
    "Hebrew": "heb",
    "Hindi": "hin",
    "Hungarian": "hun",
    "Icelandic": "isl",
    "Indonesian": "ind",
    "Irish": "gle",
    "Italian": "ita",
    "Japanese": "jpn",
    "Javanese": "jav",
    "Kannada": "kan",
    "Kazakh": "kaz",
    "Khmer": "khm",
    "Korean": "kor",
    "Kurdish": "kur",
    "Lao": "lao",
    "Latin": "lat",
    "Latvian": "lav",
    "Lithuanian": "lit",
    "Luxembourgish": "ltz",
    "Macedonian": "mkd",
    "Malagasy": "mlg",
    "Malay": "msa",
    "Malayalam": "mal",
    "Maltese": "mlt",
    "Maori": "mri",
    "Marathi": "mar",
    "Mongolian": "mon",
    "Nepali": "nep",
    "Norwegian": "nor",
    "Occitan": "oci",
    "Pashto": "pus",
    "Persian": "fas",
    "Polish": "pol",
    "Portuguese": "por",
    "Punjabi": "pan",
    "Quechua": "que",
    "Romanian": "ron",
    "Russian": "rus",
    "Sanskrit": "san",
    "Scots Gaelic": "gla",
    "Serbian": "srp",
    "Sinhala": "sin",
    "Slovak": "slk",
    "Slovenian": "slv",
    "Somali": "som",
    "Spanish": "spa",
    "Sundanese": "sun",
    "Swahili": "swa",
    "Swedish": "swe",
    "Tagalog": "tgl",
    "Tajik": "tgk",
    "Tamil": "tam",
    "Tatar": "tat",
    "Telugu": "tel",
    "Thai": "tha",
    "Tibetan": "bod",
    "Tigrinya": "tir",
    "Turkish": "tur",
    "Uighur": "uig",
    "Ukrainian": "ukr",
    "Urdu": "urd",
    "Uzbek": "uzb",
    "Vietnamese": "vie",
    "Welsh": "cym",
    "Xhosa": "xho",
    "Yiddish": "yid",
    "Yoruba": "yor",
    "Zulu": "zul"
}

# Language selection dropdown
selected_language = st.selectbox("Select the language of the document:", list(languages.keys()))
is_table = st.selectbox("Is the uploaded file have tables or Not?", ["Select", "Yes", "No"])
# Define the API URL and authentication header for Hugging Face Inference API



def upload_file_to_s3(file, bucket, file_name):
    try:
        s3_client.upload_fileobj(
            file,
            bucket,
            file_name,
            ExtraArgs={'ContentType': 'text/plain'}
        )
        file_url = f"https://{bucket}.s3.{S3_REGION}.amazonaws.com/{file_name}"
        return file_url
    except NoCredentialsError:
        st.error("AWS credentials not available.")
        return None
    except PartialCredentialsError:
        st.error("Incomplete AWS credentials.")
        return None
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Function to start the Textract job
def start_textract_job(client, s3_bucket_name, object_name):
    response = client.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': s3_bucket_name,
                'Name': object_name
            }
        })
    return response["JobId"]

# Function to check if the Textract job is complete
def is_job_complete(client, job_id):
    time.sleep(1)
    response = client.get_document_text_detection(JobId=job_id)
    status = response["JobStatus"]
    while status == "IN_PROGRESS":
        time.sleep(1)
        response = client.get_document_text_detection(JobId=job_id)
        status = response["JobStatus"]
    return status

# Function to get the results of the Textract job
def get_textract_results(client, job_id):
    pages = []
    time.sleep(1)
    response = client.get_document_text_detection(JobId=job_id)
    pages.append(response)
    next_token = response.get('NextToken')
    while next_token:
        time.sleep(1)
        response = client.get_document_text_detection(JobId=job_id, NextToken=next_token)
        pages.append(response)
        next_token = response.get('NextToken')
    return pages



# Function to extract tables and store in text key-value pairs
def extract_tables_with_textract(file_key):
   
    response = textract_client.start_document_analysis(
        DocumentLocation={"S3Object": {"Bucket": S3_BUCKET, "Name": file_key}},
        FeatureTypes=["TABLES"]
    )
    job_id = response["JobId"]

    while True:
        status = textract_client.get_document_analysis(JobId=job_id)
        if status["JobStatus"] == "SUCCEEDED":
            break
        elif status["JobStatus"] == "FAILED":
            st.error("Textract job failed.")
            return []

        time.sleep(5)
    
    key_value_pairs = {}
    for block in status["Blocks"]:
        if block["BlockType"] == "CELL":
            row_index = block.get("RowIndex", 0)
            column_index = block.get("ColumnIndex", 0)
            text = ""
            if "Relationships" in block:
                for rel in block["Relationships"]:
                    if rel["Type"] == "CHILD":
                        for child_id in rel["Ids"]:
                            for item in status["Blocks"]:
                                if item["Id"] == child_id and item["BlockType"] == "WORD":
                                    text += item["Text"] + " "
            key_value_pairs[f"Row {row_index} Column {column_index}"] = text.strip()
    return key_value_pairs

import os

def save_table_text_to_s3(table_text, bucket_name, file_name):
    """
    Save extracted table text as a .txt file in the current directory and upload it to S3.

    Args:
        table_text (str): The extracted table data as text.
        bucket_name (str): The S3 bucket name.
        file_name (str): The name for the file in S3.

    Returns:
        str: URL of the uploaded file in S3, or None if upload fails.
    """
    try:
        # Define a directory to store the file (current directory)
        save_directory = os.getcwd()
        local_file_path = os.path.join(save_directory, file_name)

        # Save the table text to the file
        with open(local_file_path, "w", encoding="utf-8") as file:
            file.write(table_text)

        # Upload the file to S3
        upload_success = upload_file_to_s3(local_file_path, bucket_name, file_name)

        # Clean up the local file after upload
        os.remove(local_file_path)

        # Return the S3 URL if the upload was successful
        if upload_success:
            return f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
        else:
            return None
    except Exception as e:
        print(f"Error while saving and uploading table text: {e}")
        return None



def save_and_upload_to_s3(content, file_name, bucket_name):
    """
    Save a string to a text file and upload it to an S3 bucket.

    Args:
        content (str): The string content to save.
        file_name (str): The name of the text file (e.g., 'output.txt').
        bucket_name (str): The S3 bucket name.
        s3_client (boto3.client): The S3 client.

    Returns:
        str: The S3 file URL if successful, or None if an error occurs.
    """
        # Ensure the file name ends with .txt
    if not file_name.endswith(".txt"):
            file_name += ".txt"
    
        # Get the current working directory
    current_directory = os.getcwd()
    
        # Build the full file path
    file_path = os.path.join(current_directory, file_name)
    
        # Save the content to a local file
    with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        
    print(f"File saved locally at: {file_path}")
    
    with open(file_path, "rb") as file:
            upload_file_to_s3(file, bucket_name, file_name)

st.write("Upload a PDF file to an S3 bucket and extract text and tables from it using AWS Textract.")

# File uploader widget
uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf","png"])

if uploaded_file:
    st.write(f"Selected file: {uploaded_file.name}")
    file_type = st.selectbox("Is the uploaded file an image or a PDF?", ["Select", "Image", "PDF"])
    # Upload button
    if file_type=="PDF":
      if selected_language=="en" and st.button("Upload to S3"):
        with st.spinner("Uploading to S3..."):
            file_url = upload_file_to_s3(uploaded_file, S3_BUCKET, uploaded_file.name)
            if file_url:
                st.success("File uploaded successfully!")
                st.write("Access your file at:")
                st.write(file_url)
            table_row_column_relation=extract_tables_with_textract(uploaded_file.name)
            table_text = table_to_readable_paragraph(table_row_column_relation)
            st.write(table_text)
            
        if table_text:
            try:
                # Save and upload the table text to S3
                file_name_txt = uploaded_file.name.rsplit('.', 1)[0] + "_tables.txt"
                table_file_url = save_and_upload_to_s3(table_text, file_name_txt, S3_BUCKET)
                

                if table_file_url:
                    st.success("Extracted table data stored successfully!")
                    st.write(f"Access your table data: [Download Here]({table_file_url})")
                else:
                    st.error("Failed to store table data.")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
        else:
            st.error("No table data was extracted.")
      else:
        if st.button("Upload to S3"):
          with st.spinner("Uploading to S3..."):
            output_file_path="text_extracted.txt"
            file_url =  extract_text_from_pdf(uploaded_file,output_file_path,selected_language)
            translated_output_file_path = "translated_output.txt" 
            translate_text_with_aws(output_file_path,translated_output_file_path,"en")
            file_url= upload_file_to_s3(translate_text_with_aws, S3_BUCKET, translate_text_with_aws.name)
            if file_url:
                st.success("File uploaded successfully!")
                st.write("Access your file at:")
                st.write(file_url)
            else:
                st.warning("failed to uploade the pdf")
    else:
            file_url = upload_file_to_s3(uploaded_file, S3_BUCKET, uploaded_file.name)
            if file_url:
                st.success("File uploaded successfully!")
                st.write("Access your file at:")
                st.write(file_url)
            image_text=extract_image(uploaded_file.name)
            image_text=image_text+table_to_readable_paragraph(uploaded_file.name)
            if image_text:
                        # Save and upload the data to S3 as a .txt file
                        file_name_txt = uploaded_file.name.rsplit('.', 1)[0] + "_tables.txt"
                        table_file_url = save_and_upload_to_s3(image_text, file_name_txt, S3_BUCKET)

                        if table_file_url:
                            st.success("Extracted table data stored successfully!")
                            st.write(f"Access your table data: {table_file_url}")
            

    
    # Query Kendra (for demonstration purposes)
from langchain import PromptTemplate
        

RAG_PROMPT_TEMPLATE = '''Here is some important context which can help inform the questions the Human asks.
Make sure to not make anything up to answer the question if it is not provided in the context.
Can you provide a detailed and well-structured breakdown of [TOPIC]? Please list each major part or component of [TOPIC], followed by its key characteristics and functions, organized into clear, numbered sections. For example:

1. *Component Name*
    - Characteristics: Brief description of its structure, location, or key features.
    - Functions: Key functions or roles that this component performs.

Ensure the response is neatly formatted and easy to read.



{context}


Human: {human_input}

Assistant:
'''
PROMPT = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

import json
query_text = st.text_input("Enter query text for Kendra")
if query_text:
 search_results =retriever.get_relevant_documents(query_text)
 
 context_string = '\n\n'.join([f'Document {ind+1}: ' + i.page_content for ind, i in enumerate(search_results)])
 st.write(context_string)
 prompt_data = PROMPT.format(human_input=query_text, context=context_string)
 inputText=prompt_data
 body_part=json.dumps({'inputText': inputText,
 'textGenerationConfig': {'maxTokenCount': 8192,
  'stopSequences': [],
  'temperature': 0,
  'topP': 1}})
 response = boto3_bedrock.invoke_model(
    body=body_part,
    contentType="application/json",
    accept="application/json",
    modelId='amazon.titan-text-express-v1'
 )
 output_text=json.loads(response['body'].read())['results'][0]['outputText']
 if output_text:
  st.write(output_text)
