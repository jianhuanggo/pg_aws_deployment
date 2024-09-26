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



def get_api_gateway_id(aws_region: str,
                       api_gateway_api_name: str):

    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Get the API Gateway API ID
    api_gateway_api_id = []

    if api_gateway_api_name:
        apis_response = apigateway_client.get_rest_apis()
        sleep(_WAIT_TIME_)
        api_gateway_api_id = [item.get("id") for item in apis_response.get("items") if
                              api_gateway_api_name == item.get("name")]

    return api_gateway_api_id[0] if len(api_gateway_api_id) > 0 else None


@_common_.aws_client_handle_exceptions()
def run(ecr_repository_name: str,
        aws_region: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None) -> None:

    from _aws import _api_gateway

    api_gateway_api_id = _api_gateway.api_gateway_create_by_name(api_gateway_api_name, aws_region)[0]
    _api_gateway.api_gateway_get_root_resource(api_gateway_api_id, aws_region)





    # obtain the API Gateway API ID
    from _deployment.deploy_api_gateway import api_gateway_api_id
    api_gateway_api_id = api_gateway_api_id.get_api_gateway_id(aws_region, api_gateway_api_name)



    sleep(_WAIT_TIME_)