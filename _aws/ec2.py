from typing import List, Union, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from time import sleep
from logging import Logger as Log
from inspect import currentframe
from _common import _common as _common_
from _util import _util_common as _util_common_



__WAIT_TIME__ = 10


def find_image(aws_region: str,
               kernel_arch: str = "x86_64",
               logger: Log = None
               ) -> Union[str, None]:

    """obtain aws linux 2 image id in the specified region

    Args:
        aws_region: aws region
        kernel_arch: kernel architecture, x86_64 for x86_64 architecture (default) or arm64 for ARM64 architecture
        logger: logger

    Returns:
        return image id if successful, None otherwise

    """

    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe images with the specified filters
    # 'amzn2-ami-hvm-*-arm64-gp2' for ARM64 architecture
    response = ec2_client.describe_images(
        Owners=['amazon'],
        Filters=[
            {'Name': 'name', 'Values': [f"amzn2-ami-hvm-*-{kernel_arch}-gp2"]},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    image = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
    if len(image) > 0:
        return image[0].get("ImageId")
    else:
        return None


@_common_.aws_client_handle_exceptions()
def find_instances_by_tag(tag_key: str,
                          tag_value: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None) -> List[str]:
    """finds and returns a list of EC2 instance IDs that have a specific tag key and value.

    Args:
        tag_key: The key of the tag to filter by (e.g., 'pg_auto_project_name').
        tag_value: The value of the tag
        aws_region: aws region
        logger: logger

    Returns:
        return a list of ec2 instance ids that match the given tag key and value.

    """

    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe instances with the specific tag key and value
    _parameters = {
        "Filters": [
            {
                "Name": f"tag:{tag_key}",
                "Values": [tag_value]
            },
            {
                "Name": "instance-state-name",
                "Values": ["running"]
            }
            ]
    }
    _response = ec2_client.describe_instances(**_parameters)

    if _response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"not able to retrieve object",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Extract instance IDs from the response
    instances = []
    for reservation in _response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instances.append(instance.get("InstanceId"))

    if instances:
        _common_.info_logger(f"Found instances with tag {tag_key}={tag_value}: {instances}")
    else:
        _common_.info_logger(f"No instances found with tag {tag_key}={tag_value}.")
    return instances


def find_instance_by_id(instance_id: str,
                        aws_region: str = "us-east-1",
                        logger: Log = None) -> List[Dict]:

    """finds and returns a list of EC2 instance IDs using instance id

    Args:
        instance_id: ec2 instance id
        aws_region: aws region
        logger: logger

    Returns:
        return a list of ec2 instance ids that match the given tag key and value.

    """

    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the instance by instance ID
    response = ec2_client.describe_instances(InstanceIds=[instance_id])

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"not able to retrieve object",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    # Extract instance information
    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instances.append(instance)

    if instances:
        _common_.info_logger(f"Found instances using instance id {instance_id}: {instances}")
    else:
        _common_.info_logger(f"Instances not found using instance id {instance_id}")

    return instances


@_common_.aws_client_handle_exceptions()
def run_ec2_from_template(launch_template_id: str,
                          version: str = "$Latest",
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> List[str]:
    """launch an ec2 instance from the specified launch template

    Args:
        launch_template_id: launch template id
        aws_region: aws region
        version: version, default to latest
        logger: logger

    Returns:
        True if the instance is launched successfully, False otherwise

    """
    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)
    _parameters = {
        "LaunchTemplate": {
            "LaunchTemplateId": launch_template_id,
            "Version": version
        },
        # # "SubnetId": subnet_id,
        # "NetworkInterfaces": [
        #     {
        #         "AssociatePublicIpAddress": False,
        #         "SubnetId": subnet_id,
        #         "Groups": ["sg-0cea0bd861446063b"],
        #         "DeviceIndex": 0,
        #     }],
        "MinCount": 1,
        "MaxCount": 1
    }

    _response = ec2_client.run_instances(**_parameters)
    if _response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"not able to retrieve object",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    else:
        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Waiting for instance {instance_id} to reach the 'running' state...")

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])

            # Wait for the instance to pass both system and instance status checks
        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Waiting for instance {instance_id} to pass all status checks...")

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            status_waiter = ec2_client.get_waiter('instance_status_ok')
            status_waiter.wait(InstanceIds=[instance_id])

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Instance {instance_id} has passed all status checks and is fully operational.")

        return [each_instance.get("InstanceId") for each_instance in _response.get("Instances", [])]


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
    # initialize the boto3 client for ec2
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

    # initialize the boto3 client for ec2
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
    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the spot instance request to get details
    if not is_spot_request_exist(spot_request_id, aws_region):
        _common_.info_logger(f"No EC2 instance associated with Spot Request ID {spot_request_id}.")
        return False

    # Terminate the associated EC2 instance
    for instance_id in get_spot_request_associated_instance(spot_request_id, aws_region):
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
    # initialize the boto3 client for ec2
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


@_common_.aws_client_handle_exceptions("InvalidKeyPair.NotFound")
def describe_key_pair(key_pair_name: str,
                      aws_region: str = "us-east-1",
                      logger: Log = None
                      ) -> bool:

    """check if the specified key pair exists

    Args:
        key_pair_name: The name of the key pair
        aws_region: aws region
        logger: log object

    Returns:
        true if the key pair exists, false otherwise.

    """
    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe key pairs with the specified name
    _parameters = {
        "KeyNames": [key_pair_name]
    }
    response = ec2_client.describe_key_pairs(KeyNames=[key_pair_name])
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Key pair '{key_pair_name}' exists")
    return True if response.get("KeyPairs") else False


@_common_.aws_client_handle_exceptions("InvalidKeyPair.NotFound")
def delete_key_pair(key_pair_name: str,
                    aws_region: str,
                    logger: Log = None
                    ) -> Union[bool, None]:
    """delete the specified key pair if it exists

    Args:
        key_pair_name: The name of the key pair
        aws_region: aws region
        logger: log object

    Returns:
        true if the key pair exists, false otherwise.

    """
    # initialize the boto3 client for ec2
    ec2_client = boto3.client('ec2', region_name=aws_region)

    response = ec2_client.delete_key_pair(KeyName=key_pair_name)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"Key pair '{key_pair_name}' deleted.")
    return response.get("KeyPairId")


@_common_.aws_client_handle_exceptions()
def create_key_pair(aws_region: str,
                    key_name: str,
                    file_path: str,
                    logger: Log = None
                    ):

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Create a key pair
    response = ec2_client.create_key_pair(KeyName=key_name)

    # Save the private key to a file
    with open(file_path, 'w') as file:
        file.write(response['KeyMaterial'])

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Key pair created and private key {key_name}.pem saved to {file_path}")
    return response


@_common_.aws_client_handle_exceptions()
def is_public_subnet(subnet_id: str,
                     aws_region: str = "us-east-1",
                     logger: Log = None
                     ) -> bool:
    """check if the specified subnet is a public subnet

    Args:
        aws_region: aws region
        subnet_id: subnet id
        logger: logger

    Returns:
        True if the subnet is a public subnet, False otherwise

    """
    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the subnet to get its VPC ID
    subnet_response = ec2_client.describe_subnets(SubnetIds=[subnet_id])

    if subnet_response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    if not subnet_response.get("Subnets"):
        _common_.info_logger(f"No subnet found with ID {subnet_id}")
        return False

    vpc_id = subnet_response.get("Subnets", [{}])[0].get("VpcId")
    # Describe route tables associated with the VPC

    _parameters = {
        "Filters": [
            {
                "Name": "vpc-id",
                "Values": [
                    vpc_id
                ]
            }
        ]
    }
    route_table_response = ec2_client.describe_route_tables(**_parameters)

    if route_table_response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    route_tables = route_table_response.get("RouteTables")

    main_route_table_id = None
    public_route_table_ids = set()

    # find main route table and route tables which includes a route to an internet gateway
    for route_table in route_tables:
        for association in route_table.get("Associations", []):
            if association.get("Main") is True:
                main_route_table_id = association.get("RouteTableId")

        for route in route_table.get('Routes', []):
            if route.get("GatewayId") and route.get("GatewayId", "").startswith('igw-'):
                public_route_table_ids.add(route_table.get("RouteTableId"))

    _parameters = {
        "Filters": [
            {
                "Name": "association.subnet-id",
                "Values": [subnet_id]
             }
        ]
    }
    response = ec2_client.describe_route_tables(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    route_tables = response.get("RouteTables")
    if not route_tables:
        _common_.info_logger(f"No route table found for subnet ID {subnet_id}, use main route table")

    route_tables = route_tables[0] if route_tables else main_route_table_id
    return route_tables in public_route_table_ids


@_common_.aws_client_handle_exceptions()
def get_public_subnets(vpc_id: str,
                       aws_region: str = "us-east-1",
                       logger: Log = None
                       ) -> Union[List, None]:
    """find the first public subnet in the specified VPC

    Args:
        vpc_id: vpc id
        aws_region: aws region
        logger: logger

    Returns:
        return the first public subnet in the specified VPC else None

    """
    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe route tables for the VPC
    _parameter = {
        "Filters": [
            {
                "Name": "vpc-id",
                "Values": [vpc_id]
            }
        ]
    }
    response = ec2_client.describe_subnets(**_parameter)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    subnets = response['Subnets']

    if not subnets:
        _common_.info_logger(f"No subnets found in VPC ID {vpc_id}")
        return []

    public_subnets = set()

    # Extract subnet IDs and print details
    for subnet in subnets:
        _parameter = {
            "subnet_id": subnet.get("SubnetId"),
            "aws_region": aws_region
        }
        if is_public_subnet(**_parameter):
            public_subnets.add(subnet['SubnetId'])

    return list(public_subnets)


@_common_.aws_client_handle_exceptions()
def define_network(vpc_id: str = None,
                   aws_region: str = "us-east-1",
                   logger: Log = None
                   ) -> Union[Dict, None]:
    """return appropriate network configuration

    Args:
        vpc_id: vpc id
        aws_region: aws region
        logger: logger

    Returns:
        return the first public subnet in the specified VPC if found and if no vpc id is provided then search for all
        vpcs and return the first public subnet found else None

    """
    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe all VPCs
    response = ec2_client.describe_vpcs()
    vpcs = response.get("Vpcs")
    if not vpcs:
        _common_.info_logger("No VPCs found.")
        return

    if vpc_id:
        # pick the very first public subnet
        _parameter = {
            "vpc_id": vpc_id,
            "aws_region": aws_region,
            }
        if public_subnets := get_public_subnets(**_parameter):
            return {
                "vpc_id": vpc_id,
                "public_subnet": public_subnets[0]
            }
        else:
            return None

    # if vpc_id is not provided, will search thru all vpcs and pick the very first public subnet
    for vpc in vpcs:
        vpc_id = vpc.get("VpcId")
        _common_.info_logger(f"VPC ID: {vpc_id}")
        _parameter = {
            "vpc_id": vpc_id,
            "aws_region": aws_region,
        }
        if public_subnets := get_public_subnets(**_parameter):
            return {
                "vpc_id": vpc_id,
                "public_subnet": public_subnets[0]
            }

    return None


@_common_.aws_client_handle_exceptions()
def get_security_group_id(sg_name: str,
                          vpc_id: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> Union[None, str]:
    """retrieve security group id if the specified security group exists

    Args:
        sg_name: security group name
        vpc_id: vpc id
        aws_region: aws region
        logger: logger

    Returns:
        return group id if exists else None
    """
    _parameter = {
        "vpc_id": vpc_id,
        "aws_region": aws_region
    }
    for each_sg in get_security_groups_in_vpc(**_parameter):
        if each_sg.get("GroupName") == sg_name:
            _common_.info_logger(f"security group name '{sg_name}' is found")
            return each_sg.get("GroupId")
    return None


@_common_.aws_client_handle_exceptions()
def delete_security_group(sg_id: str,
                          max_retries: int = 5,
                          wait_time: int = 60,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> bool:
    """delete security group id if the specified security group exists

    Args:
        sg_id: security group id
        max_retries: max retries
        wait_time: wait time
        aws_region: aws region
        logger: logger

    Returns:
        return group id if exists else None
    """


    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Delete the security group
    _parameter = {
        "GroupId": sg_id
    }

    for attempt in range(1, max_retries + 1):
        try:
            response = ec2_client.delete_security_group(**_parameter)
            if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
                _common_.error_logger(currentframe().f_code.co_name,
                                      f"operation failed, reason response code is not 200",
                                      logger=logger,
                                      mode="error",
                                      ignore_flag=False)
            _common_.info_logger(f"security group id '{sg_id}' is deleted")
            return True
        except ClientError as err:
            if err.response['Error']['Code'] == 'DependencyViolation':
                _common_.info_logger(f"Attempt {attempt}: Dependency violation detected. Retrying in {wait_time} seconds...")
                sleep(wait_time)  # Wait before retrying
            else:
                # If it's a different error, raise it
                _common_.error_logger(currentframe().f_code.co_name,
                                      f"Error occurred: {err}, Failed to delete security group {sg_id} after {max_retries} attempts.",
                                      logger=logger,
                                      mode="error",
                                      ignore_flag=False)

    return False



@_common_.aws_client_handle_exceptions()
def get_security_groups_in_vpc(vpc_id: str,
                               aws_region: str = "us-east-1",
                               logger: Log = None
                               ) -> List[Union[None, Dict]]:
    """verify if the specified security group exists

    Args:
        aws_region: aws region
        vpc_id: vpc id
        logger: logger

    Returns:
        True if the security group exists, False otherwise.
    """

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe security groups with a filter on the VPC ID
    _parameters = {
        "Filters": [
            {
                "Name": "vpc-id",
                "Values": [vpc_id]
            }
        ]
    }
    response = ec2_client.describe_security_groups(**_parameters)
    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    return [{"GroupName": sg.get("GroupName"), "GroupId": sg.get("GroupId")} for sg in
            response.get("SecurityGroups", [])]


@_common_.aws_client_handle_exceptions()
def create_security_group(sg_name: str,
                          vpc_id: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> Union[None, str]:
    """create security group in aws

    Args:
        sg_name: security group name
        vpc_id: vpc id
        aws_region: aws region
        logger: logger

    Returns:
        return security group id if successful, None otherwise

    """

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Define the parameters for the security group
    description = f"created by auto deployment {sg_name}"

    # Create the security group
    _parameters = {
        "GroupName": sg_name,
        "Description": description,
        "VpcId": vpc_id
    }
    response = ec2_client.create_security_group(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    _common_.info_logger(f"security group name '{sg_name}' is created")
    return response.get("GroupId", None)


@_common_.aws_client_handle_exceptions()
def create_sg_ingress_rules(sg_id: str,
                            sg_ingress_rules: List[Dict],
                            aws_region: str = "us-east-1",
                            logger: Log = None
                            ) -> bool:
    """Add ingress rules to a security group.
    Args:
        aws_region: aws region
        sg_id: security group id
        sg_ingress_rules: list of ingress rules
        logger: logger

    Returns:
        True if the rules were added successfully otherwise False

    """

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Add ingress rules to the security group
    _parameter = {
        "GroupId": sg_id,
        "IpPermissions": sg_ingress_rules
    }
    response = ec2_client.authorize_security_group_ingress(**_parameter)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Ingress rules added to the security group {sg_id}")
    return True


@_common_.aws_client_handle_exceptions("InvalidLaunchTemplateName.NotFoundException")
def check_launch_template_exists(launch_template_name: str,
                                 aws_region: str,
                                 logger: Log = None
                                 ) -> bool:

    """check if the specified launch template exists

    Args:
        launch_template_name: launch template name
        aws_region: aws region
        logger: logger object

    Returns:
        returns True if the launch template exists, False otherwise

    """

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Describe the launch template to check if it exists
    _parameters = {
        "LaunchTemplateNames": [launch_template_name]
    }
    response = ec2_client.describe_launch_templates(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    return True


@_common_.aws_client_handle_exceptions("InvalidLaunchTemplateName.NotFoundException")
def delete_launch_template(launch_template_name: str,
                           aws_region: str,
                           logger: Log = None
                           ) -> bool:

    """delete the specified launch template

    Args:
        launch_template_name: launch template name
        aws_region: aws region
        logger: logger object

    Returns:
        returns True if the launch template is deleted successfully, False otherwise

    """

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    # Delete the launch template
    _parameters = {
        "LaunchTemplateName": launch_template_name
    }
    response = ec2_client.delete_launch_template(**_parameters)

    if response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Launch template '{launch_template_name}' deleted successfully")
    return response


@_common_.aws_client_handle_exceptions()
def create_launch_template(project_id: str,
                           launch_template_name: str,
                           image_id: str,
                           keypair_name: str,
                           security_group_ids: Union[str, List],
                           subnet_id: str,
                           instance_name: str,
                           instance_type: str,
                           kms_id: str,
                           launch_template_description: str,
                           user_data: str = "",
                           iam_instance_role: str = "",
                           aws_region: str = "us-east-1",
                           logger: Log = None
                           ):

    """create launch template given specific parameters

    Args:

        project_id: project name, used for tagging
        launch_template_name: launch template name
        image_id: image id
        keypair_name: keypair name
        security_group_ids: security group
        subnet_id: subnet id
        instance_name: instance name
        instance_type: instance type
        kms_id: kms id
        launch_template_description: launch template description
        user_data: user data plain text
        iam_instance_role:  iam role name
        aws_region: aws region
        logger: logger object

    Returns:
        returns the response from the create launch template operation

    """



    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    if isinstance(security_group_ids, str):
        security_group_ids = [security_group_ids]

    # if not _util_common_.is_base64_encoded(user_data):
    user_data = _util_common_.string_to_base64(user_data)


    _parameters = {
            "LaunchTemplateName": launch_template_name,
            "VersionDescription": launch_template_description,
            "LaunchTemplateData": {
                "ImageId": image_id,
                "InstanceType": instance_type,
                'BlockDeviceMappings': [
                    {
                        'DeviceName': '/dev/xvda',
                        'Ebs': {
                            'VolumeSize': 30,
                            'VolumeType': 'gp2',
                            'Encrypted': True,
                            'KmsKeyId': kms_id
                        }
                    }
                ],
                'NetworkInterfaces': [
                    {
                        'AssociatePublicIpAddress': True,
                        'DeviceIndex': 0,
                        'SubnetId': subnet_id,
                        'Groups': security_group_ids,
                    },
                ],
                "KeyName": keypair_name,
                # "SecurityGroupIds": security_group_ids,
                'InstanceMarketOptions': {
                    'MarketType': 'spot',
                    'SpotOptions': {
                        'SpotInstanceType': 'one-time'
                    }
                },
                "UserData": user_data,
                "TagSpecifications": [
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {
                                "Key": "Name",
                                "Value": instance_name
                            },
                            {
                                'Key': 'pg_auto_project_name',
                                'Value': project_id
                            }
                        ]
                    }
                ]
            }
        }
    if iam_instance_role:
        _parameters["LaunchTemplateData"]["IamInstanceProfile"] = {
            "Name": iam_instance_role
        }
    _response = ec2_client.create_launch_template(**_parameters)
    if _response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"operation failed, reason response code is not 200",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)

    _common_.info_logger(f"Launch template '{launch_template_name}' created successfully")
    return _response.get("LaunchTemplate", {}).get("LaunchTemplateId")


@_common_.aws_client_handle_exceptions()
def run_ec2_from_template(launch_template_id: str,
                          version: str = "$Latest",
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ) -> List[str]:
    """launch an ec2 instance from the specified launch template

    Args:
        launch_template_id: launch template id
        aws_region: aws region
        version: version, default to latest
        logger: logger

    Returns:
        True if the instance is launched successfully, False otherwise

    """
    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)

    _parameters = {
        "LaunchTemplate": {
            "LaunchTemplateId": launch_template_id,
            "Version": version
        },
        # # "SubnetId": subnet_id,
        # "NetworkInterfaces": [
        #     {
        #         "AssociatePublicIpAddress": False,
        #         "SubnetId": subnet_id,
        #         "Groups": ["sg-0cea0bd861446063b"],
        #         "DeviceIndex": 0,
        #     }],
        "MinCount": 1,
        "MaxCount": 1
    }

    _response = ec2_client.run_instances(**_parameters)
    if _response.get("ResponseMetadata").get("HTTPStatusCode") != 200:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"not able to retrieve object",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    else:
        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Waiting for instance {instance_id} to reach the 'running' state...")

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])

        # Wait for the instance to pass both system and instance status checks
        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Waiting for instance {instance_id} to pass all status checks...")

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            status_waiter = ec2_client.get_waiter('instance_status_ok')
            status_waiter.wait(InstanceIds=[instance_id])

        for each_instance in _response.get("Instances", []):
            instance_id = each_instance.get("InstanceId")
            _common_.info_logger(f"Instance {instance_id} has passed all status checks and is fully operational.")

        return [each_instance.get("InstanceId") for each_instance in _response.get("Instances", [])]


@_common_.aws_client_handle_exceptions()
def wait_for_ec2_running(instance_id: str,
                         aws_region: str = "us-east-1",
                         logger: Log = None
                         ):

    from datetime import datetime

    if isinstance(instance_id, str): instance_id = [instance_id]

    # initialize the boto3 ec2 client
    ec2_client = boto3.client('ec2', region_name=aws_region)
    _common_.info_logger(f"Waiting for instance {instance_id} to be in the running state...")
    done_flag = False
    _parameters = {
        "InstanceIds": instance_id
    }
    while True:
        response = ec2_client.describe_instance_status(**_parameters)
        print(response)
        if done_flag: break
        elif "InstanceStatuses" in response and len(response["InstanceStatuses"]) > 0:
            for status in response["InstanceStatuses"]:
                instance_status = status.get('InstanceStatus', {}).get('Details', [None])[0].get('Status')
                if instance_status == "passed":
                    done_flag = True
                    break
                _common_.info_logger(f"{datetime.now()}: Instance Id {instance_id}, instance status: {instance_status}")
        else:
            _common_.info_logger(f"No status information available for instance {instance_id[0]}")
            break
        sleep(__WAIT_TIME__)
    _common_.info_logger(f"{instance_id} is running")

