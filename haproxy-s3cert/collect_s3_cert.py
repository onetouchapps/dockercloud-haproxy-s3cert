import json
import os
import re
import sys
import urllib2

import boto3

CERT_BUCKET_IAM_ROLE = os.environ['CERT_BUCKET_IAM_ROLE']
CERT_BUCKET_NAME = os.environ['CERT_BUCKET_NAME']
CERT_OBJECT_NAME = os.environ['CERT_OBJECT_NAME']

S3_BUCKET_CREDS = ('http://169.254.169.254/latest/meta-data/iam/'
                   'security-credentials/' + CERT_BUCKET_IAM_ROLE)
response = urllib2.urlopen(S3_BUCKET_CREDS).read()
security_creds = json.loads(response.decode('utf-8'))
s3 = boto3.resource('s3',
                    aws_access_key_id=security_creds['AccessKeyId'],
                    aws_secret_access_key=security_creds['SecretAccessKey'],
                    aws_session_token=security_creds['Token'])
cert_object = s3.Object(CERT_BUCKET_NAME, CERT_OBJECT_NAME)
cert = cert_object.get()['Body'].read()
cert_escaped = re.sub(r'\n', r'\\n', cert)
sys.stdout.write(cert_escaped)
