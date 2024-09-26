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


def create_api_gateway_deployment(aws_region: str,
                                  api_gateway_api_id: str
                                  ) -> bool:

    """creates an api gateway deployment.

    """
    try:
        apigateway_client = boto3.client('apigateway', region_name=aws_region)
        _parameters = {
            "restApiId": api_gateway_api_id,
            "stageName": "prod",
            "description": "Deploying new method to prod"
        }
        apigateway_client.create_deployment(**_parameters)
        sleep(_WAIT_TIME_)
        _common_.info_logger(f"api gateway deployment created successfully for {api_gateway_api_id}")
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

    # obtain the api gateway api id
    from _deployment.deploy_api_gateway import api_gateway_api_id
    api_gateway_api_id = api_gateway_api_id.get_api_gateway_id(aws_region, api_gateway_api_name)

    # obtain the api gateway root resource id
    from _deployment.deploy_api_gateway import api_gateway_api_root_id
    api_gateway_root_res_id = api_gateway_api_root_id.get_api_gateway_root_id(aws_region, api_gateway_api_id)

    # obtain the api gateway resource id
    from _deployment.deploy_api_gateway import api_gateway_api_resource
    resource_id = api_gateway_api_resource.get_api_gateway_resource_id(aws_region, api_gateway_api_id, lambda_function_name)
    print(resource_id, api_gateway_api_id, api_gateway_root_res_id)

    # Create new deployment
    print(create_api_gateway_deployment(aws_region, api_gateway_api_id))