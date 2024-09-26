import boto3
from logging import Logger as Log
from typing import Union, List
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
    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    try:
        # Get the list of resources
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
    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    try:

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
        aws_region: aws region
        api_gateway_api_id: the id of the api gateway api.
        api_gateway_root_res_id: the id of the root resource in the api gateway.
        lambda_function_name: the name of the lambda function (used as the resource path)

    Returns:
        the id of the newly created resource.

    """
    apigateway_client = boto3.client('apigateway', region_name=aws_region)
    try:
        # Create the new resource
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


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:

    # obtain the api gateway api id
    from _deployment.deploy_api_gateway import api_gateway_api_id
    api_gateway_api_id = api_gateway_api_id.get_api_gateway_id(aws_region, api_gateway_api_name)

    # obtain the api gateway root resource id
    from _deployment.deploy_api_gateway import api_gateway_api_root_id
    api_gateway_root_res_id = api_gateway_api_root_id.get_api_gateway_root_id(aws_region, api_gateway_api_id)

    # obtain the api gateway resource id
    resource_id = get_api_gateway_resource_id(aws_region, api_gateway_api_id, lambda_function_name)
    print(resource_id, api_gateway_api_id, api_gateway_root_res_id)

    if resource_id:
        # Resource exists, delete it
        if delete_api_gateway_resource(aws_region, api_gateway_api_id, resource_id):
            # Wait before creating the new resource to ensure deletion has propagated
            sleep(_WAIT_TIME_)

    # Create the new resource
    create_api_gateway_resource(aws_region,
                                api_gateway_api_id,
                                api_gateway_root_res_id,
                                lambda_function_name)

