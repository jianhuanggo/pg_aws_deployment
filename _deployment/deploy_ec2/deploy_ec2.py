from inspect import currentframe
from logging import Logger as Log
from _common import _common as _common_
_WAIT_TIME_ = 4


def run(project_name: str,
        aws_account_number: str,
        project_path: str,
        keypair_name: str,
        private_key_path: str,
        sg_name: str,
        sg_ingress_rules: list,
        website_port: int,
        instance_type: str ="t2.micro",
        user_data: str = "",
        aws_region: str = "us-east-1",
        logger: Log = None) -> bool:

    """create an ec2 instance for the project end to end

    Args:

        project_name: project name
        aws_account_number: aws account number
        project_path: project path
        keypair_name: keypair name
        private_key_path: private key path
        sg_name: security group name
        website_port: website port
        instance_type: instance type
        sg_ingress_rules: security group ingress rules
        user_data: user data, will auto detect whether it is base64 encoded
        aws_region: aws region
        logger: log object

    Returns:
        returns True if successful else False

    """



    # project_name = "pg_simple_website"
    # aws_account_number = "717435123117"
    # aws_region = "us-east-1"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    # keypair_name = f"{project_name}-keypair"
    # private_key_path = f"{project_name}-keypair.pem"
    # sg_name = f"{project_name}-security-group"

    from _aws import ec2

    # terminate existing instance belong to the project
    for instance_id in ec2.find_instances_by_tag("pg_auto_project_name", project_name):
        response = ec2.describe_ec2_get_spot_request(instance_id)
        if response and (spot_request_id := response[0].get("spot_request_id")):
            ec2.terminate_spot_request_and_instances(spot_request_id)

    # find default ami id
    ami_id = ec2.find_image(aws_region)
    if not ami_id:
        _common_.error_logger(currentframe().f_code.co_name,
                              "ami id not found in the specified region",
                              logger=None,
                              mode="error",
                              ignore_flag=False)
    # create a key pair
    from _deployment.deploy_ec2 import ec2_key_pair
    _parameter = {
        "key_name": keypair_name,
        "file_path": private_key_path,
        "aws_region": aws_region
    }

    ec2_key_pair.run(**_parameter)

    # find an appropriate subnet
    from _deployment.deploy_ec2 import ec2_network
    _parameters = {
        "aws_region": aws_region
    }
    network_info = ec2_network.run(**_parameters)
    vpc_id = network_info.get("vpc_id")

    # create a security group
    from _deployment.deploy_ec2 import ec2_security_group
    _parameter = {
        "vpc_id": vpc_id,
        "sg_name": sg_name,
        "project_name": project_name,
        "sg_ingress_rules": sg_ingress_rules,
        "aws_region": aws_region
    }
    sg_id = ec2_security_group.run(**_parameter)

    # create instance profile role
    # iam_instance_role = f"{project_name}-role"
    from _deployment.deploy_ec2 import ec2_role

    # _parameters = {
    #     "iam_instance_role": iam_instance_role,
    #     "aws_region": aws_region
    # }

    role_info = ec2_role.run(project_name=project_name)

    # create a launch template
    from _deployment.deploy_ec2 import ec2_launch_template

    launch_template_name = f"lt-{project_name}-launch-template"
    instance_name = f"{project_name}-instance"

    print(launch_template_name, project_name, ami_id, keypair_name, sg_id, network_info.get("public_subnet"), instance_type, instance_name, role_info.get("instance_profile_name"), aws_region)

    lt_response = ec2_launch_template.run(lt_name=launch_template_name,
                                          project_id=project_name,
                                          ami_id=ami_id,
                                          keypair_name=keypair_name,
                                          sg_id=[sg_id],
                                          subnet_id=network_info.get("public_subnet"),
                                          instance_type=instance_type,
                                          instance_name=instance_name,
                                          iam_instance_role=role_info.get("instance_profile_name"),
                                          user_data=user_data,
                                          aws_region=aws_region
                                          )

    if len(lt_response) > 0:
        public_dns_name = ec2.find_instance_by_id(lt_response[0])[0].get("PublicDnsName")
        _common_.info_logger(f"ssh -i {private_key_path} ec2-user@{public_dns_name}")
        _common_.info_logger(f"http://{public_dns_name}:{website_port}")

    return True


def destroy(project_name: str,
            aws_account_number: str,
            project_path: str,
            keypair_name: str,
            private_key_path: str,
            sg_name: str,
            user_data: str = "",
            aws_region: str = "us-east-1",
            logger: Log = None) -> bool:

    """this function is to destroy the resources created by run

    Args:
        project_name: project name
        aws_account_number: aws account number
        project_path: project path
        keypair_name: keypair name
        private_key_path: private key path
        sg_name: security group name
        user_data: user data, will auto detect whether it is base64 encoded
        aws_region: aws region
        logger: log object

    Returns:
        returns True if successful else False

    """

    from _aws import ec2

    # terminate existing instance belong to the project
    for instance_id in ec2.find_instances_by_tag("pg_auto_project_name", project_name):
        response = ec2.describe_ec2_get_spot_request(instance_id)
        if response and (spot_request_id := response[0].get("spot_request_id")):
            ec2.terminate_spot_request_and_instances(spot_request_id)



    # delete a key pair
    from _deployment.deploy_ec2 import ec2_key_pair
    _parameter = {
        "key_name": keypair_name,
        "aws_region": aws_region
    }
    ec2_key_pair.destroy(**_parameter)

    # find an appropriate subnet
    from _deployment.deploy_ec2 import ec2_network
    _parameters = {
        "aws_region": aws_region
    }
    network_info = ec2_network.run(**_parameters)
    vpc_id = network_info.get("vpc_id")

    # delete a security group
    from _deployment.deploy_ec2 import ec2_security_group
    _parameter = {
        "vpc_id": vpc_id,
        "sg_name": sg_name,
        "project_name": project_name,
        "aws_region": aws_region
    }
    ec2_security_group.destroy(**_parameter)

    from _deployment.deploy_ec2 import ec2_role

    ec2_role.destroy(project_name=project_name)

    # create a launch template
    from _deployment.deploy_ec2 import ec2_launch_template

    launch_template_name = f"lt-{project_name}-launch-template"
    instance_name = f"{project_name}-instance"

    # find default ami id
    ami_id = ec2.find_image(aws_region)
    if not ami_id:
        _common_.error_logger(currentframe().f_code.co_name,
                              "ami id not found in the specified region",
                              logger=None,
                              mode="error",
                              ignore_flag=False)

    ec2_launch_template.destroy(lt_name=launch_template_name,
                                aws_region=aws_region
                                )

    return True
