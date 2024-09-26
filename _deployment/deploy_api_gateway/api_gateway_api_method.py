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


@_common_.aws_client_handle_exceptions()
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
        response = apigateway_client.get_method(**_parameters)
        print(response)
        print(f"HTTP method '{http_method}' exists for resource ID '{resource_id}'.")
        return response

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


def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:

    # obtain the API Gateway API ID
    from _deployment.deploy_api_gateway import api_gateway_api_id
    api_gateway_api_id = api_gateway_api_id.get_api_gateway_id(aws_region, api_gateway_api_name)


    # obtain the API Gateway root resource ID
    from _deployment.deploy_api_gateway import api_gateway_api_root_id
    api_gateway_root_res_id = api_gateway_api_root_id.get_api_gateway_root_id(aws_region, api_gateway_api_id)

    # obtain the resource ID
    from _deployment.deploy_api_gateway import api_gateway_api_resource
    resource_id = api_gateway_api_resource.get_api_gateway_resource_id(aws_region, api_gateway_api_id, lambda_function_name)

    api_gateway_method = get_api_gateway_method(aws_region, api_gateway_api_id, resource_id, "GET")

    if api_gateway_method:
        # Resource exists, delete it

        if delete_api_gateway_method(aws_region, api_gateway_api_id, resource_id, "GET"):
            # Wait before creating the new resource to ensure deletion has propagated
            sleep(_WAIT_TIME_)

    # Create the new resource
    create_api_gateway_method(aws_region,
                              api_gateway_api_id,
                              resource_id,
                              "GET")
    sleep(_WAIT_TIME_)
