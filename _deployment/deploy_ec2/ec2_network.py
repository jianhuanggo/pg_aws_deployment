from typing import List, Union, Dict
from logging import Logger as Log
from inspect import currentframe
from _common import _common as _common_


_WAIT_TIME_ = 4


@_common_.aws_client_handle_exceptions()
def run(vpc_id: str = None,
        aws_region: str = "us-east-1",
        logger: Log = None) -> Union[Dict, None]:
    """find a suitable public subnet to place the resource

    Args:
        vpc_id: specified vpc id
        aws_region: aws region
        logger: logger object

    Returns:
        return the network information regarding public subnet and vpc id if successful else None

    """
    from _aws import ec2


    _parameters = {
        "aws_region": aws_region
    }
    network_info = ec2.define_network(**_parameters)

    if not network_info:
        _common_.error_logger(currentframe().f_code.co_name,
                              "No public subnet found",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    vpc_id = network_info.get("vpc_id")
    if not vpc_id:
        _common_.error_logger(currentframe().f_code.co_name,
                              "No vpc found to place the resource",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    return network_info
