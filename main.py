"""
poetry add pygithub
poetry add pyyaml
poetry add pandas
poetry add pygit2
poetry add gitpython

# update poetry

poetry add boto3


Advantage:

skip cloudformation stack which often cause problems and takes longer to deploy






quick start:

For lambda/api gateway deployment or stateless app:
_example.example_lambda_deploy.example_end_2_end() -> end to end to deploy code to lambda and create api gateway resource to
                                channel the traffic to the lambda function



For ec2 deployment or stateful/web app:

_example.example_deploy_website.example_website_ec2() -> end to end to deploy website to ec2 instance



Notables:

Add security:

1) deploy EC2 instance into a private subnet, need to create a NAT gateway and load balancer
2) least privilege principle for IAM role and security group
3) use AWS WAF and AWS shield to protect the website
4) add CDN to cache the static content
5)


Add parallel deployment:

1) put jobs into DAG and figure out dependencies between jobs and create aws resource in parallel to pace the deployment



Add monitoring:



Add self healing capability:
- log past errors, fits well with LLM




"""


def main(event, context):
    from _example import example_deployment_lambda
    return example_deployment_lambda.example_end_2_end()


def main1(event, context):
    # from _example import example_deployment_lambda2
    # return example_deployment_lambda2.example_end_2_end()
    from _example import example_deployment_lambda2_1
    return example_deployment_lambda2_1.example_end_2_end()
    exit(0)
    return example_deployment_lambda2.destroy_deployment_example()
    exit(0)
    from _deployment.deploy_api_gateway import deploy_api_gateway
    deploy_api_gateway.run(ecr_repository_name="pg_simple_website_streamlit-test",
                           aws_region="us-east-1",
                           aws_account_number="717435123117",
                           project_path="/Users/jianhuang/anaconda3/envs/pg_simple_login_ui/pg_simple_login_ui",
                           lambda_function_name="pg_simple_website_streamlit",
                           lambda_function_role="pg_simple_website_streamlit-role",
                           api_gateway_api_name="pg_simple_website_streamlit-test"
                           )
    exit(0)
    from _example import example_deployment_website, example_deployment_website_react
    #return example_deployment_website_react.example_website_ec2_react_destroy()
    return example_deployment_website_react.example_website_ec2_react(project_name="react-app",
                                                                      project_path="/Users/jianhuang/projects/ui/pg_website_react2/template/vertical_timeline")
    #return example_deployment_website.example_website_ec2_destroy()
    #return example_deployment_website.example_website_ec2()


def main2(event, context):
    from _example.example_describe_ec2 import describe_ec2_get_spot_request, terminate_spot_request_and_instances, terminate_instance_and_wait
    # from _example.example_describe_ec2 import status_for_spot_request
    # print(status_for_spot_request("sir-9dzpxtqk"))
    # exit(0)

    from _aws import ec2
    print(ec2.describe_key_pair("ssdsdssd"))
    exit(0)

    print(describe_ec2_get_spot_request("i-0629306d84835d625"))

    # terminate_spot_request_and_instances("sir-9dzpxtqk")
    terminate_instance_and_wait("i-0629306d84835d625-1")


def main_react_example():
    from _example import example_deployment_website, example_deployment_website_react
    # return example_deployment_website_react.example_website_ec2_react_destroy()
    return example_deployment_website_react.example_website_ec2_react(project_name="react-app",
                                                                      project_path="/Users/jianhuang/projects/ui/pg_website_react2/template/vertical_timeline")
    # return example_deployment_website.example_website_ec2_destroy()
    # return example_deployment_website.example_website_ec2()


def main_example_website():
    from _example import example_deployment_website
    return example_deployment_website.example_website_ec2()
    # return example_deployment_website.example_website_ec2_destroy()


def main_react_example():
    from _example import example_deployment_website, example_deployment_website_react
    # return example_deployment_website_react.example_website_ec2_react_destroy()
    return example_deployment_website_react.example_website_ec2_react(project_name="react-app",
                                                                      project_path="/Users/jianhuang/projects/ui/pg_website_react2/template/vertical_timeline")


if __name__ == "__main__":
    # print(main2({}, {}))
    # exit(0)
    # print(main1({}, {}))
    # print(main_react_example())
    print(main_example_website())
