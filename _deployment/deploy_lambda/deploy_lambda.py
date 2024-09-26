
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
import boto3

_WAIT_TIME_ = 4


def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


def check_lambda_function_exists(function_name: str,
                                 aws_region: str = "us-east-1") -> bool:
    """checks if a specified aws lambda function exists.

    Args:
        function_name: the name of the lambda function
        aws_region: aws region

    Returns:
        True if the function exists, False otherwise.

    """
    lambda_client = aws_client("lambda", aws_region)
    try:
        # Attempt to get the Lambda function configuration
        _parameters = {
            "FunctionName": function_name
        }
        lambda_client.get_function(**_parameters)
        _common_.info_logger(f"Lambda function '{function_name}' exists.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        _common_.error_logger(currentframe().f_code.co_name,f"Lambda function '{function_name}' does not exist.")
    except NoCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,"Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,"Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.error_logger(f"Unexpected error: {err.response.get('Error', {}).get('Message')}")
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
    lambda_client = aws_client("lambda", aws_region)
    try:
        # Attempt to delete the Lambda function
        _parameters = {
            "FunctionName": function_name
        }
        lambda_client.delete_function(**_parameters)
        _common_.info_logger(f"Lambda function '{function_name}' deleted successfully.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        _common_.error_logger(currentframe().f_code.co_name,f"Error: Lambda function '{function_name}' does not exist.")
    except NoCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,"Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name,"Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"Unexpected error: {err.response['Error']['Message']}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=None,
                              mode="error",
                              ignore_flag=False)


def get_ecr_image_uri(ecr_repository_name: str,
                      aws_region: str = "us-east-1",
                      image_tag: str = "latest"
                      ):
    """retrieve the amazon ecr image uri for a given repository and image tag.

    Args:
        ecr_repository_name: the name of the lambda function
        aws_region: aws region
        image_tag: the tag of the image (default: 'latest')

    Returns:
        the uri of the specified image

    Raises:
        Various exceptions based on AWS service issues or missing credentials

    """

    try:
        # Create a boto3 ECR client
        ecr_client = boto3.client('ecr', region_name=aws_region)

        # Describe images in the specified repository
        _parameters = {
            "repositoryName": ecr_repository_name,
            "imageIds": [
                {
                    "imageTag": image_tag
                },
            ]
        }
        response = ecr_client.describe_images(**_parameters)
        # from pprint import pprint
        # pprint(response)

        # Extract the image details
        image_details = response.get("imageDetails")[0]
        registry_id = image_details.get("registryId")
        repository_name = image_details.get("repositoryName")
        image_digest = image_details.get("imageDigest")

        # Construct the image URI
        image_uri = f"{registry_id}.dkr.ecr.{aws_region}.amazonaws.com/{repository_name}:{image_tag}"
        return image_uri

    except NoCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name, "Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.error_logger(currentframe().f_code.co_name, "Error: Incomplete AWS credentials found.")
    except ClientError as err:
        error_code = err.response.get("Error", {}).get("Code")
        if error_code == 'RepositoryNotFoundException':
            _common_.error_logger(currentframe().f_code.co_name,f"The repository '{ecr_repository_name}' does not exist.")
        elif error_code == 'ImageNotFoundException':
            _common_.error_logger(currentframe().f_code.co_name,f"The image with tag '{image_tag}' does not exist in the repository '{ecr_repository_name}'.")
        else:
            _common_.error_logger(currentframe().f_code.co_name,f"An unexpected error occurred: {err}")
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,f"An unexpected error occurred: {err}")


def get_role_arn(role_name: str, aws_region: str = "us-east-1"):
    """retrieve the amazon ecr image uri for a given repository and image tag.

    Args:
        role_name: the name of the role
        aws_region: aws region

    Returns:
        The arn of the specified role

    Raises:
        Various exceptions based on AWS service issues or missing credentials

    """
    try:
        # Create a boto3 IAM client
        iam_client = boto3.client('iam', region_name=aws_region)

        # Get the role details
        _parameters = {
            "RoleName": role_name
        }
        response = iam_client.get_role(**_parameters)

        # Extract the role ARN
        return response.get("Role", {}).get("Arn")

    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Please configure your credentials.")
    except PartialCredentialsError:
        raise RuntimeError("Incomplete AWS credentials found. Please check your credentials.")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchEntity':
            raise RuntimeError(f"The role '{role_name}' does not exist.")
        else:
            raise RuntimeError(f"An unexpected error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


def create_lambda_function(function_name: str,
                           image_uri: str,
                           aws_region: str,
                           lambda_function_role_arn: str,
                           timeout: int = 30,
                           logger: Log = None) -> Union[str, None]:

    """Creates an aws lambda function using an image stored in an ECR repository.

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


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role_name: str = None,
        api_gateway_api_name: str = None) -> None:

    ecr_image_uri = get_ecr_image_uri(ecr_repository_name, aws_region)
    print(ecr_image_uri)

    role_arn = get_role_arn(lambda_function_role_name)
    print(role_arn)

    if check_lambda_function_exists(lambda_function_name):
        delete_lambda_function(lambda_function_name)
        sleep(_WAIT_TIME_)

    sleep(15)
    create_lambda_function(lambda_function_name,
                           ecr_image_uri,
                           aws_region,
                           role_arn,
                           31)
    sleep(_WAIT_TIME_)
