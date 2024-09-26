import boto3
from typing import List, Union, Dict, Optional
from logging import Logger as Log
from inspect import currentframe
from time import sleep
from datetime import datetime
from _common import _common as _common_


__WAIT_TIME__ = 10


@_common_.aws_client_handle_exceptions()
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


@_common_.aws_client_handle_exceptions()
def describe_ec2_get_spot_request(instance_id: str,
                                  aws_region: str = "us-east-1",
                                  logger: Log = None) -> Optional[List[Dict]]:
    """check if the specified instance is a spot instance

    Args:
        instance_id: instance id
        aws_region: aws region
        logger: logger object

    Returns:
        return list of dictionary containing instance_id,
        spot_request_id and status if successful, empty list otherwise empty list

    """
    # Initialize a session using Amazon EC2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Replace 'your-instance-id' with the actual instance ID you want to check

    # Describe the instance to get detailed information
    response = ec2_client.describe_instances(InstanceIds=[instance_id])

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Extract instance information
    instance = response['Reservations'][0]['Instances'][0]

    # Check if the instance is a spot instance
    if 'InstanceLifecycle' in instance and instance['InstanceLifecycle'] == 'spot':
        if "SpotInstanceRequestId" in instance:
            spot_request_id = instance['SpotInstanceRequestId']

            if not is_spot_request_exist(spot_request_id, aws_region):
                return []

            _common_.info_logger(f"Spot Instance Request ID {spot_request_id} is associated with instance {instance_id}")
            return [{"instance_id": instance_id, "spot_request_id": spot_request_id}]

    else:
        _common_.info_logger(f"Instance {instance_id} is not a spot instance.")
    return []


@_common_.aws_client_handle_exceptions("InvalidSpotInstanceRequestID.Malformed")
def is_spot_request_exist(spot_request_id: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None) -> bool:

    """check if the specified instance is a spot instance

    Args:
        spot_request_id: spot request id
        aws_region: aws region
        logger: logger object

    Returns:
        return the status for spot request if successful, None otherwise

    """

    # Initialize a session using Amazon EC2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the spot instance request to get details
    _parameter = {
        "SpotInstanceRequestIds": [spot_request_id]
    }

    response = ec2_client.describe_spot_instance_requests(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Extract spot instance request information
    return response['SpotInstanceRequests'][0].get("Status", {}).get("Code") == "fulfilled"


@_common_.aws_client_handle_exceptions("InvalidSpotInstanceRequestID.Malformed")
def get_spot_request_associated_instance(spot_request_id: str,
                                         aws_region: str = "us-east-1",
                                         logger: Log = None) -> Union[List[str], None]:

    """get the instance associated with the spot request

    Args:
        spot_request_id: spot request id
        aws_region: aws region
        logger: logger object

    Returns:
        return the status for spot request if successful, None otherwise

    """

    # Initialize a session using Amazon EC2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the spot instance request to get details
    _parameter = {
        "SpotInstanceRequestIds": [spot_request_id]
    }

    response = ec2_client.describe_spot_instance_requests(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Extract spot instance request information
    instance_ids = [each_instance.get("InstanceId") for each_instance in response.get("SpotInstanceRequests", [])]
    return instance_ids if instance_ids else []


@_common_.aws_client_handle_exceptions()
def terminate_spot_request_and_instances(spot_request_id: str,
                                         aws_region: str = "us-east-1",
                                         logger: Log = None) -> bool:
    """delete the specified spot request and associated instances

    Args:
        spot_request_id: spot request id
        aws_region: aws region
        logger: logger object

    Returns:
        return True if successful False otherwise

    """
    # Initialize a session using Amazon EC2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the spot instance request to get details

    if not is_spot_request_exist(spot_request_id, aws_region):
        _common_.info_logger(f"No EC2 instance associated with Spot Request ID {spot_request_id}.")
        return False


    for instance_id in get_spot_request_associated_instance(spot_request_id, aws_region):
    #
    # response = ec2_client.describe_spot_instance_requests(SpotInstanceRequestIds=[spot_request_id])
    #
    # # Extract spot instance request information
    # spot_request = response['SpotInstanceRequests'][0]
    #
    # # Check if an instance is associated with the spot request
    # if 'InstanceId' in spot_request:
    #     instance_id = spot_request['InstanceId']

        # Terminate the associated EC2 instance
        _common_.info_logger(f"Terminating Instance ID {instance_id} associated with Spot Request ID {spot_request_id}")
        terminate_instance_and_wait(instance_id)


    # Cancel the spot instance request
    _parameter = {
        "SpotInstanceRequestIds": [spot_request_id]
    }
    response = ec2_client.cancel_spot_instance_requests(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Spot Request ID {spot_request_id} has been canceled.")


@_common_.aws_client_handle_exceptions("InvalidInstanceID.Malformed")
def terminate_instance_and_wait(instance_id: str,
                                aws_region: str = "us-east-1",
                                logger: Log = None) -> bool:

    """terminate the specified spot request and associated instances

    Args:
        instance_id: instance id
        aws_region: aws region
        logger: logger object

    Returns:
        return True if instance was terminated successfully otherwise False

    """
    # Initialize a session using Amazon EC2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Terminate the EC2 instance
    _common_.info_logger(f"Terminating instance {instance_id}...")
    ec2_client.terminate_instances(InstanceIds=[instance_id])

    # Wait for the instance to be fully terminated
    _common_.info_logger(f"Waiting for instance {instance_id} to be fully terminated...")
    waiter = ec2_client.get_waiter('instance_terminated')
    waiter.wait(InstanceIds=[instance_id])
    _common_.info_logger(f"Instance {instance_id} has been successfully terminated.")
    sleep(__WAIT_TIME__)
    return True

    # from _deployment.deploy_ec2 import ec2_network
    #
    # _parameters = {
    #     "aws_region": aws_region
    # }
    # network_info = ec2_network.define_network(**_parameters)
    #
    # if not network_info:
    #     _common_.error_logger(currentframe().f_code.co_name,
    #                           "No public subnet found",
    #                           logger=None,
    #                           mode="error",
    #                           ignore_flag=False)
    # sg_name = f"{project_name}-security-group"
    # vpc_id = network_info.get("vpc_id")
    # if not vpc_id:
    #     _common_.error_logger(currentframe().f_code.co_name,
    #                           "No vpc found to place the resource",
    #                           logger=None,
    #                           mode="error",
    #                           ignore_flag=False)
    #
    # _parameters = {
    #     "aws_region": aws_region,
    #     "sg_name": sg_name,
    #     "vpc_id": vpc_id
    # }
    # if sg_id := ec2_network.get_security_group_id(**_parameters):
    #     _parameters = {
    #         "aws_region": aws_region,
    #         "sg_id": sg_id,
    #     }
    #     ec2_network.delete_security_group(**_parameters)





