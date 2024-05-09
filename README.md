# Group Project1 : IAAS

## CSE 546: Cloud Computing Project

Group members:

- Atul Prakash - 
- Abhi Teja Veresi- 
- Kedar Sai Nadh Reddy Kanchi - 

<hr>

Web-tier's URL: http://127.0.0.1:8081/upload

EIP: [54.236.154.135](https://us-east-1.console.aws.amazon.com/vpcconsole/home?region=us-east-1#ElasticIpDetails:AllocationId=eipalloc-)

SQS queue names: `RequestQueue` and `ResponseQueue`

S3 bucket names: `ccinput` and `outputcc`

Credentials:

aws_access_key_id = ``
aws_secret_access_key = `+`

Config: `region=us-east-1`

Keypair name: `SkylineSurfers`

PEM key -

-----BEGIN RSA PRIVATE KEY-----
==
-----END RSA PRIVATE KEY-----

<hr>

## Member Tasks

### Atul Prakash - **()**

* **Setting up Infrastructure:** I have created the infrastructure requirements for the project, which includes setting up all the buckets (input bucket, output bucket and a demo bucket which contains the app.py file which executes in all the running instances when the request is generated, the credentials, config files, controller.py, webTier.py, myscript.sh which contains all the scripts to run before executing the app.py file in the aws console in the instances and the imagenet-labels.json which has the tags possible for the image classification). Creating the queues(Request and Response Queues), the policies required for the IAM instance profile to run the program (all access policy), snapshot of the image provided to us, setting up security groups and also the key pairs. Also created two instances namely webTier and controller which had webTier.py and controller.py respectively.
* **Controller optimization:** Also helping in some logic of controller.py for creating instances automatically for processing the requests (Autoscaling), monitoring the buckets, queues and testing some cases of the application while sending single and concurrent/multiple requests from workloadgen.py and optimization of the application code accordingly to achieve autoscaling in our project.

### Abhi Teja Veresi – (ASU ID: )

- **Web tier Implementation:** I have implemented the webtier part of the application. Created webTier.py in a flask framework which would be running in webTier EC2 instance. It is  a multithreaded environment which gets multiple concurrent requests from the workload generator (workloadgen.py). Created API endpoints to get the images from the post request. Stored the images in a folder and pushed it to the SQS request Queue. Used base64 encoding to push the image to the queue. Designed the logic to run a different thread to get the responses from the response queue by pooling 10 messages at a time and delete the messages after storing the responses in a temporary dictionary. Implemented the logic to get the results from the bucket and return the response to the workload generator. Tested the functionality of web tier by sending multiple concurrent messages in different ranges.
- **Report and Readme creation:** Helped in writing the report using the provided template and also created the README file in the git repository which details the installation requirements and the steps to run the application.

### Kedar Sai Nath Reddy Kanchi-  (ASU ID: )

- **Controller and App file implementation:**  I havedesigned the logic to the auto scaling algorithm in the controller.py file based on the demand (depth) of the request queue. Scale out function is implemented when the current instances running are less than maximum count and total messages in the queue greater than current instances. Implemented logic for each user data to run in Ubuntu by app.py file for each instance.
- Implemented logic for app tier by getting the requests from request queue and storing the images in input buckets. After processing the retrieved images using the deep learning model pushed in the response queue and results in output buckets.
- Tested the auto scaling algorithms for different requests concurrently by monitoring the queues and buckets.

<hr>

### Demo video of the project

- [https://drive.google.com/file/d/1GAwEKJp3JS_c5q2EISlsPBtlKDdxtSQF/view?usp=sharing](https://drive.google.com/file/d/1GAwEKJp3JS_c5q2EISlsPBtlKDdxtSQF/view?usp=sharing)
