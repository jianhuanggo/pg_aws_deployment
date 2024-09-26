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


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:
    """this function is to create the resources needed for the deployment

    Args:
        ecr_repository_name: ecr repository name
        aws_region: aws region
        aws_account_number: aws account number
        project_path: project path
        lambda_function_name: lambda function name
        lambda_function_role: lambda function role
        api_gateway_api_name: api gateway api name

    Returns:
        bool: True if the resources are destroyed successfully, False otherwise

    """

    # check if ECR repository exists, if exists, delete it
    if check_ecr_repository_exists(ecr_repository_name):
        delete_ecr_repository(ecr_repository_name, aws_region=aws_region, force=True)
        sleep(_WAIT_TIME_)

    # Create ECR repository
    ecr_arn, ecr_image_uri = create_ecr_repository(ecr_repository_name, aws_region=aws_region)
    sleep(_WAIT_TIME_)


def destroy(ecr_repository_name: str,
            aws_region: str,
            aws_account_number: str = None,
            project_path: str = None,
            lambda_function_name: str = None,
            lambda_function_role: str = None,
            api_gateway_api_name: str = None) -> bool:
    """this function is to destroy the resources created by run

    Args:
        ecr_repository_name: ecr repository name
        aws_region: aws region
        aws_account_number: aws account number
        project_path: project path
        lambda_function_name: lambda function name
        lambda_function_role: lambda function role
        api_gateway_api_name: api gateway api name

    Returns:
        bool: True if the resources are destroyed successfully, False otherwise

    """

    # check if ECR repository exists, if exists, delete it
    if check_ecr_repository_exists(ecr_repository_name):
        delete_ecr_repository(ecr_repository_name, aws_region=aws_region, force=True)
        sleep(_WAIT_TIME_)
    return True
