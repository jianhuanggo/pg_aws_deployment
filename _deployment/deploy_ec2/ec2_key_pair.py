from inspect import currentframe
from _common import _common as _common_
from time import sleep

_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def run(key_name: str,
        file_path: str,
        aws_region: str = "us-east-1") -> bool:
    """create a ssh key pair

    Args:
        key_name: the name of the key pair
        file_path: the path to save the private key
        aws_region: aws region

    Returns:
        return the key pair id if successful otherwise None

    """
    from _aws import ec2
    _parameters = {
        "key_pair_name":key_name,
        "aws_region": aws_region
    }

    if ec2.describe_key_pair(**_parameters):
        ec2.delete_key_pair(**_parameters)

    _parameter = {
        "key_name": key_name,
        "file_path": file_path,
        "aws_region": aws_region
    }

    print(file_path, key_name, aws_region)

    sleep(_WAIT_TIME_)
    kp_response = ec2.create_key_pair(**_parameter)
    if not kp_response:
        _common_.error_logger(currentframe().f_code.co_name,
                              "unable to create keypair",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    # print(kp_response)
    return True


@_common_.aws_client_handle_exceptions()
def destroy(key_name: str,
            file_path: str = "",
            aws_region: str = "us-east-1") -> bool:
    """this function is to destroy the resources created by run

    Args:
        key_name: the name of the key pair
        file_path: the path to save the private key
        aws_region: aws region

    Returns:
        return the key pair id if successful otherwise None

    """
    from _aws import ec2
    _parameters = {
        "key_pair_name":key_name,
        "aws_region": aws_region
    }

    if ec2.describe_key_pair(**_parameters):
        ec2.delete_key_pair(**_parameters)

    return True
