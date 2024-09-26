from typing import List, Union, Dict
import boto3
from logging import Logger as Log
from inspect import currentframe
from _common import _common as _common_


_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


@_common_.aws_client_handle_exceptions()
def get_aws_managed_keys(kms_alias: str,
                         aws_region: str = "us-east-1",
                         logger: Log = None
                         ) -> List[str]:
    """get the list of AWS managed keys with the specified alias

    Args:
        kms_alias: kms key alias
        aws_region: aws region
        logger: logger object

    Returns:
        return the list of AWS managed keys else an empty list

    """
    # Initialize a session using AWS KMS
    kms_client = boto3.client("kms", region_name=aws_region)

    response = kms_client.list_aliases()
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    return [each_key.get("TargetKeyId") for each_key in
            response.get("Aliases") if each_key.get("AliasName") == kms_alias]
