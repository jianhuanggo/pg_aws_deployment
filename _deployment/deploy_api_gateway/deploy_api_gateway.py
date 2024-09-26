from time import sleep
from _common import _common as _common_
from _util import _util_common as _util_common_
import boto3


_WAIT_TIME_ = 10


@_common_.aws_client_handle_exceptions()
def aws_client(service_name: str, aws_region: str):
    return boto3.client(service_name, region_name=aws_region)


@_common_.aws_client_handle_exceptions()
def run(ecr_repository_name: str,
        aws_account_number: str = None,
        project_path: str = None,
        lambda_function_name: str = None,
        lambda_function_role: str = None,
        api_gateway_api_name: str = None,
        api_method: str = "GET",
        aws_region: str = "us-east-1"
        ) -> None:

    # ecr_repository_name = "pg_finance_trade_test8"
    # aws_account_number = "717435123117"
    # aws_region = "us-east-1"
    # lambda_function_role = f"role-auto-deployment-lambda-{_util_common_.get_random_string(6)}"
    # lambda_function_name = f"lambda-{ecr_repository_name}"
    # project_path = "/Users/jianhuang/anaconda3/envs/pg_finance_trade_1/pg_finance_trade_1"
    # api_gateway_api_name = "test_test_api"

    from _aws import _api_gateway

    api_gateway_api_id = _api_gateway.api_gateway_create_by_name(api_gateway_name=api_gateway_api_name,
                                                                 aws_region=aws_region)

    # obtain the API Gateway root resource ID
    api_gateway_root_res_id = _api_gateway.api_gateway_get_root_resource(api_gateway_api_id=api_gateway_api_id,
                                                                         aws_region=aws_region)

    # obtain the api gateway resource id
    resource_id = _api_gateway.get_api_gateway_resource_id(api_gateway_api_id=api_gateway_api_id,
                                                           lambda_function_name=lambda_function_name,
                                                           aws_region=aws_region)

    _common_.info_logger(f"resource_id: {resource_id}, api_gateway_api_id: {api_gateway_api_id} api_gateway_root_res_id: {api_gateway_root_res_id}")

    if resource_id:
        if _api_gateway.delete_api_gateway_resource(api_gateway_api_id=api_gateway_api_id,
                                                    resource_id=resource_id,
                                                    aws_region=aws_region):
            # Wait before creating the new resource to ensure deletion has propagated
            sleep(_WAIT_TIME_)

    # Create the new resource
    resource_id = _api_gateway.create_api_gateway_resource(api_gateway_api_id=api_gateway_api_id,
                                                           api_gateway_root_res_id=api_gateway_root_res_id,
                                                           lambda_function_name=lambda_function_name,
                                                           aws_region=aws_region
                                                           )
    sleep(_WAIT_TIME_)

    # create api gateway resource method

    api_gateway_method = _api_gateway.get_api_gateway_method(api_gateway_api_id=api_gateway_api_id,
                                                             resource_id=resource_id,
                                                             http_method=api_method,
                                                             aws_region=aws_region)

    if api_gateway_method:
            # Resource exists, delete it
            if _api_gateway.delete_api_gateway_method(api_gateway_api_id=api_gateway_api_id,
                                                      resource_id=resource_id,
                                                      http_method=api_method,
                                                      aws_region=aws_region):
                # Wait before creating the new resource to ensure deletion has propagated
                sleep(_WAIT_TIME_)

    # Create the new resource
    _api_gateway.create_api_gateway_method(api_gateway_api_id=api_gateway_api_id,
                                           resource_id=resource_id,
                                           http_method=api_method,
                                           aws_region=aws_region)

    sleep(_WAIT_TIME_)

    # create api gateway resource method integration
    response = _api_gateway.get_api_gateway_integration(api_gateway_api_id=api_gateway_api_id,
                                                        resource_id=resource_id,
                                                        http_method=api_method,
                                                        aws_region=aws_region, )

    if response:
        # Resource exists, delete it
        if _api_gateway.delete_api_gateway_integration(api_gateway_api_id=api_gateway_api_id,
                                                       resource_id=resource_id,
                                                       http_method=api_method,
                                                       aws_region=aws_region):

            # Wait before creating the new resource to ensure deletion has propagated
            sleep(_WAIT_TIME_)

    # Create the new resource
    response = _api_gateway.create_api_gateway_integration(api_gateway_api_id=api_gateway_api_id,
                                                           resource_id= resource_id,
                                                           http_method=api_method,
                                                           aws_account_number=aws_account_number,
                                                           lambda_function_name=lambda_function_name,
                                                           aws_region=aws_region
                                                           )

    sleep(_WAIT_TIME_)

    # create api gateway resource method response
    response = _api_gateway.get_api_gateway_method_response(api_gateway_api_id=api_gateway_api_id,
                                                            resource_id=resource_id,
                                                            http_method=api_method,
                                                            status_code="200",
                                                            aws_region=aws_region)



    if response:
        _api_gateway.delete_api_gateway_method_response(api_gateway_api_id=api_gateway_api_id,
                                                        resource_id=resource_id,
                                                        http_method=api_method,
                                                        status_code="200",
                                                        aws_region=aws_region)

    response = _api_gateway.create_api_gateway_method_response(api_gateway_api_id=api_gateway_api_id,
                                                               resource_id=resource_id,
                                                               http_method=api_method,
                                                               status_code="200",
                                                               aws_region=aws_region
                                                               )
    sleep(_WAIT_TIME_)

    # create api gateway deployment and deploy to stage
    stage_name = "prod"
    response = _api_gateway.create_api_gateway_deployment(api_gateway_api_id=api_gateway_api_id,
                                                          api_stage_name=stage_name,
                                                          aws_region=aws_region)

    print(f"https://{api_gateway_api_id}.execute-api.{aws_region}.amazonaws.com/{stage_name}/{lambda_function_name}")

    sleep(_WAIT_TIME_)


# @_common_.aws_client_handle_exceptions()
# def delete(ecr_repository_name: str,
#            aws_account_number: str = None,
#            project_path: str = None,
#            lambda_function_name: str = None,
#            lambda_function_role: str = None,
#            api_gateway_api_name: str = None,
#            aws_region: str = "us-east-1"
#            ) -> bool:
#
#     from _aws import _api_gateway
#
#     api_gateway_api_id = _api_gateway.api_gateway_get_name(api_gateway_name=api_gateway_api_name,
#                                                            aws_region=aws_region)
#
#     # obtain the API Gateway root resource ID
#     api_gateway_root_res_id = _api_gateway.api_gateway_get_root_resource(api_gateway_api_id=api_gateway_api_id,
#                                                                          aws_region=aws_region)
#
#     # obtain the api gateway resource id
#     resource_id = _api_gateway.get_api_gateway_resource_id(api_gateway_api_id=api_gateway_api_id,
#                                                            lambda_function_name=lambda_function_name,
#                                                            aws_region=aws_region)
#
#     _common_.info_logger(f"resource_id: {resource_id}, api_gateway_api_id: {api_gateway_api_id} api_gateway_root_res_id: {api_gateway_root_res_id}")
#
#     if resource_id:
#         if _api_gateway.delete_api_gateway_resource(api_gateway_api_id=api_gateway_api_id,
#                                                     resource_id=resource_id,
#                                                     aws_region=aws_region):
#             # Wait before creating the new resource to ensure deletion has propagated
#             sleep(_WAIT_TIME_)
#
#     response = _api_gateway.api_gateway_delete_by_name(api_gateway_name=api_gateway_api_name,
#                                                        aws_region=aws_region)
#     print(response)
#     return response










