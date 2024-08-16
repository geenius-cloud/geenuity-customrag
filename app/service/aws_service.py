#use this to store and delete files from aws
import boto3
from dotenv import load_dotenv
import os
import uuid

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
    def uploadFile(self, file, destBucket, local_path): 
        
        self.client.upload_fileobj(file, destBucket, local_path)
        #TODO: generate random file id, save file by fileid on S3
        fileid= uuid.uuid1()
        return fileid
