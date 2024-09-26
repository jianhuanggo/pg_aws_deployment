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


def get_api_gateway_root_id(aws_region: str,
                            api_gateway_api_id: str):

    apigateway_client = boto3.client('apigateway', region_name=aws_region)

    # Get the API Gateway API root ID
    response = apigateway_client.get_resources(restApiId=api_gateway_api_id)

    sleep(_WAIT_TIME_)
    api_gateway_root_res_id = [item.get("id") for item in response.get("items") if item.get("path") == '/']

    return api_gateway_root_res_id[0] if len(api_gateway_root_res_id) > 0 else None

