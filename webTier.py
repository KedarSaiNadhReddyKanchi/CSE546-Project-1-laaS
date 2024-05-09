# -------------------------------- -------------------------------- Imports ------------------------------------------------------------------------ 
from flask import Flask, request
import boto3
import os
import time
import threading
from datetime import datetime, timedelta
import base64
import random
from werkzeug.utils import secure_filename
# ----------------------------------------------------------------  Imports -------------------------------- ----------------------------------------

# ---------------------------------------------------------------- Web Application Initilization ---------------------------------------------------------------------
UPLOAD_FOLDER = 'savedImages'
application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# ---------------------------------------------------------------- Web Application Initilization ---------------------------------------------------------------------

# -------------------------------- SQS Initilization ----------------------------------------
sqs_client = boto3.client('sqs', region_name = 'us-east-1', 
                 aws_access_key_id = '####################', 
                 aws_secret_access_key='####################+'
                 )

sqs_request_queue_url = 'https://sqs.us-east-1.amazonaws.com/####################/RequestQueue'
sqs_response_queue_url = 'https://sqs.us-east-1.amazonaws.com/####################/ResponseQueue'
# -------------------------------- SQS Initilization ----------------------------------------

# -------------------------------- S3 Initilization ----------------------------------------
# Setting up Bucket name
output_bucket_name = "outputcc"
# Create S3 Client for uploading image and downloading the txt result file
s3_client = boto3.client('s3', region_name = 'us-east-1', 
                 aws_access_key_id = '####################', 
                 aws_secret_access_key='####################+'
                 )
# -------------------------------- S3 Initilization ----------------------------------------


# -------------------------------- Application Default Route ----------------------------------------
@application.route('/')
def hello_world():
        return 'Hello World'
# -------------------------------- Application Default Route ----------------------------------------

# The functionality of this function is to read the corresponding image output file from the output bucket.
def get_corresponding_image_output_file_from_output_s3(file_name):
    print("Fetching result file : " , file_name , " from output S3 bucket")
    return s3_client.get_object(Bucket = output_bucket_name, Key = file_name)["Body"]


# Using a dictionary to maintain all the responses and the corresponding results.
# This is being implemented locally so that the thread can end as soon as it see that the corresponding request has been processed.
RESULTS = dict()
def check_if_response_is_available_or_not(image_file_name):
    try:
        while image_file_name not in RESULTS.keys():
            continue
        #print("exited the while loop in the check_if_response_is_available_or_not function")
        image_classified_name_by_the_model = RESULTS[image_file_name]
        RESULTS.pop(image_file_name)
        #print("trying to return the image_classified_name_by_the_model from the check_if_response_is_available_or_not function")
        return image_classified_name_by_the_model
    except Exception as e:
        print("Error while executing the check_if_response_is_available_or_not function : " , e)

# As the code is using the Results dictionary
# we are using this function to load the response data from the model
# into the results dictionary 
def load_response_into_results_dictionary(image_file_name, image_classified_name_by_the_model):
    RESULTS[image_file_name] = image_classified_name_by_the_model
    print('updated local data store - Results Dictionary')
    print(RESULTS)

# function to delete message for SQS after it has been processed
def delete_from_the_sqs_response_queue(sqs_response_message_receipt_handle):
    #print("in my delete_from_the_sqs_response_queue function to delete the message from the response queue")
    sqs_client.delete_message(QueueUrl = sqs_response_queue_url, ReceiptHandle=sqs_response_message_receipt_handle)
# function to delete message for SQS after it has been processed

def push_request_from_workload_into_the_sqs_request_queue(image_filename):
    with open("savedImages/"+image_filename, "rb") as image_data_as_string:
        bytes = base64.b64encode(image_data_as_string.read())
    response = sqs_client.send_message(QueueUrl=sqs_request_queue_url,
                        MessageAttributes={
        'ImageName': {
            'DataType': 'String',
            'StringValue': image_filename
        }},MessageBody=bytes.decode('ascii'))
    print ("Message for " , image_filename , " uploded to the request queue  : ", response['MessageId'])

# Continuously polling the Response Queue, the program saves incoming messages to a RESULT dictionary, enabling a waiting thread to read and respond to the user based on the stored data.
def get_messages_from_response_queue():
    while True:
        try:
            print("checking for Messages in the SQS response queue")
            message_from_the_sqs_response_queue = sqs_client.receive_message(QueueUrl=sqs_response_queue_url, AttributeNames=['All'], MessageAttributeNames=['All'], MaxNumberOfMessages=10, WaitTimeSeconds = 20)
            if 'Messages'in message_from_the_sqs_response_queue:
                for message in message_from_the_sqs_response_queue['Messages']:
                    body = message['Body']
                    resp_filename, result = body.split(',')
                    load_response_into_results_dictionary(resp_filename, result)
                    print("File Name: ", resp_filename)
                    print("Classification Result: ", result)
                    delete_from_the_sqs_response_queue(message["ReceiptHandle"])
            #time.sleep(5)
        except Exception as e:
            print("Error while consuming message from Response Queue : " , e)


# -------------------------------- MAIN ----------------------------------------
@application.route("/upload", methods=["POST"])
def upload():
    if request.method == 'POST':
        try:
            image = request.files['myfile']
            filename = secure_filename(image.filename)
            path = os.path.join(application.config['UPLOAD_FOLDER'], filename)
            image.save(path)
            push_request_from_workload_into_the_sqs_request_queue(image.filename)
            print(image.filename)
            check_if_response_is_available_or_not(image.filename)
            print("Response Ready")
            file_name_in_the_output_s3_bucket = str(image.filename).strip() + "-output.txt"
            return get_corresponding_image_output_file_from_output_s3(file_name_in_the_output_s3_bucket)
        except Exception as e:
            print("Error while Processing user request : " , e)
    else:
        #print("Request hit from the workload generator file is not coming as POSt but as some other value as you can see below")
        print(request.method)

sqs_response_queue_monitoring_thread = threading.Thread(target = get_messages_from_response_queue)
sqs_response_queue_monitoring_thread.start()
# -------------------------------- MAIN ----------------------------------------

# run the app.
if __name__ == "__main__":
    application.run(host='0.0.0.0', port='8081', threaded=True)