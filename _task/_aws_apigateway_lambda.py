import os.path
from time import sleep
from _common import _common as _common_
from _util import _util_file as _util_file_

__WAIT_TIME__ = 10

"""



"""



def create_deployment(ecr_repository_name: str,
                      lambda_function_role: str,
                      lambda_function_name: str,
                      project_path: str,
                      api_gateway_api_name: str,
                      aws_account_number: str,
                      api_method: str = "GET",
                      aws_region: str = "us-east-1"
                      ):
    """create a new deployment using api gateway and lambda pattern



    1) create ecr repository
    2) build docker image (right now it is done using shell, change it to a library call)
    3) create lambda role
    4) deploy lambda
    5) missing: create a new api gateway and root resource from scratch
    6) create api gateway resource
    7) create api gateway resource method
    8) create api gateway resource method integration
    9) create api gateway resource method response
    10) create api gateway deployment and deploy to stage


    access:

    1) lambda function role (created by scratch)
    2) api gateway role (leveage the existing role) <- ideally this needs to be created from scratch

    needed:

    create a new api gateway from scratch
    create a new api gateway role from scratch

    Returns:

    """

    # ecr_repository_name = "pg_transcribe_3_test"
    # aws_account_number = "717435123117"
    # aws_region = "us-east-1"
    # lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    # lambda_function_name = f"lambda-{ecr_repository_name}"
    # project_path = "/Users/jianhuang/anaconda3/envs/transcribe_5/transcribe_5"
    # api_gateway_api_name = "MyApi_new4"
    # api_method = "GET"
    from _code import _generate_lambda_function
    _generate_lambda_function.run(project_path)

    from _deployment.build_image import setup_ecr

    # create ecr repository
    setup_ecr.run(ecr_repository_name,
                  aws_region,
                  aws_account_number,
                  project_path,
                  lambda_function_name,
                  lambda_function_role,
                  api_gateway_api_name
                  )

    sleep(__WAIT_TIME__)
    docker_file_path = os.path.join(project_path, "Dockerfile")
    if _util_file_.is_file_exist(docker_file_path):
        _common_.info_logger(f"using Dockerfile at {docker_file_path}")
    else:
        _common_.error_logger(f"Dockerfile does not exist at {docker_file_path}",
                              "DockerfileError")


    # build docker image
    from _deployment.build_image import build_image
    build_image.run(ecr_repository_name=ecr_repository_name,
                    aws_region=aws_region,
                    aws_account_number=aws_account_number,
                    project_path=project_path,
                    dockerfile_filepath=docker_file_path,
                    lambda_function_name=lambda_function_name,
                    lambda_function_role=lambda_function_role,
                    api_gateway_api_name=api_gateway_api_name
                    )

    sleep(__WAIT_TIME__)

    # create lambda role
    from _deployment.deploy_lambda import setup_lambda_role
    setup_lambda_role.run(ecr_repository_name,
                          aws_region,
                          aws_account_number,
                          project_path,
                          lambda_function_name,
                          lambda_function_role,
                          api_gateway_api_name
                          )

    sleep(__WAIT_TIME__)

    # deploy lambda
    from _deployment.deploy_lambda import deploy_lambda
    deploy_lambda.run(ecr_repository_name,
                      aws_region,
                      aws_account_number,
                      project_path,
                      lambda_function_name,
                      lambda_function_role,
                      api_gateway_api_name
                      )

    sleep(__WAIT_TIME__)

    # deploy api gateway
    from _deployment.deploy_api_gateway import deploy_api_gateway
    deploy_api_gateway.run(ecr_repository_name=ecr_repository_name,
                           aws_account_number=aws_account_number,
                           project_path=project_path,
                           lambda_function_name=lambda_function_name,
                           lambda_function_role=lambda_function_role,
                           api_gateway_api_name=api_gateway_api_name,
                           api_method=api_method,
                           aws_region=aws_region
                           )


def destroy_deployment(lambda_function_name: str,
                      api_gateway_api_name: str,
                      aws_region: str = "us-east-1"):
    """destroy api gateway resources only

    missing: destroy lambda function, ecr repository, iam role

    Returns:

    """
    from _deployment.destroy_api_gateway import destroy_api_gateway

    # ecr_repository_name = "pg_finance_trade_test8"
    # aws_account_number = "717435123117"
    # aws_region = "us-east-1"
    # lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    # lambda_function_name = f"lambda-{ecr_repository_name}"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    # api_gateway_api_name = "MyApi_new4"

    destroy_api_gateway.destroy_api_gateway_resource(api_gateway_api_name=api_gateway_api_name,
                                                     lambda_function_name=lambda_function_name,
                                                     aws_region=aws_region
                                                     )