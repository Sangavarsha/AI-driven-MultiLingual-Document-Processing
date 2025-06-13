import boto3

# AWS Translate Configuration
AWS_ACCESS_KEY = '##'  # Replace with your AWS access key
AWS_SECRET_KEY = '##'  # Replace with your AWS secret key
S3_REGION = 'us-east-1'  # Replace with your AWS region

# Initialize AWS Translate Client
translate_client = boto3.client(
    'translate',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=S3_REGION  # Ensure region is set here
)

# Function to translate text with AWS Translate
def translate_text_with_aws(text, target_language):
    try:
        # Perform translation
        translation = translate_client.translate_text(
            Text=text,
            SourceLanguageCode='auto',  # Automatically detect the source language
            TargetLanguageCode=target_language
        )
        return translation['TranslatedText']
    except Exception as e:
        print(f"Error occurred while translating text: {e}")
        return None

# Function to read text from a file
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Function to write translated text to a file
def write_translated_text_to_file(file_path, translated_text):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(translated_text)

# Main function to handle file input, translation, and output
def translate_file(input_file, output_file, target_language):
    # Read the content of the input file
    input_text = read_text_from_file(input_file)

    # Translate the text
    translated_text = translate_text_with_aws(input_text, target_language)
    
    if translated_text:
        # Write the translated text to the output file
        write_translated_text_to_file(output_file, translated_text)
        print(f"Translation successful. Translated text saved to {output_file}")
    else:
        print("Translation failed.")

# Example usage:
if __name__ == "__main__":
    input_file_path = r"C:\Users\HP\Documents\idpproject\extracted_text.txt"  # Path to your input text file
    output_file_path = "translated_output.txt"  # Path to save the translated output
    target_language = 'es'  # Target language code (e.g., 'es' for Spanish)
    
    translate_file(input_file_path, output_file_path, target_language)