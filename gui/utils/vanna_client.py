import os
from dotenv import load_dotenv
from vanna.openai import OpenAI_Chat
from openai import AzureOpenAI
from vanna.qdrant import Qdrant_VectorStore
from qdrant_client import QdrantClient
from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider

load_dotenv('.env', override=True)

qdrant_client = QdrantClient(
    url="http://localhost:6333", 
    api_key=os.getenv('QDRANT__SERVICE__API_KEY')
)

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), 
    "https://cognitiveservices.azure.com/.default"
)

openai_client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider
)

class MyVanna(Qdrant_VectorStore, OpenAI_Chat):
    def __init__(
            self, 
            qdrant_client: QdrantClient, 
            openai_client: AzureOpenAI,
            openai_model: str
        ):
        Qdrant_VectorStore.__init__(
            self, 
            config={'client': qdrant_client}
        )
        OpenAI_Chat.__init__(
            self, 
            client=openai_client, 
            config={"model": openai_model}
        ) 

vn = MyVanna(
    qdrant_client=qdrant_client,
    openai_client=openai_client,
    openai_model=os.getenv("AZURE_OPENAI_MODEL_DEPLOYMENT")
)

vn.connect_to_postgres(
    host=os.getenv('POSTGRES_HOST'), 
    dbname=os.getenv('POSTGRES_DB'), 
    user=os.getenv('POSTGRES_USER'), 
    password=os.getenv('POSTGRES_PASSWORD'), 
    port=os.getenv('POSTGRES_PORT')
)
