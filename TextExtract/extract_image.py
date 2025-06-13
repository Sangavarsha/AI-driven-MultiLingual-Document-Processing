import time
import boto3
from langchain_core.prompts import PromptTemplate
import json

S3_BUCKET = 'idpproject'       # Replace with your bucket name
S3_REGION = 'us-east-1'        # e.g., 'us-east-1'
AWS_ACCESS_KEY = '##'   # Replace with your AWS access key
 # Replace with your AWS access key
AWS_SECRET_KEY = '#'
# Initialize AWS Clients
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)
textract_client = boto3.client(
    'textract',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION
)
def extract_from_image(file_key):
    # Start the text detection job
    response = textract_client.start_document_text_detection(
        DocumentLocation={"S3Object": {"Bucket": S3_BUCKET, "Name": file_key}}
    )
    
    job_id = response['JobId']
    status = None
    
    # Wait for the job to complete
    while status != 'SUCCEEDED':
        job_status = textract_client.get_document_text_detection(JobId=job_id)
        status = job_status['JobStatus']
        if status == 'FAILED':
            raise Exception("Textract job failed")
    
    # Collect results from all pages
    text = ""
    next_token = None
    while True:
        # Fetch results for the current page
        response = textract_client.get_document_text_detection(JobId=job_id, NextToken=next_token) if next_token else textract_client.get_document_text_detection(JobId=job_id)
        
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                text += item["Text"] + "\n"
        
        # Check if there are more pages
        next_token = response.get("NextToken", None)
        if not next_token:
            break
    output_file_name='demo_rag_on_image.txt'
     

    with open(output_file_name,'w') as output_file_io:
     for x in response["Blocks"]:
        if x["BlockType"] == "LINE":
            output_file_io.write(x["Text"]+'\n')
    return text

def main():
    # File to upload
    file_name = "English Story book.pdf"  # Replace with your image file path
   
    # Extract text from the image
    extracted_text = extract_from_image(file_name.name)
    print("Extracted text:")
    print(extracted_text)

if __name__ == "__main__":
    main()
