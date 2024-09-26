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


def get_api_gateway_method_response(aws_region: str,
                                    api_gateway_api_id: str,
                                    resource_id: str,
                                    http_method: str,
                                    status_code: str) -> Union[str, None]:
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
        print(response)
        return response

    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"HTTP method response '{http_method}' does not exist for resource ID '{resource_id}'.")
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
    # except ClientError as err:
    #     if err.response.get("Error", {}).get("Code") == 'NotFoundException':
    #         _common_.info_logger(f"No existing method response found for {http_method} {status_code}")
    #         return None
    #     else:
    #         _common_.info_logger(f"Unexpected error: {err}")
    #         raise


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
    # except ClientError as err:
    #     _common_.info_logger(f"Failed to delete method response: {err}")
    # return False
    except apigateway_client.exceptions.NotFoundException:
        _common_.info_logger(f"Integration for HTTP method integration  '{http_method}' not found for resource ID '{resource_id}'.")
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
    # except ClientError as err:
    #     _common_.info_logger(f"Failed to create method response: {err}")
    # return False
    except NoCredentialsError:
        _common_.info_logger("Error: No AWS credentials found.")
    except PartialCredentialsError:
        _common_.info_logger("Error: Incomplete AWS credentials found.")
    except ClientError as err:
        _common_.info_logger(f"ClientError: {err.response.get('Error', {}).get('Message')}")
    except Exception as err:
        # error_code = err.response.get("Error", {}).get("Code")
        # if error_code == 'RepositoryNotFoundException':
        #     _common_.error_logger(currentframe().f_code.co_name,f"The repository '{ecr_repository_name}' does not exist.")
        # elif error_code == 'ImageNotFoundException':
        #     _common_.error_logger(currentframe().f_code.co_name,f"The image with tag '{image_tag}' does not exist in the repository '{ecr_repository_name}'.")
        # else:
        #     _common_.error_logger(currentframe().f_code.co_name,f"An unexpected error occurred: {err}")
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

    # If the method response exists, delete it
    method_response = get_api_gateway_method_response(aws_region,
                                                      api_gateway_api_id,
                                                      resource_id,
                                                      "GET",
                                                      "200")

    if method_response:
        delete_api_gateway_method_response(aws_region, api_gateway_api_id, resource_id, "GET", "200")

    api_method_response = create_api_gateway_method_response(aws_region,
                                                             api_gateway_api_id,
                                                             resource_id,
                                                             "GET",
                                                             "200")
    print(api_method_response)
    sleep(_WAIT_TIME_)
