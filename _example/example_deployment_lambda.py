from time import sleep
from _common import _common as _common_
from _util import _util_common as _util_common_
_WAIT_TIME_ = 4


def example_end_2_end():
    """this examples shows end to end deployment process

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

    ecr_repository_name = "pg_finance_trade_test8"
    aws_account_number = "717435123117"
    aws_region = "us-east-1"
    lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    lambda_function_name = f"lambda-{ecr_repository_name}"
    project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    api_gateway_api_name = "MyApi"

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

    sleep(_WAIT_TIME_)

    # build docker image
    from _deployment.build_image import build_image
    build_image.run(ecr_repository_name,
                    aws_region,
                    aws_account_number,
                    project_path,
                    lambda_function_name,
                    lambda_function_role,
                    api_gateway_api_name
                    )

    sleep(_WAIT_TIME_)

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

    sleep(20)

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

    sleep(_WAIT_TIME_)

    # create api gateway resource
    from _deployment.deploy_api_gateway import api_gateway_api_resource
    api_gateway_api_resource.run(ecr_repository_name,
                                 aws_region,
                                 aws_account_number,
                                 project_path,
                                 lambda_function_name,
                                 lambda_function_role,
                                 api_gateway_api_name
                                 )

    # create api gateway resource method
    from _deployment.deploy_api_gateway import api_gateway_api_method
    api_gateway_api_method.run(ecr_repository_name,
                               aws_region,
                               aws_account_number,
                               project_path,
                               lambda_function_name,
                               lambda_function_role,
                               api_gateway_api_name
                               )

    # create api gateway resource method integration
    from _deployment.deploy_api_gateway import api_gateway_api_method_integration
    api_gateway_api_method_integration.run(ecr_repository_name,
                               aws_region,
                               aws_account_number,
                               project_path,
                               lambda_function_name,
                               lambda_function_role,
                               api_gateway_api_name
                               )

    # create api gateway resource method response
    from _deployment.deploy_api_gateway import api_gateway_api_method_response
    api_gateway_api_method_response.run(ecr_repository_name,
                                        aws_region,
                                        aws_account_number,
                                        project_path,
                                        lambda_function_name,
                                        lambda_function_role,
                                        api_gateway_api_name
                                        )

    # create api gateway deployment and deploy to stage
    from _deployment.deploy_api_gateway import api_gateway_api_deployment
    api_gateway_api_deployment.run(ecr_repository_name,
                                   aws_region,
                                   aws_account_number,
                                   project_path,
                                   lambda_function_name,
                                   lambda_function_role,
                                   api_gateway_api_name
                                   )


def example_deploy_existing_lambda_function_to_apigateway():
    """this examples shows deploy existing lambda function to api gateway

    1) create api gateway resource
    2) create api gateway resource method
    3) create api gateway resource method integration
    4) create api gateway resource method response
    5) create api gateway deployment and deploy to stage

    Returns:

    """
    # from _deployment.deploy_api_gateway import api_gateway_api_id, api_gateway_api_root_id
    # api = api_gateway_api_id.get_api_gateway_id("us-east-1", "MyApi")
    # api_root = api_gateway_api_root_id.get_api_gateway_root_id("us-east-1", api)

    ecr_repository_name = "pg_finance_trade_test8"
    aws_account_number = "717435123117"
    aws_region = "us-east-1"
    lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    lambda_function_name = f"lambda-{ecr_repository_name}"
    project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    api_gateway_api_name = "MyApi"

    # create api gateway resource
    from _deployment.deploy_api_gateway import api_gateway_api_resource
    api_gateway_api_resource.run(ecr_repository_name,
                                 aws_region,
                                 aws_account_number,
                                 project_path,
                                 lambda_function_name,
                                 lambda_function_role,
                                 api_gateway_api_name
                                 )

    # create api gateway resource method
    from _deployment.deploy_api_gateway import api_gateway_api_method
    api_gateway_api_method.run(ecr_repository_name,
                               aws_region,
                               aws_account_number,
                               project_path,
                               lambda_function_name,
                               lambda_function_role,
                               api_gateway_api_name
                               )

    # create api gateway resource method integration
    from _deployment.deploy_api_gateway import api_gateway_api_method_integration
    api_gateway_api_method_integration.run(ecr_repository_name,
                                           aws_region,
                                           aws_account_number,
                                           project_path,
                                           lambda_function_name,
                                           lambda_function_role,
                                           api_gateway_api_name
                                           )

    from _deployment.deploy_api_gateway import api_gateway_api_method_response
    api_gateway_api_method_response.run(ecr_repository_name,
                                        aws_region,
                                        aws_account_number,
                                        project_path,
                                        lambda_function_name,
                                        lambda_function_role,
                                        api_gateway_api_name
                                        )

    from _deployment.deploy_api_gateway import api_gateway_api_deployment
    api_gateway_api_deployment.run(ecr_repository_name,
                                   aws_region,
                                   aws_account_number,
                                   project_path,
                                   lambda_function_name,
                                   lambda_function_role,
                                   api_gateway_api_name
                                   )


def destroy_deployment_example():
    """destroy api gateway resources only

    missing: destroy lambda function, ecr repository, iam role

    Returns:

    """
    from _deployment.destroy_api_gateway import destroy_api_gateway

    ecr_repository_name = "pg_finance_trade_test4"
    aws_account_number = "717435123117"
    aws_region = "us-east-1"
    lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    lambda_function_name = f"lambda-{ecr_repository_name}"
    project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    api_gateway_api_name = "MyApi"

    destroy_api_gateway.destroy_api_gateway_resource(aws_region,
                                                     api_gateway_api_name,
                                                     lambda_function_name
                                                     )