#use this to store and delete files from aws
import boto3
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import uuid
#get fileid creator method

class AwsService:
    client = None
    def __init__(self):
        load_dotenv()
        session = boto3.session.Session(os.environ.get('AWS_ACCESS_KEYID'),
                           aws_secret_access_key = os.environ.get('AWS_ACCESS_KEYTOKEN'))
        self.client = session.client("s3")
 
    """
    Take file as input, upload to s3 with specific bucket, and fileid
    return 
    """
    def uploadFile(self, file, destBucket): 
        #generate random file id
        self.client.upload_fileobj(file, destBucket, file.filename)
        #Save file by file id generated
        #or save fileid, where to store
        fileid= uuid.uuid1()
        return fileid
    
    #fetch a file from s3 bucket
