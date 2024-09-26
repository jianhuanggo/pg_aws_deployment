from typing import List, Union, Dict
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


@_common_.aws_handle_exceptions
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


# @_common_.aws_handle_exceptions
# def create_iam_role(aws_region: str,
#                     role_name: str,
#                     logger: Log = None
#                     ) -> str:
#     """create an iam role for access to ecr
#
#     Args:
#
#         aws_region: aws region
#         role_name: role name
#         logger: log object
#
#     Returns:
#         return the arn of the created role
#
#     """
#
#     # Initialize a session using Amazon EC2
#     ec2_client = boto3.client('ec2', region_name=aws_region)
#
#     assume_role_policy_document = {
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Effect": "Allow",
#                 "Principal": {
#                     "Service": "ec2.amazonaws.com"
#                 },
#                 "Action": "sts:AssumeRole"
#             }
#         ]
#     }
#     _parameters = {
#         "RoleName": role_name,
#         "AssumeRolePolicyDocument": json.dumps(assume_role_policy_document),
#         "Description": "Role that allows EC2 instances to access ECR"
#     }
#
#     response = ec2_client.create_role(**_parameters)
#
#     if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
#         _common_.error_logger(currentframe().f_code.co_name,
#                               f"operation failed, reason response code is not 200",
#                               logger=logger,
#                               mode="error",
#                               ignore_flag=False)
#
#     _common_.info_logger(f"created iam role: {role_name}")
#     return response.get("Role", {}).get("Arn")

@_common_.aws_client_handle_exceptions()
def run(project_name: str,
        aws_region: str = "us-east-1",
        logger: Log = None
        ) -> Dict:

    from _aws import iam_role
    iam_role_name = f"iam-role-{project_name}"
    instance_profile_name = f"inst_{project_name}"

    if iam_role.check_role_exists(iam_role_name=iam_role_name):
        if role_names := iam_role.get_instance_profile(instance_profile_name=instance_profile_name):
            for role_name in role_names:
                iam_role.detach_role_from_instance_profile(iam_role_name=role_name,
                                                           instance_profile_name=instance_profile_name)
        if iam_role.detach_role_from_instance_profile(iam_role_name=iam_role_name,
                                                      instance_profile_name=instance_profile_name):
            iam_role.delete_instance_profile(instance_profile_name=instance_profile_name)
        if iam_role.detach_all_policies_from_role(iam_role_name=iam_role_name):
            iam_role.delete_role(iam_role_name=iam_role_name)

        else:
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"unable to detach all policies from iam role {iam_role_name}",
                                  logger=None,
                                  mode="error",
                                  ignore_flag=False)

    # create iam role
    response = iam_role.create_iam_role("ec2", iam_role_name)
    if not response:
        _common_.error_logger(currentframe().f_code.co_name,
                              "unable to create iam role",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    # attach policy to iam role
    policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
    response = iam_role.attach_policy_to_role(iam_role_name=iam_role_name,
                                              policy_arn=policy_arn)
    if not response:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"unable to attach policy to iam role {iam_role_name}",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    # create instance profile
    response = iam_role.create_instance_profile(instance_profile_name=instance_profile_name)
    if not response:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"unable to create instance role {instance_profile_name}",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    # attach iam role to instance profile
    response = iam_role.add_role_to_instance_profile(instance_profile_name=instance_profile_name,
                                                     iam_role_name=iam_role_name)
    if not response:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"unable to attach iam role {iam_role_name} to iam instance profile {instance_profile_name}",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    return {"iam_role_name": iam_role_name, "instance_profile_name": instance_profile_name}


@_common_.aws_client_handle_exceptions()
def destroy(project_name: str,
            aws_region: str = "us-east-1",
            logger: Log = None
            ) -> bool:

    from _aws import iam_role

    iam_role_name = f"iam-role-{project_name}"
    instance_profile_name = f"inst_{project_name}"

    if iam_role.check_role_exists(iam_role_name=iam_role_name):
        if role_names := iam_role.get_instance_profile(instance_profile_name=instance_profile_name):
            for role_name in role_names:
                iam_role.detach_role_from_instance_profile(iam_role_name=role_name,
                                                           instance_profile_name=instance_profile_name)
        if iam_role.detach_role_from_instance_profile(iam_role_name=iam_role_name,
                                                      instance_profile_name=instance_profile_name):
            iam_role.delete_instance_profile(instance_profile_name=instance_profile_name)
        if iam_role.detach_all_policies_from_role(iam_role_name=iam_role_name):
            iam_role.delete_role(iam_role_name=iam_role_name)

        else:
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"unable to detach all policies from iam role {iam_role_name}",
                                  logger=None,
                                  mode="error",
                                  ignore_flag=False)

    return True
