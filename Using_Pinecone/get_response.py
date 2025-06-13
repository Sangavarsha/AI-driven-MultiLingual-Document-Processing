import os
import json
import boto3
from pinecone import Pinecone, ServerlessSpec, Index
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict

# Initialize Pinecone
# Initialize Pinecone using the new method
pc = Pinecone(api_key="##")  # Replace with your Pinecone API key
boto3_bedrock = boto3.client('bedrock-runtime', region_name='us-east-1', aws_access_key_id='##', aws_secret_access_key='##')

index_name = "model"

# Load Sentence Transformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Ensure the Pinecone index exists
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,  # Match the embedding dimension of the model
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )

# Get the Pinecone index
index = pc.Index(index_name)

def chunk_text(text: str, chunk_size: int = 200) -> List[str]:
    """Splits text into chunks of approximately `chunk_size` words."""
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def get_embeddings(text: str) -> np.ndarray:
    """Generates an embedding using Sentence-Transformers."""
    return embedding_model.encode(text)

def store_in_pinecone(chunks: List[str], embeddings: List[np.ndarray], doc_id: str):
    """Stores text chunks and embeddings in Pinecone."""
    pinecone_vectors = [
        {
            "id": f"{doc_id}_{i}",
            "values": embedding.tolist(),
            "metadata": {"text": chunk, "doc_id": doc_id}
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    index.upsert(vectors=pinecone_vectors)

def retrieve_similar_text(query: str, top_k: int = 5) -> List[Dict]:
    """Retrieves similar text chunks from Pinecone."""
    query_embedding = get_embeddings(query)
    search_results = index.query(
        vector=query_embedding.tolist(),
        top_k=top_k,
        include_metadata=True
    )
    return [
        {"text": match["metadata"]["text"], "score": match["score"]}
        for match in search_results["matches"]
    ]

def generate_response_with_bedrock(context: str, query: str, aws_access_key: str, aws_secret_key: str) -> str:
    """Generates a response using Amazon Bedrock."""
    bedrock_client = boto3.client('bedrock-runtime', 
                                  region_name='us-east-1', 
                                  aws_access_key_id=aws_access_key,  
                                  aws_secret_access_key=aws_secret_key)

    prompt = f"""
    Context:
    {context}

    Question:
    {query}

    Answer:
    """
    body_part = json.dumps({
        'inputText': prompt,
        'textGenerationConfig': {
            'maxTokenCount': 8192,
            'temperature': 0,
            'topP': 1
        }
    })

    try:
        response = bedrock_client.invoke_model(
            body=body_part,
            contentType="application/json",
            accept="application/json",
            modelId='amazon.titan-text-express-v1'
        )
        response_body = json.loads(response['body'].read().decode('utf-8'))
        return response_body['results'][0]['outputText']
    except Exception as e:
        return f"Error invoking model: {e}"

def process_file_and_get_response(file_path: str, aws_access_key: str, aws_secret_key: str) -> str:
    """Processes a file, stores data in Pinecone, retrieves relevant context, and generates a response."""
    doc_id = os.path.basename(file_path).split('.')[0]  # Use filename as doc_id

    # Read file
    with open(file_path, "r", encoding="utf-8") as file:
        input_text = file.read()

    # Chunk text
    chunks = chunk_text(input_text, chunk_size=200)
    
    # Generate embeddings
    embeddings = [get_embeddings(chunk) for chunk in chunks]

    # Store in Pinecone
    store_in_pinecone(chunks, embeddings, doc_id)

   

# Example Usage
if __name__ == "__main__":
    aws_access_key = "##"# Replace with your AWS Access Key
    aws_secret_key = "##"
    response = process_file_and_get_response("leps208.txt", "explain chapter 8", aws_access_key, aws_secret_key)
    print("\nGenerated Response:\n", response)
