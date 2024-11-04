from typing import List, Union
from logging import Logger as Log
from inspect import currentframe
from time import sleep
from _common import _common as _common_
from _config import _config as _config_


_WAIT_TIME_ = 10


@_common_.aws_client_handle_exceptions()
def run(lt_name: str,
        project_id: str,
        ami_id: str,
        keypair_name: str,
        sg_id: Union[str, List],
        subnet_id: str,
        instance_type: str,
        instance_name: str,
        kms_id: str = "",
        iam_instance_role: str = "",
        user_data: str = "",
        aws_region: str = "us-east-1",
        logger: Log = None
        ) -> Union[List, None]:

    """wrapper function for creating a launch template

    Args:

        user_data:
        lt_name: launch template
        project_id: project id
        ami_id: ami id
        keypair_name: keypair name
        sg_id: security group id
        subnet_id: subnet id
        instance_type: instance type
        instance_name: instance name
        kms_id: kms id
        iam_instance_role: instance profile name
        user data, will auto detect whether it is base64 encoded
        aws_region: aws region
        logger: logger object

    Returns:
        return the launch template id if it is created successfully, None otherwise

    """
    if not kms_id:
        from _aws import _kms

        _parameter = {
            "kms_alias": "alias/aws/ebs",
            "aws_region": aws_region
        }
        default_kms_id = _kms.get_aws_managed_keys(**_parameter)
        if default_kms_id:
            kms_id = default_kms_id[0]
        else:
            _common_.error_logger(currentframe().f_code.co_name,
                                  f"no default kms key found",
                                  logger=logger,
                                  mode="error",
                                  ignore_flag=False)
            return None

    _config = _config_.PGConfigSingleton()

    if not kms_id:
        kms_id = _config.config.get("kms_arn")

    from _aws import ec2
    _parameter = {
        "launch_template_name": lt_name,
        "aws_region": aws_region
    }
    if ec2.check_launch_template_exists(**_parameter):
        _parameter = {
            "launch_template_name": lt_name,
            "aws_region": aws_region
        }
        ec2.delete_launch_template(**_parameter)

    sleep(_WAIT_TIME_)

    launch_template_description = f"auto created for {project_id}"

    launch_template_id = ec2.create_launch_template(project_id=project_id,
                                                    launch_template_name=lt_name,
                                                    image_id=ami_id,
                                                    keypair_name=keypair_name,
                                                    security_group_ids=sg_id,
                                                    subnet_id=subnet_id,
                                                    instance_name=instance_name,
                                                    instance_type=instance_type,
                                                    kms_id=kms_id,
                                                    launch_template_description=launch_template_description,
                                                    iam_instance_role=iam_instance_role,
                                                    user_data=user_data,
                                                    aws_region=aws_region
                                                    )
    sleep(_WAIT_TIME_)

    if launch_template_id:
        return ec2.run_ec2_from_template(launch_template_id)
    else:
        _common_.error_logger(currentframe().f_code.co_name,
                              f"can't find appropriate launch template id",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)


@_common_.aws_client_handle_exceptions()
def destroy(lt_name: str,
            aws_region: str = "us-east-1",
            logger: Log = None
            ) -> bool:

    """this function destroys the launch template

    Args:
        lt_name: launch template
        aws_region: aws region
        logger: logger object

    Returns:
        return the launch template id if it is created successfully, None otherwise

    """
    from _aws import ec2
    _parameter = {
        "launch_template_name": lt_name,
        "aws_region": aws_region
    }
    if ec2.check_launch_template_exists(**_parameter):
        _parameter = {
            "launch_template_name": lt_name,
            "aws_region": aws_region
        }
        ec2.delete_launch_template(**_parameter)
    return True



