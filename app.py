import torch
import torchvision
import torchvision.transforms as transforms
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from urllib.request import urlopen
from PIL import Image
import numpy as np
import json
import sys
import time
import boto3
import base64
import os
import csv
import logging

model = models.resnet18(pretrained=True)
model.eval()

sqs = boto3.client('sqs', region_name = 'us-east-1', 
                 aws_access_key_id = '', 
                 aws_secret_access_key=''
                 )
s3 = boto3.client('s3', region_name = 'us-east-1', 
                 aws_access_key_id = '', 
                 aws_secret_access_key=''
                 )
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/############/RequestQueue'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/############/ResponseQueue'
input_bucket_name = 'ccinput'
output_bucket_name = 'outputcc'

def upload_file(file_name, bucket):
    print("1st line in the upload file command")
    
    object_name = os.path.basename(file_name)
    print("object name formed from the given parameters")

    s3.upload_file(file_name, bucket, object_name)
    print("successfully uploaded the file to the bucket. ")

    return True

# count = 0
# while count < 2:
#    this means the while loop will run only run twice and process only two requests, thus maintaining the ratio of 2:1 with the requests and instances

while True:
    try:
        print("i am printing my 1st line in the app.py file")

        msg = sqs.receive_message(QueueUrl=request_queue_url,AttributeNames=['All'], MessageAttributeNames =['All'])
        print("msg received")

        bytes = str.encode(msg['Messages'][0]['Body'])
        print("encoded bytes retrived")

        img_name = msg['Messages'][0]['MessageAttributes']['ImageName']['StringValue']  #need to update as per changes in web tier
        print("image name is img_name : " , img_name)

        img_add = f'/home/ubuntu/{img_name}'
        print("image add path is img_add : ")

        file = open(img_add, 'wb')
        print("file is opened successfully")

        img_bytes = base64.b64decode((bytes))
        print("encoded img_bytes retrived")

        file.write(img_bytes)
        print("file has been updated with the retrived img_bytes ")

        file.close()
        print("closed the file successfully")

        img = Image.open(img_add)
        print("image opened successfully")

        img_tensor = transforms.ToTensor()(img).unsqueeze_(0)
        print("img_tensor : data retrieved from the transfrom package ")

        outputs = model(img_tensor)
        print("set of outputs generated from the img_tensor")

        _, predicted = torch.max(outputs.data, 1)
        print("retrieved the predicted set from the outputs data using the torch library")

        with open('/home/ubuntu/classifier/imagenet-labels.json') as f:
            labels = json.load(f)
        print("successfully opened the imagenet-labels.json file and loaded it into the labels variable")

        result = labels[np.array(predicted)[0]]
        print("retrieved the object name from the labels json as per the predicted data from the deep learning model")

        save_name = f"{img_name},{result}"
        print("save name variable created")
        #print(f"-----------------------------------> {save_name}")
        
        with open(img_add+'-output.txt', 'w') as f:
            f.write(save_name)
        print("saved the save_name in to the output text file in the image add path")
        
        msg_response = None
        print('created an empty msg response variable')

        #msg_response  = sqs.send_message(QueueUrl=response_queue_url, MessageBody=save_name)
        msg_response  = sqs.send_message(QueueUrl=response_queue_url, MessageAttributes={'ImageName': {
            'DataType': 'String',
            'StringValue': img_name
        }}, MessageBody=save_name)
        print("successfully sent the message to the response queue")

        upload_file(img_add, input_bucket_name)
        print("successfully added the file into the input s3 bucket")

        upload_file(img_add+'-output.txt', output_bucket_name)
        print("successfully added the file into the output s3 bucket")
        
        del_responce = None

        del_responce = sqs.delete_message(QueueUrl=request_queue_url , ReceiptHandle=msg['Messages'][0]['ReceiptHandle'])
        print("successfully deleted the message from the request queue")

        # print(f"{save_name}")
        print('Sleep for 3 sec...')
        #time.sleep(3)
    except:
        print('Sleep for 5 sec...')
        time.sleep(5)

