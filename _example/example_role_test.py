

def example_create_iam_role():
    from _aws import iam_role

    if iam_role.check_role_exists("test-role-0001"):
        iam_role.delete_role("test-role-0001")

    response = iam_role.create_iam_role("ec2", "test-role-0001")
    print(response)
    policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"


    """
    def attach_policy_to_role(role_name: str,
                          policy_arn: str,
                          aws_region: str = "us-east-1",
                          logger: Log = None
                          ):
    
    """

    iam_role.attach_policy_to_role("test-role-0001", policy_arn)



