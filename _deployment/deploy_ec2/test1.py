class MyCustomError(Exception):
    """Custom exception class for specific error handling."""
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"[Error {self.error_code}]: {self.args[0]}"

class FileReadError(MyCustomError):
    """Exception raised for errors in the file reading process."""
    def __init__(self, message="File read error", error_code=2001):
        super().__init__(message, error_code)

class AuthenticationError(MyCustomError):
    """Exception raised for authentication errors."""
    def __init__(self, message="Authentication failed", error_code=2002):
        super().__init__(message, error_code)


def read_file(file_path):
    """Reads the contents of a file."""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            print("File content successfully read.")
            return content
    except FileNotFoundError:
        raise FileReadError("File not found 111", 2001)
    except IOError:
        raise FileReadError("Error reading file", 2001)


def authenticate_user(username, password):
    """Authenticates a user based on username and password."""
    stored_username = "admin"
    stored_password = "secret"

    if username != stored_username:
        raise AuthenticationError("Invalid username", 2002)
    if password != stored_password:
        raise AuthenticationError("Invalid password", 2002)

    print("User authenticated successfully.")
    return True






def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            raise FileReadError("File not found 1111", 2001)
        except IOError:
            raise FileReadError("Error reading file", 2001)
        except AuthenticationError as e:
            raise FileReadError("Error reading file", 2001)
        except MyCustomError as e:
            print(e)
    return wrapper


def create_launch_template(template_name, image_id, instance_type, key_name, security_group_ids, user_data=None):
    # Initialize a session using Amazon EC2
    ec2 = boto3.client('ec2')

    try:
        # Create the launch template
        response = ec2.create_launch_template(
            LaunchTemplateName=template_name,
            LaunchTemplateData={
                'ImageId': image_id,
                'InstanceType': instance_type,
                'KeyName': key_name,
                'SecurityGroupIds': security_group_ids,
                'UserData': user_data
            }
        )

        print("Launch Template Created Successfully")
        return response

    except NoCredentialsError:
        print("Error: No AWS credentials found.")
    except PartialCredentialsError:
        print("Error: Incomplete AWS credentials found.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'InvalidLaunchTemplateName.AlreadyExistsException':
            print("Error: Launch Template with this name already exists.")
        else:
            print(f"Unexpected error: {e}")





if __name__ == "__main__":
    # content = read_file("non_existent_file.txt")
    # authenticate_user("admin", "wrong_password")
    authenticate_user("wrong_username", "secret")

