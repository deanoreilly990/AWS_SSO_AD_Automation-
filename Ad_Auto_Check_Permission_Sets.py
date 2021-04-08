## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0
import boto3
import os
import urllib.request

""" The below variables are created and assigned the Enviornment variables values."""

instance_store_id = os.environ.get('InstanceStoreID')
instance_domain_name = os.environ.get('DomainName')
ps_admin = os.environ.get('SSOPermissionSetAdminOnlyAccess')
ps_viewonly = os.environ.get('SSOPermissionSetViewOnlyAccess')
permission_sets = [ps_admin, ps_viewonly]
sso_instance_id = os.environ.get('SSOInstance')
topic_arn = os.environ.get('TopicARN')
account_list = []
exclude_account_list = []


def send_sns(accounts):
    """ This function will create a boto client and generate a dynamic message to send to the Owner email. The custom message is create with Dynamic values. """
    sns = boto3.client('sns')
    custom_message = "Hi there,\n The following accounts and permission sets have been identified as begin required.\n Please ensure that the following AD groups are created to allow the automated assignment to proceed. The AD groups required are:"
    for i in accounts:
        custom_message = custom_message + "\n"+str("aws-"+i+"-ViewOnly") + "\n"+str("aws-"+i+"-Admin")
    custom_message = custom_message + "\n \n The process will kick off in 30 minutes from now. Please contact your admin to turn off this automation should it be required. \n Thanks, \n AWS"
    try:
        sns.publish(
            TopicArn = topic_arn,
            Subject = "AWS Automation - Please create AD Groups",
            Message = custom_message
        )
    except Exception as e: 
        print("Cannot send SNS: "+(e))
    

def add_account_to_list(account):
    """ This function recieves accounts which have been found in the organization service. 
        The function checks if the account is already in the list and if not, it will then append the account to the account list. """
        
    if account in account_list:
        pass
    else:
        account_list.append(account)

            
def check_account_permissions(accountid):
    """ This Function checks each account recieved for each of the Permission Sets that are being tested. 
        If the permisison set is not found, the account is added to a  list to be included in the automation assignment. """
    ps_count = False
    count = 0
    client = boto3.client('sso-admin')
    try:
        response = client.list_permission_sets_provisioned_to_account(
            InstanceArn = sso_instance_id,
            AccountId = accountid,
            ProvisioningStatus = 'LATEST_PERMISSION_SET_PROVISIONED'
        )
        print ("Number of Permissions Sets on Account :"+str(len(response["PermissionSets"])))
        per_sets = permission_sets
        print(per_sets)
        for ps in response["PermissionSets"]:
            print("Permission set testing:")
            print(ps)
            if str(ps) in per_sets:
                print("Match found:"+ ps)
                count = count+1
    except:
        print('No permissions found')
        return False
    if count == len(per_sets):
        print("All PS set on account")
        ps_count = True
    return ps_count


def list_org_accounts():
    """ This Function is used to query the organization service and list all accounts. 
        The Accounts are then appended to send to a control function which adds them to a global list."""
    try:
        client = boto3.client('organizations')
        response = client.get_paginator('list_accounts')
        response_iterator = response.paginate()
        for i in response_iterator:
            accounts = i['Accounts']
            for account in accounts: 
                add_account_to_list(account['Id'])
    except IOError:
        print('Error with Account Listing')

def check_permission_sets():
    """This Function orchastrates each of the accounts check process."""
    accounts_update = []
    for account in account_list:
        print("Checking Account:"+ account)
        permissions = check_account_permissions(account)
        if permissions == False: 
            accounts_update.append(account)
            print("Permission Set Confirmed:"+ str(permissions))
        else:
            pass
    return accounts_update


def lambda_handler(event, context):
    """ The Lambda function, kicks off the process. Once all accounts have been tested, the Email notication is then sent to the Owner. 
        The list of accounts is then passed back to the StepFunction service. """
    account_list=[]
    list_org_accounts()
    try: 
        print(account_list)
        acc_list_update=check_permission_sets()
        print (acc_list_update)
        send_sns(acc_list_update)
        return acc_list_update
    except Exception as e: 
        print("Processing Failed "+(e))
