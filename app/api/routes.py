from flask import Blueprint, request, jsonify
from app.service.aws_service import AwsService
from app.service.embedding_service import EmbedService
from app.service.openai_service import OpenaiService
import os

api_blueprint = Blueprint('api', __name__)
aws_service = AwsService()
embed_service = EmbedService()
openai_service = OpenaiService()
UPLOAD_FOLDER = 'docs'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@api_blueprint.route("/")
def homepage():
    return "RAG based chatbot"

@api_blueprint.route("/uploadFile", methods=['POST', 'GET'])
def uploadFile(): 
    if 'file' not in request.files:
        print("File not found")
        return 'No file found', 400
    if 'question' not in request.form:
        print("Question not found")
        return 'No file found', 400
    file = request.files.get('file')
    #Write file to S3 bucket
    destBucket = "geenuity-custom-mantra-user-rag-files"
    fileid = aws_service.uploadFile(file, destBucket)
    #Save file to local folder to read and process
    if file:
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        filename = filename.lower()
        file.save(filename)
    
    question = request.form.get('question')

    #TODO: Add a userid/auth mechanism to distinguish useruserid = '1234D'
    docs = embed_service.get_document_text(file, filename)
   
    ensemble_retriever = embed_service.ensemble_retriever_from_docs(docs, openai_service.fetchEmbeddings(model="text-embedding-ada-002"))
     
    #TODO: Add a RedisChatHistory memory chain
    chain = embed_service.create_full_chain(retriever=ensemble_retriever)
    
    return jsonify(chain.invoke(question))

