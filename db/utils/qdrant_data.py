import os
import json
import uuid
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, 
    VectorParams, 
    Distance
)

load_dotenv('.env.dev', override=True)

QDRANT_API_KEY=os.getenv('QDRANT__SERVICE__API_KEY')

# --- 1. JSON data ---
# Open and read the JSON file
with open('db/schema/sales_db.json', 'r') as file:
    json_data = json.load(file)

# print(json_data)

# --- 2. OpenAI Embedding ---

 
ollama_client = OpenAI(
    base_url='http://localhost:11434/v1/',
    api_key='ollama' # required, but unused
)

EMBED_MODEL = "nomic-embed-text:latest" 

def get_embedding(text):
    response = ollama_client.embeddings.create(
        input=text,
        model=EMBED_MODEL
    )
    return response.data[0].embedding

# --- 3. Qdrant Setup ---
qdrant = QdrantClient(
    "http://localhost:6333",
    api_key=QDRANT_API_KEY,
)
COLLECTION_NAME = "sales_db"

vector_len = len(get_embedding("Creating a dummy embedding to get Embedding Model's vector length"))

print('vector_len:', vector_len)

# Create collection if it doesn't exist
if COLLECTION_NAME not in [c.name for c in qdrant.get_collections().collections]:
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_len, distance=Distance.COSINE) 
    )

# --- 4. Insert embeddings ---
points = []
for idx, obj in enumerate(json_data):
    text_to_embed = json.dumps(obj)
    embedding = get_embedding(text_to_embed)
    points.append(
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            # Store the original object as metadata
            payload=obj  
        )
    )

qdrant.upsert(
    collection_name=COLLECTION_NAME,
    points=points
)

print(f"Inserted {len(points)} objects with embeddings into Qdrant collection '{COLLECTION_NAME}'.")
