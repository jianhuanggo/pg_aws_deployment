from typing import List, Union, Dict
import boto3
from logging import Logger as Log
from inspect import currentframe

from jinja2.nodes import Tuple

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


@_common_.aws_client_handle_exceptions()
def create_kms_keys(aws_region: str = "us-east-1",
                    logger: Log = None
                    ) -> tuple[any, any]:
    """create kms id

    Args:
        aws_region: aws region
        logger: logger object

    Returns:
        return the list of AWS managed keys else an empty list

    """
    # Initialize a session using AWS KMS
    kms_client = boto3.client("kms", region_name=aws_region)

    _parameters = {
        "Description": "ec2 kms key for encrypting data",
        "KeyUsage": "ENCRYPT_DECRYPT",
        "CustomerMasterKeySpec": "SYMMETRIC_DEFAULT"
    }
    response = kms_client.create_key(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"created kms key: {response.get('KeyMetadata', {}).get('KeyId')}", logger=logger)
    return response.get("KeyMetadata", {}).get("KeyId"), response.get("KeyMetadata", {}).get("Arn")


@_common_.aws_client_handle_exceptions()
def create_kms_key_alias(alias_name: str,
                         key_id: str,
                         aws_region: str = "us-east-1",
                         logger: Log = None
                         ) -> bool:
    """create kms alias

    Args:
        alias_name: alias name
        key_id: key id
        aws_region: aws region
        logger: logger object

    Returns:
        return the list of AWS managed keys else an empty list

    """
    # Initialize a session using AWS KMS
    kms_client = boto3.client("kms", region_name=aws_region)

    _parameters = {
        "AliasName": "alias/" + alias_name,
        "TargetKeyId": key_id
    }

    response = kms_client.create_alias(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"created kms key alias {alias_name} for key_id {key_id}", logger=logger)
    return True


@_common_.aws_client_handle_exceptions()
def check_alias_exists(alias_name: str,
                       aws_region="us-east-1",
                       logger: Log = None
                       ) -> bool:
    """check whether the alias exists

    Args:
        alias_name: alias name
        key_id: key id
        aws_region: aws region
        logger: logger object

    Returns:
        return true if the alias exists else false

    """
    # Initialize the KMS client
    kms_client = boto3.client("kms", region_name=aws_region)

    # List all aliases and check for the specified alias
    paginator = kms_client.get_paginator('list_aliases')
    for page in paginator.paginate():
        for alias in page['Aliases']:
            if alias.get("AliasName") == alias_name:
                return True  # Alias exists
    return False  # Alias does not exist


@_common_.aws_client_handle_exceptions()
def get_key_alias_arn(alias_name: str,
                      aws_region="us-east-1",
                      logger: Log = None
                      ) -> Union[str, None]:
    """get key alias arn

    Args:
        alias_name: alias name
        aws_region: aws region
        logger: logger object

    Returns:
        return arn of key alias if the alias exists else None

    """
    # Initialize the KMS client
    kms_client = boto3.client("kms", region_name=aws_region)
    print(alias_name)

    # List all aliases and check for the specified alias
    paginator = kms_client.get_paginator('list_aliases')
    for page in paginator.paginate():
        for alias in page['Aliases']:
            if alias.get("AliasName") == alias_name:
                return alias.get("AliasArn")  # Alias exists
    return None  # Alias does not exist