## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0
import boto3
import os
from botocore.exceptions import ClientError
import urllib.request
""" The below variables are created and assigned the Enviornment variables values. """
instance_store_id = os.environ.get('InstanceStoreID')
sso_instance_id = os.environ.get('SSOInstance')
instance_domain_name = os.environ.get('DomainName')
ps_admin = os.environ.get('SSOPermissionSetAdminOnlyAccess')
ps_viewonly = os.environ.get('SSOPermissionSetViewOnlyAccess')
topic_arn = os.environ.get('TopicARN')
ps_list = [ps_admin,ps_viewonly]
AD_group_required = []


def send_sns():
    """ This function will create a boto client and generate a dynamic message to send to the Owner email. 
        The custom message is create with Dynamic values. """
    sns = boto3.client('sns')
    custom_message = "Hi there,\n The AD Groups were not found on the AD: "+instance_domain_name+"\n Please create the AD Groups, as the automation will kick off again. The AD Groups are \n "
    for i in AD_group_required:
        custom_message = custom_message + "\n"+str(i)
    custom_message = custom_message + "\n \n The process will kick off in 30 minutes from now. Please contact your admin to turn off this automation should it be required. \n Thanks, \n AWS"
    
    try: 
        sns.publish(
            TopicArn = topic_arn,
            Subject = "AWS Automation - Please create AD Groups",
            Message = custom_message
        )
    except Exception as e: 
        print("Cannot send SNS: "+(e))


def ad_group_status_check(account,permission_set_name):
    """This Function, recieves the account and specific permission set which is being tested. 
       The function will then check if the AD Group has been created on the AD Directory. If so the unquie Group Id is returned."""

    client = boto3.client('identitystore')
    group_name = "aws-"+account+"-"+str(permission_set_name)
    print("Checking group name:"+group_name)
    try:
        response = client.list_groups(
            IdentityStoreId = str(instance_store_id),
            Filters=[
                {
                    'AttributePath': 'DisplayName',
                    'AttributeValue': group_name+'@'+instance_domain_name
                },
            ]
        )
        group_id = response['Groups'][0]['GroupId']
        print('Group ID: '+str(response))
        return group_id
    except:
        print("Acting for no AD Group")
        return None


def create_assignment(account,groupid,permission_set):
    """ This Function recieves the account, AD group ID and the permission Set. 
        The function then creates an account assignement between the three. """
    client = boto3.client('sso-admin')
    print("Creating assignment for "+ account + groupid + permission_set)
    try:
        response = client.create_account_assignment(
            InstanceArn = sso_instance_id,
            TargetId = account,
            TargetType = 'AWS_ACCOUNT',
            PermissionSetArn = str(permission_set),
            PrincipalType = 'GROUP',
            PrincipalId = groupid
        )
        print(response)
        print('Assignment complete')
    except ClientError:
        print(ClientError)
        print("Error unable to assign")
    

def ps_group_automation(account):
    """This function acts as the orchastration for this process. The function recieves each AWS account that has been passed to Lambda
        The function then generates the required Permission Set ID and Name - and passes these to the required functions to complete the process."""
    ps_list = [ps_admin,ps_viewonly]
    ps_count = 0
    permission_sets_name = ["Admin","ViewOnly"]
    for ps in permission_sets_name:
        group_id_response = ad_group_status_check(account,ps)
        if group_id_response == None:
            AD_group_required.append("aws-"+account+"-"+ps)
        else:
            create_assignment(account,group_id_response,ps_list[ps_count])
        ps_count = ps_count+1

def lambda_handler(event, context):
    """The lambda handler will recieve the list of accounts passed by Step Functions. 
       Each account is then passed to the functions aboved. 
       After each account has been processed. The final send_sns is processed to inform the OwnerEmail. """
    print(event)
    try: 

        for account in event: 
            print("Checking Group ID" + account)
            ps_group_automation(account)
        send_sns()
    except Exception as e: 
        print("Processing Failed "+(e))