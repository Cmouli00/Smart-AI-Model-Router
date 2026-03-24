

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer('all-MiniLM-L6-v2')
q_client = QdrantClient(
    url=os.getenv("QDRANT_URL"), 
    api_key=os.getenv("QDRANT_API_KEY"),
)

# print(q_client.get_collections())

# Initialize collection
COLLECTION_NAME = "llm_cache"
try:
    q_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
except:
    pass # Collection already exists

def check_cache(prompt: str):
    try:
        vector = encoder.encode(prompt).tolist()
    
        search_result = q_client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=1
        ).points 
        
        if search_result and search_result[0].score > 0.92:
            return search_result[0].payload.get("answer")
    except Exception as e:
        print(f"Cache Search Error: {e}")
    return None

def update_cache(prompt: str, answer: str):
    vector = encoder.encode(prompt).tolist()
    q_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=hash(prompt) % 10**8, vector=vector, payload={"answer": answer})]
    )