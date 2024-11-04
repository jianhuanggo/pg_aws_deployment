from typing import List, Union
from logging import Logger as Log
from inspect import currentframe
from _common import _common as _common_


_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def run(vpc_id: str,
        sg_name: str,
        aws_region: str,
        project_name: str,
        sg_ingress_rules: List = [],
        logger: Log = None
        ) -> Union[str, None]:
    """this function checks whether the security group exists, recreate it if it exists

    Args:

        vpc_id: vpc id
        sg_name: security group name
        aws_region: aws region
        project_name: project name
        sg_ingress_rules: security group ingress rules
        logger: log object

    Returns:
        return security group id if successful else None

    """
    from _aws import ec2

    _parameters = {
        "aws_region": aws_region,
        "sg_name": sg_name,
        "vpc_id": vpc_id
    }
    if sg_id := ec2.get_security_group_id(**_parameters):
        _parameters = {
            "aws_region": aws_region,
            "sg_id": sg_id,
        }
        ec2.delete_security_group(**_parameters)
    _parameters = {
        "aws_region": aws_region,
        "sg_name": sg_name,
        "vpc_id": vpc_id
    }
    sg_id = ec2.create_security_group(**_parameters)
    if not sg_id:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"Not able to create security group {sg_name}",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    # Define ingress rules
    default_ingress_rules = [
        {
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow SSH from anywhere
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow HTTP from anywhere
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': 443,
            'ToPort': 443,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow HTTPS from anywhere
        }
    ]

    sg_ingress_rules = sg_ingress_rules if sg_ingress_rules else default_ingress_rules

    _parameters = {
        "aws_region": aws_region,
        "sg_id": sg_id,
        "sg_ingress_rules": sg_ingress_rules
    }

    if not ec2.create_sg_ingress_rules(**_parameters):
        _common_.error_logger(currentframe().f_code.co_name,
                              f"Not able to create security group ingress rules for {project_name}-security-group",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return sg_id


@_common_.aws_client_handle_exceptions()
def destroy(vpc_id: str,
            sg_name: str,
            aws_region: str,
            project_name: str,
            sg_ingress_rules: List = [],
            logger: Log = None
            ) -> bool:
    """this function destroys the security group

    Args:

        vpc_id: vpc id
        sg_name: security group name
        aws_region: aws region
        project_name: project name
        sg_ingress_rules: security group ingress rules
        logger: log object

    Returns:
        return security group id if successful else None

    """
    from _aws import ec2

    _parameters = {
        "aws_region": aws_region,
        "sg_name": sg_name,
        "vpc_id": vpc_id
    }
    if sg_id := ec2.get_security_group_id(**_parameters):
        _parameters = {
            "aws_region": aws_region,
            "sg_id": sg_id,
        }
        ec2.delete_security_group(**_parameters)

    return True
