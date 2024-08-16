from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_pinecone import PineconeVectorStore
from langchain import hub

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate

class EmbedService():
    pinecone_client: None
    def __init__(self) -> None:
        load_dotenv()
        self.pinecone_client = Pinecone(api_key = os.environ.get("PINECONE_API_KEY"))

    @staticmethod
    def get_document_text(uploaded_file, fname, title=None):
        docs = []
        fname = uploaded_file.filename
        if not title:
            title = os.path.basename(fname)
        # pdf_content = io.BytesIO()
        pdf_reader = PdfReader(uploaded_file)
        for num, page in enumerate(pdf_reader.pages):
            page = page.extract_text()
            doc = Document(page_content=page, metadata={'title': title, 'page': (num + 1)})
            docs.append(doc)

        return docs
    
    @staticmethod
    def split_documents(docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False)

        contents = docs
        if docs and isinstance(docs[0], Document):
            contents = [doc.page_content for doc in docs]

        texts = text_splitter.create_documents(contents)
        n_chunks = len(texts)
        #print(f"Split into {n_chunks} chunks")
        return texts

    def upload_to_db(self, texts, embeddings):
        embeddings = OpenAIEmbeddings()
        index_name = "geenuity-user-data"
        pinecone = self.pinecone_client
        #need to have an existing pinecone index before using PineconeVectorStore
        if index_name not in pinecone.list_indexes().names():
            pinecone.create_index(index_name, dimension=1536,
                                  spec = ServerlessSpec(
                                         cloud="aws",
                                         region="us-east-1"))

        docsearch = PineconeVectorStore.from_documents(
            documents=texts,
            index_name=index_name,
            embedding=embeddings, 
        )
    
        index = pinecone.Index(index_name)
        for ids in index.list():
            query = index.query(
                id=ids[0],
                top_k=1,
                include_values=True,
                include_metadata=True
            )
        return docsearch

    def ensemble_retriever_from_docs(self, docs, embeddings=None):
        texts = self.split_documents(docs)
        vs = self.upload_to_db(texts, embeddings)
        vs_retriever = vs.as_retriever()

        bm25_retriever = BM25Retriever.from_texts([t.page_content for t in texts])

        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, vs_retriever],
            weights=[0.5, 0.5])

        return ensemble_retriever

    @staticmethod
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    def make_rag_chain(self, model, retriever, rag_prompt = None):
        if not rag_prompt:
            rag_prompt = hub.pull("rlm/rag-prompt")

        rag_chain = (
            {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | model
            | StrOutputParser()
        )
        return rag_chain

    def create_full_chain(self, retriever, openai_api_key=None):
        model = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
        system_prompt = """You are a helpful AI assistant for busy professionals trying to improve their knowledge of the stock market by reading research papers.
        Use the following context to help the user:
        If you don't know the answer, just say that you don't know. 
        
        Context: {context}
        
        Question: """

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{question}"),
            ]
        )

        rag_chain = self.make_rag_chain(model, retriever, rag_prompt=prompt)
        #chain = self.create_memory_chain(model, rag_chain, chat_memory) # to store conversational history
        return rag_chain