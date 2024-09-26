from time import sleep
from jinja2 import Template
from inspect import currentframe
from _common import _common as _common_
from _util import _util_common as _util_common_
_WAIT_TIME_ = 4


def example_website_ec2():
    """
    add instance role to the instance
    Returns:

    """


    project_name = "pg_simple_website_streamlit"
    aws_account_number = "717435123117"
    aws_region = "us-east-1"
    project_path = "/Users/jianhuang/anaconda3/envs/pg_simple_login_ui/pg_simple_login_ui"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    keypair_name = f"{project_name}-keypair"
    file_path = f"{project_name}-keypair.pem"
    sg_name = f"{project_name}-security-group"

    ecr_repository_name = f"{project_name}-test"
    website_port = 8501
    instance_type = "t2.micro"

    sg_ingress_rules = [
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
        },
        {
            'IpProtocol': 'tcp',
            'FromPort': website_port,
            'ToPort': website_port,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Allow HTTPS from anywhere
        }
    ]


    # ecr_repository_name = "pg_finance_trade_test8"
    # aws_account_number = "717435123117"
    # aws_region = "us-east-1"
    # lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    # lambda_function_name = f"lambda-{ecr_repository_name}"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    # api_gateway_api_name = "MyApi"

    from _deployment.build_image import setup_ecr

    # create ecr repository
    setup_ecr.run(ecr_repository_name,
                  aws_region
                  )

    sleep(_WAIT_TIME_)

    # build docker image
    from _deployment.build_image import build_image

    build_image.run(ecr_repository_name=ecr_repository_name,
                    aws_region=aws_region,
                    aws_account_number=aws_account_number,
                    project_path=project_path,
                    dockerfile_filepath=f"{project_path}/Dockerfile_streamlit"
                    )
    # exit(0)
    sleep(_WAIT_TIME_)

    from _deployment.deploy_ec2 import ec2_userdata_template

    user_data_input = {
        "aws_account_number": aws_account_number,
        "ecr_repo": ecr_repository_name,
        "aws_region": aws_region,
        "forwarding_port_string": f"-p {website_port}:{website_port}"
    }

    template = Template(ec2_userdata_template.user_data_streamlit_template)
    rendered_user_data = template.render(user_data_input)

    # Print the rendered user data
    print(rendered_user_data)

    from _deployment.deploy_ec2 import deploy_ec2

    _parameters = {
        "project_name": project_name,
        "aws_account_number": aws_account_number,
        "project_path": project_path,
        "keypair_name": keypair_name,
        "private_key_path": file_path,
        "sg_name": sg_name,
        "sg_ingress_rules": sg_ingress_rules,
        "user_data": rendered_user_data,
        "aws_region": aws_region,
        "website_port": website_port,
        "instance_type": instance_type
    }

    deploy_ec2.run(**_parameters)
    return True





def example_website_ec2_destroy():
    """this function is used to destroy the resources created by example_website_ec2


    """
    project_name = "pg_simple_website_streamlit"
    aws_account_number = "717435123117"
    aws_region = "us-east-1"
    project_path = "/Users/jianhuang/anaconda3/envs/pg_simple_login_ui/pg_simple_login_ui"
    keypair_name = f"{project_name}-keypair"
    file_path = f"{project_name}-keypair.pem"
    sg_name = f"{project_name}-security-group"

    ecr_repository_name = f"{project_name}-test"
    website_port = 8501
    instance_type = "t2.micro"

    from _deployment.build_image import setup_ecr

    # create ecr repository
    setup_ecr.destroy(ecr_repository_name,
                      aws_region
                      )

    sleep(_WAIT_TIME_)

    from _deployment.deploy_ec2 import ec2_userdata_template

    user_data_input = {
        "aws_account_number": aws_account_number,
        "ecr_repo": ecr_repository_name,
        "aws_region": aws_region
    }

    from _deployment.deploy_ec2 import deploy_ec2
    _parameters ={
        "project_name": project_name,
        "aws_account_number": aws_account_number,
        "project_path": project_path,
        "keypair_name": keypair_name,
        "private_key_path": file_path,
        "sg_name": sg_name,
        "aws_region": aws_region
    }

    deploy_ec2.destroy(**_parameters)

    return True
