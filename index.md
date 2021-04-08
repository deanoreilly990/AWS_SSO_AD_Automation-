#  Use Active Directory to manage User access to AWS Accounts

For many [Amazon Web Services(AWS)](https://aws.amazon.com/) Customers, AWS [Single Sign-On(SSO)](https://aws.amazon.com/single-sign-on/) offers for a flexible way to manage access to AWS accounts. AWS SSO also allows for the efficient management of user permissions to allow access to these accounts.

AWS offers [AWS Directory Service(AD Connector)](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_ad_connector.html). This feature, allows for Microsoft Active Directory Service to authenticate users on the AWS Platform.

In medium to large  scale AWS Environments, SysOps engineers can spend alot of time provisioning user access and permissions to AWS Accounts of which they manage. In this solution we will look at how to automatically manage user permissions and access in AWS Environment through Active Directory. This solution, will utilise several AWS services, along with the newly released  [AWS Single Sign-On API&#39;s](https://aws.amazon.com/about-aws/whats-new/2020/09/aws-single-sign-on-adds-account-assignment-apis-and-aws-cloudformation-support-to-automate-multi-account-access-management/). The solution utilises the `sso-admin` API.

This solution, uses the following AWS Services:

- AWS CloudFormation
- Amazon CloudWatch
- AWS Lambda
- AWS Single Sign-On
- AWS Step Functions
- Amazon Simple Notification Service (Amazon SNS)
- AWS Directory Service

![](RackMultipart20210408-4-1tinyxx_html_b248efb1b261b449.jpg)

Image: Solution Process Flow

In this solution, the AWS AD Connector will be utilised to allow for the authentication of AD Users credentials. This blog post will also walk through the setup of the AD Connector Directory in AWS as the SSO Directory. The AD Connector, allow for users and groups which are located in a Microsoft AD, to be used as identities in the Directory Service located in the AWS Environment. These users and groups can be assigned Permission Sets specific to individual AWS Accounts. These permission sets allow for the AD group or user to assume the permission.

This solution will check all existing AWS Accounts associated with a  AWS SSO, then generate a list of all accounts associated. From there, two permissions sets(defined in the example- Admin &amp; ViewOnly) will be automatically assigned to Active Directory groups. Each AWS Account will require the creation of two Active Directory groups:

AWS-\&lt;AccountID\&gt;-Admin

AWS-\&lt;AccountID\&gt;-ViewOnly

The Admin Permission Set which is created in this solution, allows for new resources to be created, but prevents any existing CloudFormation resources to be deleted or updated.

## Pre-requirements

The following prerequisites must exist before conducting this solution:

- AD Connector already configured in the AWS Directory Service. For information on this, please see here [https://docs.aws.amazon.com/directoryservice/latest/admin-guide/create\_ad\_connector.html](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/create_ad_connector.html)
  - The AD Connector does require specific network configuration, specifically - to be configured in an VPC which has access to the Active Directory server. For additional information on Active Directory Connector see [here](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_ad_connector.html).
- AWS Organizations and AWS SSO configured. AWS SSO is integrated with AWS Organizations. All AWS Accounts in the organization will be checked in this example. For that reason, AWS SSO must  be configured for all AWS Accounts beforehand - please see [https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-accounts.html](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-accounts.html).
- Access to create new Active Directory Groups and Users
- Permission to Launch AWS Cloud-formation in the AWS Organisation/SSO Account.

## Descriptions of the Flow Steps

##

The image below, identifies the process flow which this automation flow follows, along with the AWS Services that is used to achieve this process.

![](RackMultipart20210408-4-1tinyxx_html_d8e9559645b50df0.png) ![](RackMultipart20210408-4-1tinyxx_html_a90f7838a0287bd7.jpg)

Image: Solution Architecture and process flow

## Descriptions of the Flow Steps

1. **AWS CloudWatch Event: Kicks off AWS Step Functions**

    1. AWS CloudWatch Events, allows for scheduled or rule based strings to be used to schedule events to trigger. With these events - triggers can target on or more resources in AWS and kick off an execution.
    2. In our case, the CloudWatch Event is with a rule based string, to trigger the Step Functions Resource.
1. **AWS Step Functions for orchestration: **

    1. Step Functions, allows for the definition of state machines. These resources allow for the orchestration between AWS resources.
    2. In our case, the Step Functions service, will orchestrate the AWS Lambda execution along with allowing for a wait period between functions.
    3. The following steps are located within the Step Functions Service:
2. **AWS Lambda - Check Permission Sets: **

    1. This Lambda functions acts as the check. The Lambda function checks the Accounts within the associated SSO service. For each account, there should be two permission sets as per our demo. The Lambda function, makes a list of the accounts which does not have both of these Permission Sets associated. Once it has checked all the accounts, it generates a message which is then sent to the SNS Topic. The Permission Sets which it checks for are:
      1. aws-\&lt;account-id\&gt;-AdminOnly
      2. aws-\&lt;account-id\&gt;-ViewOnly
3. **AWS SNS - Send Notification: **

    1. Once the Lambda function generates the list of accounts which require the new permission sets. It sends a message to the SNS topic. The message will include a list of AD groups which you need to ensure to create. This email can be delivered to a specific email address such as a Service Desk.
    2. The SNS topic is also used to deliver an update on the AD groups which could not be found on the active directory.
4. **Step Functions Wait Period: **
  1. To allow System Operation engineers time to create the required AD groups, the Step Functions will wait for 30 minutes before beginning the next step.
  2. If the AD group is not created, the assignment of AD Groups and Permission Sets cannot move forward. The process will flag the account as having no AD Groups and send a summary email of the accounts which failed to have the required AD groups created.
5. **AWS Lambda - Set Permission Sets: **
  1. After the wait period is complete, the Step Functions will then send the list of accounts which require permission set assignment to the SetPermissionSets Lambda Function. This function will :
    1. Search the on-premise AD for the groups mentioned above for each of the accounts.
    2. If the AD group exists, the Lambda function will then create the assignment of the Permission Set to the AD group and AWS Account.
    3. If the AD group does not exist, it will send a list of AD Groups which were not located on the AD.
    4. Once completed, any changes that have occurred will be sent to the SNS Topic to the same email address.

##

## Configure your AD Connector as your Directory Service

Our solution utilises the connection between the on-premise Active Directory and the AWS Single Sign-On service. To allow for the solution to successfully look up the Active Directory Groups, the AD Connector must be selected as the Directory for the identity source.

If you have not already done so, please follow the following steps to select the AD Connector Directory as your Identity Source:

1. Log into the AWS Console and select the [AWS Single Sign-On Service](https://ap-southeast-2.console.aws.amazon.com/singlesignon/home?region=ap-southeast-2)
2. Under &#39;Settings&#39; perform the following:

  - Identity Source: Change
  - Select Active Directory:
    - In the Drop Down - select your AD Connector which you have set-up prior.
  - Review and ensure you have read the Conditions

![](RackMultipart20210408-4-1tinyxx_html_21f14e74ff607b86.png) ![](RackMultipart20210408-4-1tinyxx_html_a0a998cb4d51312f.jpg)

Image: Choosing identity store in AWS SSO

Now that your Identity Source is changed to the Active Directory, we can perform the following tests to ensure we are ready for the next phase.

### Test allocation of Permission Sets to an Active Directory User

As we will be using the Single Sign on from here on, we will need to assign the correct permission sets to the engineer which is performing the following setup.

With Permission Sets, several preconfigured permission sets are already configured with in the AWS SSO Service. For this use case we will be assigning the AD User(we recommend to use your own as it will be secure) and assigning that user the **Administrator Permission Set** on the Management AWS Account.

To complete this manual task, perform the following steps:

1. Locate the Single Sign On Console page
2. Under Accounts : Select the Management Account
3. Select Assign Users
4. You will see your AD DNS Name: search for your Active Directory User

![](RackMultipart20210408-4-1tinyxx_html_b791b02b951c5c0d.png) ![](RackMultipart20210408-4-1tinyxx_html_ee212e74ecb9c096.jpg)

Image: Manually selecting AD Groups in AWS SSO

1. Select the AWSAdministratorAccess Permission Set from the list
2. Finish

To test access:

1. Locate the User Portal URL - which can be found in Settings
2. Open the URL in a In-Cognito web browser
3. Login using your AD Username and password

You should now see the allocated AWS Accounts:

![](RackMultipart20210408-4-1tinyxx_html_80489c621ac8161e.png) ![](RackMultipart20210408-4-1tinyxx_html_a8aadf39e31c615a.jpg)

Image: AWS SSO Login Page – Account Listing

## Launch the Automation AD Stack

Now that we have successfully tested the manual process of assigning an AD User with a permission set on an AWS Account. We can now deploy the following stacks onto our Management account.

The management account is the account which the Control Tower is setup in. The following stacks, use API&#39;s which are available on this account to interact with the services needed.

**Lambda function Upload to S3: **

With AWS CloudFormation, there are multiple ways to deploy Lambda functions. These can be seen here([https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html)). In our solution, due to the size of the Lambda functions, they will need to be zipped upload to an S3 bucket. The S3 bucket will need to be in the same account that you are launching this stack. The Management account of your AWS Control Tower.

The Lambda functions are zipped and ready to be uploaded directly to your S3 Bucket.

**\&lt;\&lt;\&lt;Lambda\_zip\_Functions\&gt;\&gt;**

Please note the the Bucket and Key name - as these will be required in the parameters in your CloudFormation.

## Deployment of the AD Automation Stack

Once the Lambda functions have been uploaded as zipped to the S3 bucket. You can now launch the CloudFormation template. The Template will create several resources, which we have discussed during this article. The image below, identifies the resources which are automatically deployed to your AWS Account.

I ![](RackMultipart20210408-4-1tinyxx_html_c85a5c3e79c94cb8.jpg)
 mage: AWS Resources created

 Each of these services and its use case is explained:

1. **Step Functions: **
  1. The Step function service is used to orchestrate the activity flow. The Step Functions is kicked off by the Cloudwatch Event.
2. **Step Functions Role: **
  1. The Step Functions role, provides the Step Functions resource with the permission required to launch both of the Lambda functions.
3. **CloudWatch Events: **
  1. The Cloudwatch event, is configured with a rule based string. This string controls how often the Step Functions is executed.
4. **Cloudwatch Event Role: **
  1. The CW event requires permission in order to execute the Step Function resource. The role attached provides that levels of permissions.
5. **Lambda function: **
  1. In this example, there are two Lambda functions being used:
    1. CheckPermissionSetsAccountLambda:
    2. SetPermissionSetAssignmentLambda:
6. **Lambda Function Role: **
  1. One Lambda role is used for both of the Lambda functions. The Role allows for:
    1. Default Lambda permissions with CloudWatch Logs
    2. Required permissions for the SSO Service
    3. Permission required for the SNS Topic Publish Message
7. **SNS Topic: **
  1. The SNS Topic is created and a subscription is added. The subscription is the email address you add for the pre-req&#39;s.

In order to deploy the stack, the following parameters are required.

**Parameters: **

1. **InstanceStore** : Instance Store ID from the AWS Directory Service. This is the Instance Store ID of the Directory which you have attached to your AWS SSO.
2. **SSODomainInstanceArn** : Your SSO ARN - This can be found in the Settings tab of the  AWS SSO Console
3. **OwnerEmail** : this is the email address to send the SNS messages to.
4. **CWEventRule** : This is the string which defines the frequency for the Permission Sets Checks to be carried out.
  1. Default: rate(30 minutes)
5. **SSODomainName** : This is the domain name for the Active Directory you are using with your AWS SSO.
6. **S3BucketName** : The S3 bucket where the Lambda functions have been uploaded to.
7. **LambdaCheckKey** : The name of the S3 file zip file that holds the check lambda function. Default set as checkpermission.zip
8. **LambdaSetKey** : The name of the S3 file zip file that holds the set lambda function. Default set as setpermission.zip

Once you launch the CloudFormation template, the resources mentioned above will be created in the AWS Account. During the setup, the email address you supply will receive a subscription notification from SNS. Please ensure you Confirm this subscription(Link on email).

## Automation in action

Once the template is fully uploaded, the Cloudwatch Event will automatically trigger in 30minutes once successfully launched. Once trigger, the Lambda function (CheckPermissionSetsAccountsLambda) will look up all AWS Accounts associated with your SSO Domain. It will then check each account to ensure that the Admin and ViewOnly Permission Sets have been assigned to these accounts. If they have not been, an email will be sent to your OwnerEmail address with a list of AD groups required.

Once the Email has been published, the process will wait 30 Minutes, to allow an Engineer to action, then the Lambda function (SetPermissionSetAssignmentLambda) will then receive the list of accounts which do not have both Permission Sets assigned. The Lambda function, will then look up to see if each of the AD groups required has been created on the Active Directory. If they have been, the Lambda function will then automatically, create an assignment for each of the Permission Set to the correct AD Group for each of the Accounts that require them.

If the AD group have not been created, an email is then sent to the OwnerEmail with the list of AD groups that is still required.

### Test the access:

Once the AD Group has been created, you can begin assigning AD users to these Groups. These AD Users, will assume the same permissions and access which is assigned to the AD Group. This means, for any AD Group which the users are assigned, the same level of permission is on the User.

When these AD Users login to the AWS SSO Console, they will now see the AWS Accounts which they have been assigned to an AD Automation Group through the Automation process. The users, will only see the corresponding Permission Set which has been assigned through the AD Group.

For example, if you have given the AD User Bob, to a AD Group : aws-123456789-ViewOnly. When Bob logs into the AWS SSO Console, Bob will only see the ViewOnly Permission for the AWS Account 123456789.

## Conclusion

Once implemented, the solution will allow for the automated assignment of Permission Sets on AWS Accounts to corresponding Active Directory Groups. This automated, will allow for System Operations Engineers to reduce time required to login and manually create this assignment, thus increasing the time to complete new account registration.

System Operations Engineers, have the ability to further enhance this solution by creating automated script on the AD server to automatically create the Active Directory group, allowing for even faster account creation and access assignment. These automation processes allow for the reduce time spent on repetitive tasks by SysOps Engineers.

Following this article, SysOps Engineers, should look to further automating this process by extending out the number of permission sets required by your Organization. Be sure to follow best practices and apply least privilege.

Organizations, should also review how they can move on-premise Active Directory to AWS Managed Active Directory. This can be found here: https://aws.amazon.com/blogs/security/how-to-migrate-your-on-premises-domain-to-aws-managed-microsoft-ad-using-admt/