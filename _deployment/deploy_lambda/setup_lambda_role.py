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


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:

    # Create IAM role for Lambda

    if check_role_exists(lambda_function_role):
        delete_role(lambda_function_role)
        sleep(_WAIT_TIME_)

    lambda_function_role_arn = create_lambda_function_role(lambda_function_role)
    sleep(_WAIT_TIME_)




