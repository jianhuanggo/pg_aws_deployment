from time import sleep
from _common import _common as _common_

_WAIT_TIME_ = 4


def destroy_api_gateway_resource(api_gateway_api_name: str,
                                 lambda_function_name: str,
                                 aws_region: str = "us-east-1"
                                 ) -> bool:


    # obtain the api gateway api id
    from _aws import _api_gateway

    # obtain the api gateway
    api_gateway_api_id = _api_gateway.api_gateway_get_name(api_gateway_name=api_gateway_api_name,  aws_region=aws_region)
    api_gateway_root_res_id = resource_id = None

    # obtain the API Gateway root resource ID
    if api_gateway_api_id:
        api_gateway_root_res_id = _api_gateway.api_gateway_get_root_resource(api_gateway_api_id=api_gateway_api_id,
                                                                             aws_region=aws_region)

    # obtain the api gateway resource id
        resource_id = _api_gateway.get_api_gateway_resource_id(api_gateway_api_id=api_gateway_api_id,
                                                               lambda_function_name=lambda_function_name,
                                                               aws_region=aws_region)

    http_method = "GET"
    status_code = "200"

    _common_.info_logger(f"resource_id: {resource_id}, api_gateway_api_id: {api_gateway_api_id} api_gateway_root_res_id: {api_gateway_root_res_id}")

    if not (api_gateway_api_id and api_gateway_root_res_id and resource_id): return False

    # destroy the api gateway resource method response if exists

    response = _api_gateway.delete_api_gateway_method_response(api_gateway_api_id=api_gateway_api_id,
                                                               resource_id=resource_id,
                                                               http_method="http_method",
                                                               status_code=status_code,
                                                               aws_region=aws_region)

    sleep(_WAIT_TIME_)

    response = _api_gateway.delete_api_gateway_integration(api_gateway_api_id=api_gateway_api_id,
                                                           resource_id=resource_id,
                                                           http_method="http_method",
                                                           aws_region=aws_region)

    sleep(_WAIT_TIME_)

    response = _api_gateway.delete_api_gateway_method(api_gateway_api_id=api_gateway_api_id,
                                                      resource_id=resource_id,
                                                      http_method="http_method",
                                                      aws_region=aws_region)

    sleep(_WAIT_TIME_)

    response = _api_gateway.delete_api_gateway_resource(api_gateway_api_id=api_gateway_api_id,
                                                        resource_id=resource_id)

    sleep(_WAIT_TIME_)

    response = _api_gateway.api_gateway_delete_by_name(api_gateway_name=api_gateway_api_name,
                                                       aws_region=aws_region)


    return True
