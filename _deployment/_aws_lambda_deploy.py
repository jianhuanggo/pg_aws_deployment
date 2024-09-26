from typing import List, Union
import os
import boto3
from logging import Logger as Log
from inspect import currentframe
import subprocess
import json
from time import sleep
from boto3 import client
import base64
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from _common import _common as _common_
from _engine import _engine as _engine_
from _util import _util_common as _util_common


"""
given a lambda role called "lambda-ex6", first write a function to check its existence 
and then if it does exist, write another function to delete it.  and then write a 
function to create it, for functions, please include detail error handling as well as comments

create a separate function for get_method_response method and delete_method_response s


base on following, write a function that gets all the integration from aws

response = client.get_integrations(
    ApiId='string',
    MaxResults='string',
    NextToken='string'
)

"""

_WAIT_TIME_ = 2


def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


def check_ecr_repository_exists(repository_name) -> bool:
    try:
        ecr_client = aws_client("ecr", "us-east-1")
        _parameters = {
            "repositoryNames": [repository_name]
        }
        response = ecr_client.describe_repositories(**_parameters)

        # If the repository exists, it will return the repository details
        if repo := response.get("repositories"):
            _common_.info_logger(f"Repository {repo} exists. skipping repo creation process...")
            return True

    except ClientError as err:
        if err.response.get("Error", {}).get("Code", "") == 'RepositoryNotFoundException':
            _common_.info_logger(f"Error: Repository '{repository_name}' not found.")
        elif err.response.get("Error", {}).get("Code", "") == 'RepositoryNotEmptyException':
            _common_.info_logger(f"Error: Repository '{repository_name}' is not empty. Use force=True to delete it anyway.")
        else:
            _common_.info_logger(f"Unexpected error: {err}")
    return False


def delete_ecr_repository(repository_name,
                          aws_region: str = "us-east-1",
                          force: bool = False) -> bool:
    """Deletes an Amazon ECR repository.

    Args:
        repository_name: The name of the repository to delete.
        aws_region: aws region
        force: If True, deletes the repository even if it contains images.

    return:
        bool: True if the repository was deleted successfully, False otherwise.
    """
    try:
        ecr_client = aws_client("ecr", aws_region)
        _parameters = {
            "repositoryName": repository_name,
            "force": force
        }
        response = ecr_client.delete_repository(**_parameters)
        _common_.info_logger(response)
        _common_.info_logger(f"Repository '{repository_name}' deleted successfully.")
        return True

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        if err.response.get("Error", {}).get("Code", "") == 'RepositoryNotFoundException':
            _common_.info_logger(f"Error: Repository '{repository_name}' not found.")
        elif err.response.get("Error", {}).get("Code", "") == 'RepositoryNotEmptyException':
            _common_.info_logger(f"Error: Repository '{repository_name}' is not empty. Use force=True to delete it anyway.")
        else:
            _common_.info_logger(f"Unexpected error: {err}")
    return False

def create_ecr_repository(repository_name: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> Union[List, None]:
    """Creates an Amazon ECR repository.

    Args:
        repository_name: The name of the repository to delete.
        aws_region: aws region
        tags: If True, deletes the repository even if it contains images.
        logger: The logger object to use for logging.

    return:
        repository arn and repositoryURI
    """
    ecr_client = aws_client("ecr", aws_region)

    try:
        _parameters = {
            "repositoryName": repository_name
        }
        response = ecr_client.create_repository(**_parameters)
        _common_.info_logger(f"Repository '{repository_name}' created successfully.")
        return [response.get("repository", {}).get("repositoryArn"), response.get("repository", {}).get("repositoryUri")]
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        if err.response.get("Error", {}).get("Code", "") == 'RepositoryAlreadyExistsException':
            _common_.info_logger(f"Error: Repository '{repository_name}' already exists.")
        else:
            _common_.error_logger(currentframe().f_code.co_name,
                                  err,
                                  logger=logger,
                                  mode="error",
                                  ignore_flag=False)


def get_ecr_login_password(aws_region: str = "us-east-1") -> tuple[str, str, str]:
    """Retrieves the Docker login credentials for Amazon ECR.

    :return: A tuple containing the username, password, and proxy endpoint.
    """
    ecr_client = aws_client("ecr", aws_region)

    try:
        # Retrieve the authorization token from ECR

        response = ecr_client.get_authorization_token()

        # Extract the authorization data
        auth_data = response.get("authorizationData")[0]
        auth_token = auth_data.get("authorizationToken")

        # Decode the base64-encoded authorization token
        decoded_token = base64.b64decode(auth_token).decode('utf-8')

        # Split the decoded token into username and password
        username, password = decoded_token.split(':')

        # Extract the proxy endpoint
        proxy_endpoint = auth_data.get("proxyEndpoint")

        return username, password, proxy_endpoint

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
        return None, None, None
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
        return None, None, None
    except ClientError as err:
        _common_.info_logger(f"Error: {err.response.get('Error', {}).get('Message')}")
        return None, None, None
    except KeyError as err:
        _common_.info_logger(f"Error: Key {err} not found in the response.")
        return None, None, None
    except Exception as err:
        _common_.info_logger(f"Unexpected error: {err}")
        return None, None, None


@_common_.exception_handler
def build_docker_image(repository_name: str,
                       aws_account_number: str,
                       aws_region: str,
                       path: str = ".") -> bool:

    # Build, tag, and push Docker image
    _common_.info_logger("Building Docker image...")

    build_cmd = f'docker build -t {repository_name} {path}'
    _engine_.run_command_progress(build_cmd)
    _common_.info_logger("Docker build completed.")

    # Tag Docker image
    _common_.info_logger("tagging docker image...")
    tag_cmd = f'docker tag {repository_name}:latest {aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:latest'
    _engine_.run_command_progress(tag_cmd)
    _common_.info_logger("tagging docker image is tagged.")


    # Push image to ECR
    _common_.info_logger("pushing docker image to ecr...")
    push_cmd = f'docker push {aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:latest'
    _engine_.run_command_progress(push_cmd)
    _common_.info_logger("pushing docker image is completed.")
    return True

def check_role_exists(aws_role_name: str,
                      aws_region: str = "us-east-1") -> bool:
    """Checks if a specified IAM role exists.

    Args:
        aws_role_name: The name of the IAM role to check.
        aws_region: aws region

    Returns:
        True if the role exists, False otherwise.

    """
    try:
        iam_client = aws_client("iam", aws_region)
        _parameters = {
            "RoleName": aws_role_name
        }
        iam_client.get_role(**_parameters)
        _common_.info_logger(f"Role '{aws_role_name}' exists.")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        _common_.info_logger(f"Role '{aws_role_name}' does not exist.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def delete_role(aws_role_name: str,
                aws_region: str = "us-east-1") -> bool:

    """    Deletes a specified IAM role.

    Args:
        aws_role_name: The name of the IAM role to delete.
        aws_region: aws region

    Returns:
        True if the role was deleted successfully, False
    """
    try:
        iam_client = aws_client("iam", aws_region)
        _parameters = {
            "RoleName": aws_role_name
        }
        iam_client.delete_role(RoleName=aws_role_name)
        _common_.info_logger(f"Role '{aws_role_name}' deleted successfully.")
        return True
    except iam_client.exceptions.NoSuchEntityException:
        _common_.info_logger(f"Error: Role '{aws_role_name}' does not exist.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def create_role(aws_role_name: str,
                assume_role_policy_document: dict,
                aws_region: str = "us-east-1") -> Union[str, None]:
    """

    Args:
        aws_role_name: The name of the IAM role to create.
        assume_role_policy_document: The policy document that grants an entity permission to assume the role.
        aws_region: aws region

    Returns:
        role arn if the role is deleted successfully else None

    """

    try:
        iam_client = aws_client("iam", aws_region)
        _parameters = {
            "RoleName": aws_role_name,
            "AssumeRolePolicyDocument": json.dumps(assume_role_policy_document)
        }
        response = iam_client.create_role(**_parameters)
        # print(response)
        _common_.info_logger(f"Role '{aws_role_name}' created successfully.")
        return response.get("Role", {}).get("Arn")

    except iam_client.exceptions.EntityAlreadyExistsException:
        _common_.info_logger(f"Error: Role '{aws_role_name}' already exists.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return None

def attach_policy_to_role(role_name: str,
                          policy_arn: str,
                          aws_region: str = "us-east-1"):
    try:
        iam_client = aws_client("iam", aws_region)
        _parameters = {
            "RoleName": role_name,
            "PolicyArn": policy_arn
        }
        iam_client.attach_role_policy(**_parameters)
        _common_.info_logger(f"Attached policy {policy_arn} to role {role_name}")
    except iam_client.exceptions.NoSuchEntityException:
        _common_.info_logger(f"Error: Role '{role_name}' or policy '{policy_arn}' does not exist.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        # Catch other client errors and print the error message
        _common_.info_logger(f"Error attaching policy: {err.response['Error']['Message']}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)


@_common_.exception_handler
def create_lambda_function_role(aws_role_name: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None
                                ) -> Union[str, None]:
    """Create lamda function role

    Args:
        aws_role_name: The name of the IAM role to create.
        aws_region: aws region
        logger: The logger object to use for logging.

    Returns:
        role arn if the role is deleted successfully else None

    """
    # need to create a policy
    ADMIN_POLICY_ARN = 'arn:aws:iam::aws:policy/AdministratorAccess'
    assume_lambda_trust_role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    role_arn = create_role(aws_role_name, assume_lambda_trust_role_policy, aws_region)
    attach_policy_to_role(aws_role_name, ADMIN_POLICY_ARN)
    return role_arn


def check_lambda_function_exists(function_name: str,
                                 aws_region: str = "us-east-1") -> bool:
    """checks if a specified aws lambda function exists.

    Args:
        function_name: the name of the lambda function
        aws_region: aws region

    Returns:
        True if the function exists, False otherwise.

    """

    try:
        # Attempt to get the Lambda function configuration
        lambda_client = aws_client("lambda", aws_region)
        _parameters = {
            "FunctionName": function_name
        }
        lambda_client.get_function(**_parameters)
        print(f"Lambda function '{function_name}' exists.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"Lambda function '{function_name}' does not exist.")
    except NoCredentialsError:
        print("Error: No AWS credentials found.")
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        print(f"Unexpected error: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def delete_lambda_function(function_name: str,
                           aws_region: str = "us-east-1"):
    """deletes a specified aws Lambda function

    Args:
        function_name: the name of the lambda function
        aws_region: aws region

    Returns:
        True if the function exists, False otherwise.

    """

    try:
        # Attempt to delete the Lambda function
        lambda_client = aws_client("lambda", aws_region)
        _parameters = {
            "FunctionName": function_name
        }
        lambda_client.delete_function(**_parameters)
        _common_.info_logger(f"Lambda function '{function_name}' deleted successfully.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        _common_.info_logger(f"Error: Lambda function '{function_name}' does not exist.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err.response['Error']['Message']}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)


def create_lambda_function(function_name: str,
                           image_uri: str,
                           aws_region: str,
                           lambda_function_role_arn: str,
                           timeout: int = 30,
                           logger: Log = None) -> Union[str, None]:

    """Creates an AWS Lambda function using an image stored in an ECR repository.

    Args:
        function_name: The name of the lambda function.
        aws_account_number: The aws account number.
        aws_region: The aws region where the Lambda function will be created.
        lambda_function_role_arn: The name of the iam role that the Lambda function will assume.
        timeout: The amount of time that Lambda allows a function to run before stopping it.
        logger: The logger object to use for logging.

    Returns:
         The arn of the created Lambda function.

    """

    # Initialize the Lambda client
    lambda_client = boto3.client('lambda', region_name=aws_region)

    try:
        # Create the Lambda function
        _parameters = {
            "FunctionName": function_name,
            "PackageType": "Image",
            "Role": lambda_function_role_arn,
            # "Code": {"ImageUri": f'{aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{function_name}:latest'},
            "Code": {"ImageUri": image_uri},
            "Timeout": timeout
        }
        response = lambda_client.create_function(**_parameters)
        _common_.info_logger(f"Lambda function {function_name} created ")
        return response.get("FunctionArn")

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except lambda_client.exceptions.ResourceConflictException:
        _common_.info_logger(f"Error: A Lambda function with the name {function_name} already exists.")
    except lambda_client.exceptions.InvalidParameterValueException as err:
        _common_.info_logger(f"Error: Invalid parameter value - {err}")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    return None


def get_api_gateway_resource_id(aws_region: str,
                                api_gateway_api_id: str,
                                lambda_function_name: str) -> Union[str, None]:

    """Checks if an API Gateway resource exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        lambda_function_name: the name of the lambda function (used as the resource path)

    Returns:
        the id of the resource if it exists, None otherwise.

    """
    try:
        # Get the list of resources
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        resources = apigateway_client.get_resources(restApiId=api_gateway_api_id)

        # Find the resource ID if it exists
        resource_id = next((item.get("id") for item in resources.get("items", []) if item.get("pathPart") == lambda_function_name), None)
        if resource_id:
            _common_.info_logger(f"Resource '{lambda_function_name}' exists with ID: {resource_id}.")
            return resource_id
        else:
            _common_.info_logger(f"Resource '{lambda_function_name}' not found.")
            return None

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return None



def delete_api_gateway_resource(aws_region: str,
                                api_gateway_api_id: str,
                                resource_id: str):
    """Deletes an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource to be deleted

    Returns:
        True if the resource was deleted successfully, False otherwise.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameter = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id
        }
        apigateway_client.delete_resource(**_parameter)
        _common_.info_logger(f"Resource with ID '{resource_id}' deleted successfully.")
        return True

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False




def create_api_gateway_resource(aws_region: str,
                                api_gateway_api_id: str,
                                api_gateway_root_res_id: str,
                                lambda_function_name: str) -> Union[str, None]:
    """Creates a new API Gateway resource.

    Args:
        aws_region:
        api_gateway_api_id: the id of the api gateway api.
        api_gateway_root_res_id: the id of the root resource in the api gateway.
        lambda_function_name: the name of the lambda function (used as the resource path)

    Returns:
        the id of the newly created resource.

    """

    try:
        # Create the new resource
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "parentId": api_gateway_root_res_id,
            "pathPart": lambda_function_name
        }
        resource_response = apigateway_client.create_resource(**_parameters)
        _common_.info_logger(f"Resource '{lambda_function_name}' created successfully.")
        return resource_response.get("id")

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as e:
        _common_.info_logger(f"ClientError: {e.response['Error']['Message']}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return None


def get_api_gateway_method(aws_region: str,
                           api_gateway_api_id: str,
                           resource_id: str,
                           http_method: str) -> Union[str, None]:

    """Checks if an API Gateway method exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method

    Returns:
        the id of the resource if it exists, None otherwise.

    """
    try:
        # Get the list of method
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method
        }
        method = apigateway_client.get_method(**_parameters)
        print(method)
        print(f"HTTP method '{http_method}' exists for resource ID '{resource_id}'.")
        return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"HTTP method '{http_method}' does not exist for resource ID '{resource_id}'.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return None

def delete_api_gateway_method(aws_region: str,
                              api_gateway_api_id: str,
                              resource_id: str,
                              http_method: str) -> bool:

    """Deletes an API Gateway method if it exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method

    Returns:
        True if it is successful otherwise False.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method
        }
        apigateway_client.delete_method(**_parameters)
        _common_.info_logger(f"Method '{http_method}' deleted successfully for resource ID '{resource_id}'.")
        return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Method '{http_method}' not found for resource ID '{resource_id}'.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response['Error']['Message']}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


def create_api_gateway_method(aws_region: str,
                              api_gateway_api_id: str,
                              resource_id: str,
                              http_method='GET') -> bool:

    """creates an api gateway method.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method

    Returns:
        True if it is successful otherwise False.

    """
    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "authorizationType": "NONE",
            "apiKeyRequired": False
        }
        apigateway_client.put_method(**_parameters)
        _common_.info_logger(f"Method '{http_method}' created successfully for resource ID '{resource_id}'.")
        return True

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")

    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False




def get_api_gateway_integration(aws_region: str,
                                api_gateway_api_id: str,
                                resource_id: str,
                                http_method='GET'
                                ) -> List:
    """Checks if an api Gateway integration exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.

    Returns:
        True if the integration exists, False otherwise.

    """
    try:

        # Attempt to retrieve the integration configuration
        apigateway_client = boto3.client('apigateway', region_name=aws_region)

        # apigateway_client = boto3.client('apigatewayv2')
        all_integrations = []
        next_token = None

        response = apigateway_client.get_integration(
            restApiId='string',
            resourceId='string',
            httpMethod='string'
        )
        print(response)
        exit(0)

        while True:
            try:
                # Fetch integrations with or without the NextToken
                if next_token:
                    response = apigateway_client.get_integrations(
                        ApiId=api_gateway_api_id,
                        NextToken=next_token
                    )
                else:
                    _paremeters = {
                        "ApiId": api_gateway_api_id
                    }
                    print(_paremeters)
                    response = apigateway_client.get_integrations(**_paremeters)
                print(response)
                exit(0)

                # Append fetched integrations to the list
                all_integrations.extend(response.get('Items', []))

                # Update the next_token for the next iteration
                next_token = response.get('NextToken')

                # If there's no next_token, exit the loop
                if not next_token:
                    break

            except ClientError as e:
                # Handle client errors (e.g., authentication issues, permissions)
                print(f"Failed to get integrations: {e.response['Error']['Message']}")
                break
            except Exception as e:
                # Handle any other exceptions
                print(f"Unexpected error: {e}")
                break

        return all_integrations
        # _parameters = {
        #     "restApiId": api_gateway_api_id,
        #     "resourceId": resource_id,
        #     "httpMethod": http_method
        # }
        # print("AAAA##@@#")
        # print(_parameters)
        # exit(0)
        # integration = apigateway_client.get_integration(**_parameters)
        # print(integration)
        # _common_.info_logger(f"Integration for HTTP method '{http_method}' exists for resource ID '{resource_id}'.")
        # return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Integration for HTTP method '{http_method}' does not exist for resource ID '{resource_id}'.")
        return False
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
        return False
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
        return False
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
        return False
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    return False

def delete_api_gateway_integration(aws_region: str,
                                   api_gateway_api_id: str,
                                   resource_id: str,
                                   http_method: str) -> bool:
    """deletes an existing integration in an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the integration
        http_method: the http method

    Returns:
        True if the integration exists other False.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method
        }
        apigateway_client.delete_integration(**_parameters)
        _common_.info_logger(f"Integration for HTTP method '{http_method}' deleted successfully for resource ID '{resource_id}'.")
        return True

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Integration for HTTP method '{http_method}' not found for resource ID '{resource_id}'.")
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False

def create_api_gateway_integration(aws_region: str,
                       api_gateway_api_id: str,
                       resource_id: str,
                       http_method: str,
                       aws_account_number: str,
                       lambda_function_name: str):
    """creates a new integration in an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: The ID of the API Gateway API
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        aws_account_number: the aws account number
        ecr_repository_name: the name of the repository containing the Lambda function.
        lambda_function_name: the name of the Lambda function.

    Returns:
        True if the integration exists other False.

    """

    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)

        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "type": "AWS_PROXY",
            "integrationHttpMethod": "POST",
            "uri": f"arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{aws_account_number}:function:{lambda_function_name}/invocations",
            "credentials": f"arn:aws:iam::{aws_account_number}:role/role-api-gateway-ex"
        }
        apigateway_client.put_integration(**_parameters)
        _common_.info_logger(f"Integration for HTTP method '{http_method}' created successfully for resource ID '{resource_id}'.")
        return True

    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return False


import boto3
from botocore.exceptions import ClientError


def get_api_gateway_method_response(aws_region: str,
                                    api_gateway_api_id: str,
                                    resource_id: str,
                                    http_method: str,
                                    status_code: str) -> bool:
    """checks if an api gateway method response exists.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the method.
        http_method: the http method

    Returns:
        True if the integration exists, False otherwise.

    """
    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "statusCode": status_code
        }
        response = apigateway_client.get_method_response(**_parameters)
        return response
    except ClientError as err:
        if err.response.get("Error", {}).get("Code") == 'NotFoundException':
            _common_.info_logger(f"No existing method response found for {http_method} {status_code}")
            return None
        else:
            _common_.info_logger(f"Unexpected error: {err}")
            raise


def delete_api_gateway_method_response(aws_region: str,
                                       api_gateway_api_id: str,
                                       resource_id: str,
                                       http_method: str,
                                       status_code: str) -> bool:
    """deletes an existing api_gateway method response in an API Gateway resource.

    Args:
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        resource_id: the id of the resource that contains the integration
        http_method: the http method
        status_code: the status code

    Returns:
        True if the integration exists other False.

    """
    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "resourceId": resource_id,
            "httpMethod": http_method,
            "statusCode": status_code
        }
        apigateway_client.delete_method_response(**_parameters)
        _common_.info_logger(f"Deleted existing method response for {http_method} {status_code}")
        return True
    except ClientError as err:
        _common_.info_logger(f"Failed to delete method response: {err}")
    return False


def create_api_gateway_method_response(aws_region: str,
                                       api_gateway_api_id,
                                       resource_id: str,
                                       http_method: str,
                                       status_code: str) -> bool:
    # Create a new method response
    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    _parameters = {
        "restApiId": api_gateway_api_id,
        "resourceId": resource_id,
        "httpMethod": http_method,
        "statusCode": status_code,
        "responseParameters": {},
        "responseModels": {'application/json': 'Empty'}
    }

    try:
        apigateway_client.put_method_response(**_parameters)
        _common_.info_logger(f"Created new method response for {http_method} {status_code}")
        return True
    except ClientError as err:
        _common_.info_logger(f"Failed to create method response: {err}")
    return False


def create_api_gateway(lambda_function_name: str,
                       aws_account_number: str,
                       aws_region: str,
                       api_gateway_role: str,
                       api_gateway_api_name: str = None,
                       ) -> Union[str, None]:
    """configures an api gateway to integrate with a Lambda function.

    Args:

        lambda_function_name: the name of the lambda function to be associated with the endpoint.
        aws_account_number: the aws account number.
        aws_region: the aws region where the resources are located.
        api_gateway_role: The name of the IAM role for API Gateway integration.
        api_gateway_api_name: The name of the Gateway api.

    Returns:
        api_gateway_api_id and api_gateway_root_res_id

    """

    try:
        # Initialize the API Gateway client
        apigateway_client = boto3.client('apigateway', region_name=aws_region)

        # Get the API Gateway API ID
        api_gateway_api_id = []

        if api_gateway_api_name:
            apis_response = apigateway_client.get_rest_apis()
            sleep(_WAIT_TIME_)
            api_gateway_api_id = [item.get("id") for item in apis_response.get("items") if api_gateway_api_name == item.get("name")]

        api_gateway_api_id =  api_gateway_api_id[0] if len(api_gateway_api_id) > 0 else None
        print(api_gateway_api_id)


        if api_gateway_api_id is None:
            ### create one
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"Error: api Gateway api {api_gateway_api_name} not found.",
                                  logger=None,
                                  mode="error",
                                  ignore_flag=False)

        # Get the API Gateway root resource ID
        api_gateway_root_res_id = []

        if api_gateway_api_name:
            apir_response = apigateway_client.get_resources(restApiId=api_gateway_api_id)

            sleep(_WAIT_TIME_)
            api_gateway_root_res_id = [item.get("id") for item in apir_response.get("items") if item.get("path") == '/']
            api_gateway_root_res_id = api_gateway_root_res_id[0]

        # Create API Gateway resource

        resource_id = get_api_gateway_resource_id(aws_region, api_gateway_api_id, lambda_function_name)
        print(resource_id)

        if resource_id:
            # Resource exists, delete it
            if delete_api_gateway_resource(aws_region, api_gateway_api_id, resource_id):

                # Wait before creating the new resource to ensure deletion has propagated
                sleep(_WAIT_TIME_)

        # Create the new resource
        new_resource_id = create_api_gateway_resource(aws_region,
                                                      api_gateway_api_id,
                                                      api_gateway_root_res_id,
                                                      lambda_function_name)

        print(new_resource_id)


        # print("!!@@!@!@!", new_resource_id)
        # exit(0)

        # Put method and integration for API Gateway
        api_gateway_method = get_api_gateway_method(aws_region, api_gateway_api_id, new_resource_id, "GET")
        print(api_gateway_method)

        if api_gateway_method:
            # Resource exists, delete it
            if delete_api_gateway_method(aws_region, api_gateway_api_id, new_resource_id, "GET"):

                # Wait before creating the new resource to ensure deletion has propagated
                sleep(_WAIT_TIME_)

        # Create the new resource
        api_gateway_method = create_api_gateway_method(aws_region,
                                  api_gateway_api_id,
                                  new_resource_id,
                                  "GET")
        sleep(_WAIT_TIME_)





        # apigateway_client.put_integration(
        #     restApiId=api_gateway_api_id,
        #     resourceId=resource_response.get("id"),
        #     httpMethod='GET',
        #     type='AWS_PROXY',
        #     integrationHttpMethod='POST',
        #     uri=f'arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{aws_account_number}:function:{lambda_function_name}/invocations',
        #     credentials=f'arn:aws:iam::{aws_account_number}:role/{api_gateway_role}'
        # )
        # sleep(_WAIT_TIME_)

        # Put integration response and method response

        api_gateway_integration = get_api_gateway_integration(aws_region, api_gateway_api_id, new_resource_id, "GET")
        if api_gateway_integration:
            # Resource exists, delete it
            if delete_api_gateway_integration(aws_region, api_gateway_api_id, new_resource_id, "GET"):

                # Wait before creating the new resource to ensure deletion has propagated
                sleep(_WAIT_TIME_)

        # Create the new resource
        api_integration = create_api_gateway_integration(aws_region,
                                             api_gateway_api_id,
                                             new_resource_id,
                                             "GET",
                                             aws_account_number,
                                             lambda_function_name
                                             )
        print(api_integration)
        sleep(_WAIT_TIME_)

        # If the method response exists, delete it
        method_response = get_api_gateway_method_response(aws_region,
                                                          api_gateway_api_id,
                                                          new_resource_id,
                                                         "GET",
                                                         "200")

        if method_response:
            delete_api_gateway_method_response(aws_region, api_gateway_api_id, resource_id, "GET", "200")
        api_method_response = create_api_gateway_method_response(aws_region,
                                                                 api_gateway_api_id,
                                                                 new_resource_id,
                                                                 "GET",
                                                                 "200")
        print(api_method_response)
        sleep(_WAIT_TIME_)

        # apigateway_client.put_integration_response(
        #     restApiId=api_gateway_api_id,
        #     resourceId=resource_response.get("id"),
        #     httpMethod='GET',
        #     statusCode='200'
        # )

        # apigateway_client.put_method_response(
        #     restApiId=api_gateway_api_id,
        #     resourceId=resource_response.get("id"),
        #     httpMethod='GET',
        #     statusCode='200',
        #     responseParameters={},
        #     responseModels={'application/json': 'Empty'}
        # )


        # Create deployment
        apigateway_client.create_deployment(
            restApiId=api_gateway_api_id,
            stageName='prod',
            description='Deploying new method to prod'
        )
        _common_.info_logger("API Gateway deployment created successfully.")
        sleep(_WAIT_TIME_)

    except NoCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,
                              "Error: No AWS credentials found.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except PartialCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,
                              "Error: Incomplete AWS credentials found.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except apigateway_client.exceptions.NotFoundException:
        _common_.error_logger(currentframe().f_code.co_name,
                              "Error: API Gateway resource or method not found.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except apigateway_client.exceptions.LimitExceededException:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"Error: API Gateway limit exceeded.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except apigateway_client.exceptions.TooManyRequestsException:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"Error: Too many requests to API Gateway.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except ClientError as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"ClientError: {err.response.get('Error', {}).get('Message')}",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    except Exception as e:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"Error: Too many requests to API Gateway.",
                              logger=None,
                              mode="error",
                              ignore_flag=False)







def deploy(ecr_repository_name: str,
           aws_account_number: str,
           aws_region: str,
           project_path: str,
           lambda_function_role: str):

    create_api_gateway("lambda-pg_finance_trade_test8",
                aws_account_number,
                aws_region,
                "aaa",
                "MyApi"
                )
    exit(0)


    # create_lambda_function("pg_finance_trade_test8-test11",
    #                        f"717435123117.dkr.ecr.us-east-1.amazonaws.com/pg_finance_trade_test8:latest",
    #                        aws_account_number,
    #                        aws_region,
    #                     "arn:aws:iam::717435123117:role/role-auto-deployment-lambda-26da94",
    #                        31)
    # exit(0)








    REPO_NAME = 'pg_finance_trade_test8'
    AWS_ACCOUNT_NUMBER = '717435123117'
    AWS_REGION = 'us-east-1'
    AWS_CLIENT = 'latest'

    # Initialize boto3 clients
    ecr_client = boto3.client('ecr', region_name=AWS_REGION)
    apigateway_client = boto3.client('apigateway', region_name=AWS_REGION)
    iam_client = boto3.client('iam', region_name=AWS_REGION)
    lambda_client = boto3.client('lambda', region_name=AWS_REGION)

    # check if ECR repository exists, if exists, delete it
    # Create ECR repository

    if check_ecr_repository_exists(ecr_repository_name):
        delete_ecr_repository(ecr_repository_name, aws_region=aws_region, force=True)
        sleep(_WAIT_TIME_)

    ecr_arn, ecr_image_uri = create_ecr_repository(ecr_repository_name, aws_region=aws_region)
    sleep(_WAIT_TIME_)


    # Authenticate ECR









    # def get_ecr_login_password():
    #     response = ecr_client.get_authorization_token()
    #     auth_data = response['authorizationData'][0]
    #     auth_token = auth_data['authorizationToken']
    #     decoded_token = base64.b64decode(auth_token).decode('utf-8')
    #     username, password = decoded_token.split(':')
    #     proxy_endpoint = auth_data['proxyEndpoint']
    #
    #     return username, password, proxy_endpoint

    # Get Docker login password and login
    username, password, proxy_endpoint = get_ecr_login_password()



    # print(f"Username: {username}")
    # print(f"Password: {password}")
    # print(f"Proxy Endpoint: {proxy_endpoint}")

    # set environment variables
    os.environ['DOCKER_DEFAULT_PLATFORM'] = 'linux/amd64'
    _common_.info_logger("set default docker platform to linux/amd64")

    # login to ecr
    login_cmd = f'echo {password} | docker login --username AWS --password-stdin {AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com'
    login_process = _engine_.run_command_progress(login_cmd)
    _common_.info_logger("logging into ecr successfully.")

    build_docker_image(ecr_repository_name, aws_account_number, aws_region, path=project_path)






    # # Build, tag, and push Docker image
    # print("Building Docker image...")
    # build_cmd = f'docker build -t {REPO_NAME} .'
    # build_process = _engine_.run_command_progress(build_cmd)
    # print("Docker build completed.")
    #
    # # Tag Docker image
    # print("tagging docker image...")
    # tag_cmd = f'docker tag {REPO_NAME}:latest {AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPO_NAME}:latest'
    # tag_process = _engine_.run_command_progress(tag_cmd)
    # print("tagging docker image is completed.")
    #
    # # Push
    # print("pushing docker image to ecr...")
    # push_cmd = f'docker push {AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPO_NAME}:latest'
    # push_process = _engine_.run_command_progress(push_cmd)
    # print("pushing docker image is completed.")



    # subprocess.run(f'docker tag {REPO_NAME}:latest {AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPO_NAME}:latest', shell=True, check=True)
    # subprocess.run(f'docker push {AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPO_NAME}:latest', shell=True, check=True)



    # Create IAM role for Lambda

    # lambda_function_role = f"role-auto-deployment-lambda-{_util_common.get_random_string(6)}"
    # "lambda-ex6"
    #
    # if check_role_exists(lambda_function_role):
    #     print("AAAA")
    # exit(0)
    # test_role(lambda_function_role)
    # exit(0)


    # Create Lambda function
    # response = lambda_client.create_function(
    #     FunctionName=f'lambda-{REPO_NAME}',
    #     PackageType='Image',
    #     Role=f'arn:aws:iam::{AWS_ACCOUNT_NUMBER}:role/{lambda_function_role}',
    #     Code={'ImageUri': f'{AWS_ACCOUNT_NUMBER}.dkr.ecr.{AWS_REGION}.amazonaws.com/{REPO_NAME}:latest'},
    #     Timeout=30
    # )

    # Create IAM role for Lambda
    lambda_function_role = f"role-auto-deployment-lambda-{_util_common.get_random_string(6)}"

    if check_role_exists(lambda_function_role):
        delete_role(lambda_function_role)
        sleep(_WAIT_TIME_)

    lambda_function_role_arn = create_lambda_function_role(lambda_function_role)
    sleep(_WAIT_TIME_)

    function_name = f"lambda-{ecr_repository_name}"
    print(lambda_function_role_arn)


    if check_lambda_function_exists(function_name):
        delete_lambda_function(function_name)
        sleep(_WAIT_TIME_)

    sleep(20)
    create_lambda_function(function_name,
                           f"{ecr_image_uri}:latest",
                           aws_region,
                           lambda_function_role_arn,
                           31)
    sleep(_WAIT_TIME_)
    exit(0)

    # repo_name = REPO_NAME
    # aws_account_number = AWS_ACCOUNT_NUMBER
    # aws_region = AWS_REGION
    # lambda_function_role = lambda_function_role
    # create_lambda_function(repo_name, aws_account_number, aws_region, lambda_function_role)

    print("Lambda function created successfully.")

    api_gateway('pg_finance_trade_test8', '717435123117', 'us-east-1', "aa")

    print("API Gateway created successfully.")






def test_role(aws_role_name: str, aws_region: str = 'us-east-1'):
    iam_client = boto3.client('iam', region_name=aws_region)
    ADMIN_POLICY_ARN = 'arn:aws:iam::aws:policy/AdministratorAccess'
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    def check_or_create_role(role_name, assume_role_policy_document):
        try:
            response = iam_client.get_role(RoleName=role_name)
            print(f"Role {role_name} already exists. ARN: {response['Role']['Arn']}")
            return response.get("Role", {}).get("Arn")
        except ClientError as err:
            if err.response['Error']['Code'] == 'NoSuchEntity':
                print(f"Role {role_name} does not exist. Creating role...")
                response = iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(assume_role_policy_document)
                )
                print(f"Role {role_name} created. ARN: {response['Role']['Arn']}")
                return response.get("Role", {}).get("Arn")
            else:
                # Re-raise the exception if it's not a 'NoSuchEntity' error
                raise

    def attach_policy_to_role(role_name, policy_arn):
        try:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"Attached policy {policy_arn} to role {role_name}")
        except ClientError as e:
            print(f"Error attaching policy: {e}")
            raise
    # Check or create the role
    check_or_create_role(aws_role_name, role_policy)
    attach_policy_to_role(aws_role_name, ADMIN_POLICY_ARN)

    # iam_client.create_role(
    #     RoleName='lambda-ex',
    #     AssumeRolePolicyDocument=json.dumps(role_policy)
    # )


# def create_lambda_function(repo_name, aws_account_number, aws_region, lambda_function_role):
#     lambda_client = boto3.client('lambda', region_name='us-east-1')
#     response = lambda_client.create_function(
#         FunctionName=f'lambda-{repo_name}',
#         PackageType='Image',
#         Role=f'arn:aws:iam::{aws_account_number}:role/{lambda_function_role}',
#         Code={'ImageUri': f'{aws_account_number}.dkr.ecr.{aws_region}.amazonaws.com/{repo_name}:latest'},
#         Timeout=30
#     )
#     lambda_arn = response['FunctionArn']
#     print(f"Lambda function created with ARN: {lambda_arn}")
#     return lambda_arn


# def api_gateway(repo_name, aws_account_number, aws_region, api_gateway_role):
#     apigateway_client = boto3.client('apigateway', region_name=aws_region)
#     # Get API Gateway API ID
#     apis = apigateway_client.get_rest_apis()
#     API_GATEWAY_API_ID = next(item['id'] for item in apis['items'] if 'MyApi' in item['name'])
#
#     # Get API Gateway root resource ID
#     resources = apigateway_client.get_resources(restApiId=API_GATEWAY_API_ID)
#     API_GATEWAY_ROOT_RES_ID = next(item['id'] for item in resources['items'] if item['path'] == '/')
#
#     print("!!!!", API_GATEWAY_API_ID, API_GATEWAY_ROOT_RES_ID)
#
#     try:
#
#         # Create API Gateway resource
#         resource = apigateway_client.create_resource(
#             restApiId=API_GATEWAY_API_ID,
#             parentId=API_GATEWAY_ROOT_RES_ID,
#             pathPart=repo_name
#         )
#         API_GATEWAY_RES_ID = resource['id']
#
#         # Put method and integration for API Gateway
#         apigateway_client.put_method(
#             restApiId=API_GATEWAY_API_ID,
#             resourceId=API_GATEWAY_RES_ID,
#             httpMethod='GET',
#             authorizationType='NONE',
#             apiKeyRequired=False
#         )
#
#         apigateway_client.put_integration(
#             restApiId=API_GATEWAY_API_ID,
#             resourceId=API_GATEWAY_RES_ID,
#             httpMethod='GET',
#             type='AWS_PROXY',
#             integrationHttpMethod='POST',
#             uri=f'arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{aws_account_number}:function:lambda-{repo_name}/invocations',
#             credentials=f'arn:aws:iam::{aws_account_number}:role/role-api-gateway-ex'
#         )
#
#         # Put integration response and method response
#         apigateway_client.put_integration_response(
#             restApiId=API_GATEWAY_API_ID,
#             resourceId=API_GATEWAY_RES_ID,
#             httpMethod='GET',
#             statusCode='200'
#         )
#
#         apigateway_client.put_method_response(
#             restApiId=API_GATEWAY_API_ID,
#             resourceId=API_GATEWAY_RES_ID,
#             httpMethod='GET',
#             statusCode='200',
#             responseParameters={},
#             responseModels={'application/json': 'Empty'}
#         )
#
#         # Create deployment
#         apigateway_client.create_deployment(
#             restApiId=API_GATEWAY_API_ID,
#             stageName='prod',
#             description='Deploying new method to prod'
#         )
#     except ClientError as e:
#         print(f"Error attaching policy: {e}")
#         raise


if __name__ == "__main__":
    deploy(
        "pg_finance_trade_test8",
        "717435123117",
        "us-east-1",
        None
    )


    """
        REPO_NAME = "pg_finance_trade_test8"
    AWS_ACCOUNT_NUMBER = "717435123117"
    AWS_REGION = 'us-east-1'
    AWS_CLIENT = 'latest'
    
    """
    # REPO_NAME = 'pg_finance_trade_test8'
    # AWS_ACCOUNT_NUMBER = '717435123117'
    # AWS_REGION = 'us-east-1'
    #api_gateway('pg_finance_trade_test8', '717435123117', 'us-east-1', "aa")
    # print(test_role('lambda-ex6'))
    # exit(0)

