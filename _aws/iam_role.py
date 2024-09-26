from typing import List, Union
import os
import boto3
from logging import Logger as Log
from inspect import currentframe
import subprocess
import json
from _common import _common as _common_
import boto3

_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


# @_common_.aws_client_handle_exceptions(aws_client=aws_client(service_name="iam", aws_region="us-east-1"))
@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client(service_name="iam", aws_region="us-east-1").exceptions.NoSuchEntityException)
def check_role_exists(iam_role_name: str,
                      aws_region: str = "us-east-1",
                      logger: Log = None) -> bool:

    """Checks if a specified IAM role exists.

    Args:
        iam_role_name: The name of the IAM role to check.
        aws_region: aws region
        logger: log object

    Returns:
        True if the role exists, False otherwise.

    """
    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)
    _parameters = {
        "RoleName": iam_role_name
    }
    response = iam_client.get_role(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"Role '{iam_role_name}' exists.")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client(service_name="iam", aws_region="us-east-1").exceptions.NoSuchEntityException)
def delete_role(iam_role_name: str,
                aws_region: str = "us-east-1",
                logger: Log = None
                ) -> bool:

    """ Deletes a specified IAM role.

    Args:
        aws_role_name: The name of the IAM role to delete.
        aws_region: aws region
        logger: log object

    Returns:
        True if the role was deleted successfully, False
    """
    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    _parameters = {
        "RoleName": iam_role_name
    }
    response = iam_client.delete_role(RoleName=iam_role_name)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Role '{iam_role_name}' deleted successfully.")
    return True


@_common_.aws_client_handle_exceptions()
def create_iam_role(service_name: str,
                    role_name: str,
                    aws_region: str = "us-east-1",
                    logger: Log = None
                    ) -> str:
    """create an iam role for access to ecr

    Args:

        aws_region: aws region
        service_name: service name
        role_name: role name
        logger: log object

    Returns:
        return the arn of the created role

    """

    # initialize the boto3 iam client
    iam_client = boto3.client("iam", region_name=aws_region)

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": f"{service_name}.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    _parameters = {
        "RoleName": role_name,
        "AssumeRolePolicyDocument": json.dumps(assume_role_policy_document),
        "Description": "Role that allows EC2 instances to access ECR"
    }

    response = iam_client.create_role(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"created iam role: {role_name}")
    return response.get("Role", {}).get("Arn")


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client(service_name="iam", aws_region="us-east-1").exceptions.NoSuchEntityException)
def attach_policy_to_role(iam_role_name: str,
                          policy_arn: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> bool:
    """attach a policy to a role

    Args:
        iam_role_name: role name
        policy_arn: iam policy arn
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """
    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    _parameters = {
        "RoleName": iam_role_name,
        "PolicyArn": policy_arn
    }
    response = iam_client.attach_role_policy(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Attached policy {policy_arn} to role {iam_role_name}")
    return True


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client(service_name="iam", aws_region="us-east-1").exceptions.NoSuchEntityException)
def list_attached_role_policies(role_name: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None) -> Union[List[dict], None]:
    """list all policies attaching to a role

    Args:
        role_name: role name
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """
    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    _parameters = {
        "RoleName": role_name
    }

    # List all policies attached to the role
    response = iam_client.list_attached_role_policies(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # ['AttachedPolicies']
    # Detach each policy
    return response.get("AttachedPolicies", [])


@_common_.aws_client_handle_exceptions(aws_client_exception=aws_client(service_name="iam", aws_region="us-east-1").exceptions.NoSuchEntityException)
def detach_policy_from_role(role_name: str,
                            policy_arn: str,
                            aws_region: str = "us-east-1",
                            logger: Log = None) -> bool:

    """detach a policy to a role

    Args:
        role_name: role name
        policy_arn: iam policy arn
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """

    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    # Detach the policy from the role
    _parameters = {
        "RoleName": role_name,
        "PolicyArn": policy_arn
    }
    response = iam_client.detach_role_policy(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Policy {policy_arn} successfully detached from role {role_name}")
    return True


@_common_.aws_client_handle_exceptions()
def detach_all_policies_from_role(iam_role_name: str,
                                  aws_region: str = "us-east-1",
                                  logger: Log = None) -> bool:
    """detach all policies from a role

    Args:
        iam_role_name: role name
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """

    # Detach each policy
    for policy in list_attached_role_policies(iam_role_name):
        _parameters = {
            "role_name": iam_role_name,
            "policy_arn": policy.get("PolicyArn")
        }
        detach_policy_from_role(**_parameters)
        _common_.info_logger(f"Policy {policy.get('PolicyArn')} successfully detached from role {iam_role_name}")
    return True


@_common_.aws_client_handle_exceptions()
def create_instance_profile(instance_profile_name: str,
                            aws_region: str = "us-east-1",
                            logger: Log = None) -> bool:
    """create an instance profile based on the specified name

    Args:
        instance_profile_name: instance profile name
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """
    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    response = iam_client.create_instance_profile(InstanceProfileName=instance_profile_name)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Instance profile {instance_profile_name} create successfully.")
    return True


@_common_.aws_client_handle_exceptions()
def add_role_to_instance_profile(instance_profile_name: str,
                                 iam_role_name: str,
                                 aws_region: str = "us-east-1",
                                 logger: Log = None
                                 ) -> bool:
    """add role to the instance profile

    Args:
        instance_profile_name: instance profile name
        iam_role_name: iam role name
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """

    # initialize the boto3 iam client
    iam_client = boto3.client('iam', region_name=aws_region)

    # Replace with your instance profile name and IAM role name
    _parameters = {
        "InstanceProfileName": instance_profile_name,
        "RoleName": iam_role_name
    }

    # Attach the role to the instance profile
    response = iam_client.add_role_to_instance_profile(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Role {iam_role_name} attached to instance profile {instance_profile_name}")
    return True


@_common_.aws_client_handle_exceptions("NoSuchEntity")
def detach_role_from_instance_profile(instance_profile_name: str,
                                      iam_role_name: str,
                                      aws_region: str = "us-east-1",
                                      logger: Log = None) -> bool:
    """detach role from an instance profile

    Args:
        instance_profile_name: instance profile name
        iam_role_name: iam role name
        aws_region: aws region
        logger: log object

    Returns:
        return True if successful otherwise False

    """

    # initialize the boto3 iam client
    iam_client = boto3.client('iam', region_name=aws_region)

    _parameter = {
        "InstanceProfileName": instance_profile_name,
        "RoleName": iam_role_name
    }
    response = iam_client.remove_role_from_instance_profile(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Role {iam_role_name} detached from instance profile {instance_profile_name}")
    return True


@_common_.aws_client_handle_exceptions("NoSuchEntity")
def delete_instance_profile(instance_profile_name: str,
                            aws_region: str = "us-east-1",
                            logger: Log = None) -> bool:
    """delete an instance profile

    Args:
        instance_profile_name: instance profile name
        aws_region: aws region
        logger: logger object

    Returns:
        returns true if the instance profile is deleted successfully otherwise false

    """

    iam_client = aws_client("iam", aws_region)

    response = iam_client.delete_instance_profile(InstanceProfileName=instance_profile_name)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Instance profile {instance_profile_name} deleted successfully.")
    return True


@_common_.aws_client_handle_exceptions("NoSuchEntity")
def get_instance_profile(instance_profile_name: str,
                         aws_region: str = "us-east-1",
                         logger: Log = None) -> List[str]:
    """get role names associated with the specified instance profile

    Args:
        instance_profile_name: instance profile name
        aws_region: aws region
        logger: logger object

    Returns:
        returns a list of role names associated with the instance profile

    """

    # initialize the boto3 iam client
    iam_client = aws_client("iam", aws_region)

    # Replace with your instance profile name
    instance_profile_name = 'your-instance-profile-name'
    _parameters = {
        "InstanceProfileName": instance_profile_name
    }

    # Get the instance profile
    response = iam_client.get_instance_profile(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Print out the associated roles
    return [each_role.get("RoleName") for each_role in response.get("InstanceProfile", {}).get("Roles", [])]
