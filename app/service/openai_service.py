from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import os
from typing import List

class OpenaiService:
    openai_key: str
    def __init__(self):
        #initialize credentials
        load_dotenv()
        self.openai_key = os.environ.get('OPENAI_API_KEY')

    def fetchEmbeddings(self, model):
        return OpenAIEmbeddings(openai_api_key=self.openai_key, model=model)
        # return embeddings.embed_documents(texts)

    """
    Access the model to generate prompt+query results
    """
    
