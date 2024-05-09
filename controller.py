# -------------------------------- Imports ----------------------------------------
import boto3
import time
# -------------------------------- Imports ----------------------------------------

# -------------------------------- SQS Initilization ----------------------------------------
sqs = boto3.client('sqs', region_name = 'us-east-1', 
                 aws_access_key_id = '', 
                 aws_secret_access_key=''
                 )
sqs_request_queue_url = 'https://sqs.us-east-1.amazonaws.com/############/RequestQueue'
# -------------------------------- SQS Initilization ----------------------------------------

# -------------------------------- EC2 Initilization ----------------------------------------
ec2 = boto3.client('ec2', region_name = 'us-east-1', 
                 aws_access_key_id = '', 
                 aws_secret_access_key=''
                 )
# -------------------------------- EC2 Initilization ----------------------------------------

# -------------------------------- AWS Account Details ----------------------------------------
ami_id = 'ami-#################' #Atul's acc
#ami_id = 'ami-062a60c2723fb1151' #kedar's acc
instance_type = 't2.micro'
key_name = '####'
security_group_id = 'sg-################'
iam_instance_profile = 'arn:aws:iam::############:instance-profile/########'
# -------------------------------- AWS Account Details ----------------------------------------


# -------------------------------- Setup of the User Data commands ----------------------------------------
# using ec2-user user and command 'yum' instead of 'apt' when booting up ec2 instances 
# using the current free tier operating systems which have the EC2-connect preinstalled
# userdata = '#cloud-boothook \n#!/bin/bash \nsudo yum update \nsudo yum install -y python3 \nsudo yum install -y python3-flask \nsudo yum install -y python3-pip python3 python3-setuptools \npip3 install boto3 \nsudo yum install -y tmux \nsudo yum install -y awscli \nmkdir /home/ec2-user/.aws \ncd /home/ec2-user/.aws \naws configure set aws_access_key_id #################### \naws configure set aws_secret_access_key ####################+ \naws configure set default.region us-east-1 \naws s3 cp s3://cc-proj-demo/credentials /home/ec2-user/.aws/ \naws s3 cp s3://cc-proj-demo/config /home/ec2-user/.aws \ncd .. \nsudo aws configure set aws_access_key_id #################### \nsudo aws configure set aws_secret_access_key ####################+ \nsudo aws configure set default.region us-east-1 \nsudo aws s3 cp s3://cc-proj-demo/app.py /home/ec2-user/ \nsudo aws s3 cp s3://cc-proj-demo/myscript.sh /home/ec2-user/ \nmkdir /home/ec2-user/classifier \ncd /home/ec2-user/classifier \nsudo aws configure set aws_access_key_id #################### \nsudo aws configure set aws_secret_access_key ####################+ \nsudo aws configure set default.region us-east-1 \nsudo aws s3 cp s3://cc-proj-demo/imagenet-labels.json /home/ec2-user/classifier \ncd .. \nsudo chmod +777 /home/ec2-user/app.py \nsudo chmod +x /home/ec2-user/app.py \ntouch /home/ec2-user/log.txt \nsudo chmod -R 777 /home/ec2-user \nsudo chmod +x myscript.sh \n pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html \n/usr/bin/python3 /home/ec2-user/app.py \n'

# using ubuntu user - when scaling up the ec2-instances using the professor's AMI-ID
userdata = '#cloud-boothook \n#!/bin/bash \nsudo apt update \nsudo apt install -y python3 \nsudo apt install -y python3-flask \nsudo apt install -y python3-pip python3 python3-setuptools \npip3 install boto3 \nsudo apt install -y tmux \nsudo apt install -y awscli \nmkdir /home/ubuntu/.aws \ncd /home/ubuntu/.aws \naws configure set aws_access_key_id ################ \naws configure set aws_secret_access_key ####################+ \naws configure set default.region us-east-1 \naws s3 cp s3://cc-proj-demo/credentials /home/ubuntu/.aws/ \naws s3 cp s3://cc-proj-demo/config /home/ubuntu/.aws \ncd .. \nsudo aws configure set aws_access_key_id #################### \nsudo aws configure set aws_secret_access_key ####################+ \nsudo aws configure set default.region us-east-1 \nsudo aws s3 cp s3://cc-proj-demo/app.py /home/ubuntu/ \nsudo aws s3 cp s3://cc-proj-demo/myscript.sh /home/ubuntu/ \nmkdir /home/ubuntu/classifier \ncd /home/ubuntu/classifier \nsudo aws configure set aws_access_key_id #################### \nsudo aws configure set aws_secret_access_key ####################+ \nsudo aws configure set default.region us-east-1 \nsudo aws s3 cp s3://cc-proj-demo/imagenet-labels.json /home/ubuntu/classifier \ncd .. \nsudo chmod +777 /home/ubuntu/app.py \nsudo chmod +x /home/ubuntu/app.py \ntouch /home/ubuntu/log.txt \nsudo chmod -R 777 /home/ubuntu \nsudo chmod +x myscript.sh \n pip3 install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1 -f https://download.pytorch.org/whl/torch_stable.html \nsudo -u ubuntu python3 /home/ubuntu/app.py \n'
# -------------------------------- Setup of the User Data commands ----------------------------------------


# -------------------------------- Initialising the Global Variables ----------------------------------------
ec2_instance_list = []
minimum_count = int(0)
maximum_count = int(20)
current_count = 0
additional_check_count_for_scale_out = 0
# -------------------------------- Initialising the Global Variables ----------------------------------------

# -------------------------------- Initial Verification of the EC2-Instances ----------------------------------------
instances = ec2.describe_instances( Filters = [{ 'Name': 'instance-state-code', 'Values': [ '0', '16' ] }, { 'Name': 'image-id', 'Values': [ami_id] }] )
print(instances)
#current_count = int(len(instances['Reservations']))
print('Current Number of EC2 Instances running at current time: ' , current_count)
print('Instance List: \n', ec2_instance_list)
# -------------------------------- Initial Verification of the EC2-Instances ----------------------------------------

# -------------------------------- Function to retrieve the total number of messages that are awaiting in the SQS Request Queue ----------------------------------------
def retrieve_the_total_number_of_messages_present_in_the_SQS_Request_Queue():
    sqs_request_queue_attributes = sqs.get_queue_attributes(QueueUrl = sqs_request_queue_url, AttributeNames = ['All'])
    total_number_of_visible_messges_in_the_sqs_request_queue = int(sqs_request_queue_attributes['Attributes']['ApproximateNumberOfMessages'])
    total_number_of_INvisible_messges_in_the_sqs_request_queue = int(sqs_request_queue_attributes['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    total_number_of_messages = int(total_number_of_visible_messges_in_the_sqs_request_queue + total_number_of_INvisible_messges_in_the_sqs_request_queue)
    return total_number_of_messages
# -------------------------------- Function to retrieve the total number of messages that are awaiting in the SQS Request Queue ----------------------------------------

# -------------------------------- Function to Scale out the EC2 instances as required----------------------------------------
def scale_out_ec2_instances(total_number_of_messages_present_in_the_SQS_Request_Queue , current_count_temp):
    print('Scaling Out the EC2 instances to handle the messages in the SQS Request Queue...')
    number_of_instances_to_scale_out = min(total_number_of_messages_present_in_the_SQS_Request_Queue - current_count_temp, maximum_count)
    for i in range(0 , number_of_instances_to_scale_out):
        instances = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1, InstanceType=instance_type, KeyName=key_name, SecurityGroupIds=[security_group_id,], TagSpecifications=[{'ResourceType': 'instance', 'Tags' : [{'Key': 'Name', 'Value': 'app-instance'+str(i)},]},], UserData=userdata)
        ec2_instance_list.append(instances['Instances'][0]['InstanceId'])
        print(current_count_temp)
        current_count_temp += 1
    print('Successfully scaled out - ', number_of_instances_to_scale_out , ' instances')
    additional_check_count_for_scale_out = total_number_of_messages_present_in_the_SQS_Request_Queue
    #print('setting additional_check_count_for_scale_out to total messages at this point which is = ', additional_check_count_for_scale_out)
    return current_count_temp
# -------------------------------- Function to Scale out the EC2 instances as required----------------------------------------

# -------------------------------- Function to Scale in the EC2 instances when all the messages have been processed----------------------------------------
def scaling_in_the_ec2_instances(total_number_of_messages_present_in_the_SQS_Request_Queue , current_count_temp):
    print('Scaling In the EC2 instances after all the messages in the SQS Request Queue have been processed...')
    for i in range(current_count_temp,total_number_of_messages_present_in_the_SQS_Request_Queue,-1):
        ec2.terminate_instances(InstanceIds = [ec2_instance_list.pop()])
        current_count_temp -= 1
        print(current_count_temp)
    return current_count_temp
# -------------------------------- Function to Scale in the EC2 instances when all the messages have been processed----------------------------------------


# --------------------------------Main part of the code which runs in a loop for every 30 seconds----------------------------------------
while True:
    try:
        print('Retrieving the number of awaiting messages from the Request Queue every 30 seconds...')
        
        total_number_of_messages_present_in_the_SQS_Request_Queue = retrieve_the_total_number_of_messages_present_in_the_SQS_Request_Queue()
        print('Total Number of Messages awaiting in the SQS Request Queue are: ', total_number_of_messages_present_in_the_SQS_Request_Queue)
        print('Total Number of EC2 Instances Running are: ', current_count)
        
        #Scale Out EC2 Instances
        if additional_check_count_for_scale_out < total_number_of_messages_present_in_the_SQS_Request_Queue:
            if total_number_of_messages_present_in_the_SQS_Request_Queue > current_count:
                if current_count < maximum_count:
                    current_count = scale_out_ec2_instances(total_number_of_messages_present_in_the_SQS_Request_Queue , current_count)
                    print("scale_out_ec2_instances Function - Return Point")
                        
        #Scale In App Tier Instances
        elif total_number_of_messages_present_in_the_SQS_Request_Queue <= (current_count-1) and current_count > minimum_count:
            current_count = scaling_in_the_ec2_instances(total_number_of_messages_present_in_the_SQS_Request_Queue , current_count)
            print("scaling_in_the_ec2_instances Function - Return Point")

        elif current_count < minimum_count:
            print('Starting minimum number of instances because the number of current ec2 instances running are less than the desired quantity which is 1...')
            instances = ec2.run_instances(ImageId=ami_id, MinCount=1, MaxCount=1, InstanceType=instance_type, KeyName=key_name, SecurityGroupIds=[security_group_id,], TagSpecifications=[{'ResourceType': 'instance', 'Tags' : [{'Key': 'Name', 'Value': 'app-instance'+str(current_count)},]},], UserData=userdata)
            ec2_instance_list.append(instances['Instances'][0]['InstanceId'])
            current_count += 1
            
        else:
            print('No Scaling Needed...')

        # make sure the controller.py file execution is sleeping for 30 sec so that the number of times the SQS Request Queue is not polled too many times
        time.sleep(30)

    except Exception as e:
        print("Exception Occured when running the controlle.py file :- ", e)
        break
# --------------------------------Main part of the code which runs in a loop for every 30 seconds----------------------------------------


# --------------------------------Logic used for autoscaling-----------------------------------------------------------------------------

# if total = 100:
#       Scale out 20 ec2 instances 
# elif total = 60: 
#        First scale in the currently running ec2 instances
#        Sleep for 15-20 sec 
#        Now again scale out 20 more new instances 
# elif total = 20: 
#        First scale in the currently running ec2 instances
#        Sleep for 15-20 sec 
#        Now again scale out 10 more new instances 
# elif total = 0:
#        If running ec2 instances present then  
#        First scale in the currently running ec2 instances
#        Sleep for 15-20 sec 
# else 
#       i.e., if there are no currently running ec2 instances then we need not do anything so NO SCALING REQUIRED

#-----------------------------------------------------------------------------------------------------------------------------------------