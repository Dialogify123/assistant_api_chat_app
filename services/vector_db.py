from constants import OPENAI_API_KEY,CLUSTER_ENDPOINT,COLLECTION_NAME,VECTOR_DB_TOKEN
from pymilvus import MilvusClient
from openai import OpenAI
import openai

openai.api_key = OPENAI_API_KEY

def getTemplate(tags:list[str]=[]) -> str:
    filename = db.searchFile(tags)
    with open(f"template\\{filename}","r") as f:
        return f.read()

class VectorDB:

    def __init__(self) -> None:
        self.CLUSTER_ENDPOINT= CLUSTER_ENDPOINT
        self.TOKEN= VECTOR_DB_TOKEN 
        self.COLLECTION_NAME=COLLECTION_NAME
        self.openai_client = OpenAI()
        self.client = None
    
    def connect(self):
        self.client = MilvusClient(
            uri=self.CLUSTER_ENDPOINT, 
            token=self.TOKEN 
        )
        return self.connect

    def insertTags(self, tags:list[str], filename:str):
        if not self.client: return 
        return self.client.insert(
            collection_name=self.COLLECTION_NAME,
            data={
                "Vectorfield": self.createEmbedding(tags),
                "fileName": filename,
                "Tags": tags
            }
        )
    
    def searchFile(self, tags: list[str]):
        res = self.client.search(
            collection_name=self.COLLECTION_NAME,
            data=[self.createEmbedding(tags)],
            output_fields=["fileName"],
            limit=1
        )
        return  res[0][0]['entity']['fileName']


    def createEmbedding(self, text: list[str]):
        text.sort()
        text = " ".join(text)
        response = self.openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding



db = VectorDB()
db.connect()