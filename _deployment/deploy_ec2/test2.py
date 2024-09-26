class MyCustomError(Exception):
    """Custom exception class for specific error handling."""
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"[Error {self.error_code}]: {self.args[0]}"

class FileReadError(MyCustomError):
    """Exception raised for errors in the file reading process."""
    def __init__(self, message="File read error1111", error_code=2001):
        super().__init__(message, error_code)


class AuthenticationError(MyCustomError):
    """Exception raised for authentication errors."""
    def __init__(self, message="Authentication failed", error_code=2002):
        super().__init__(message, error_code)


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


@handle_exceptions
def read_file(file_path):
    """Reads the contents of a file."""
    with open(file_path, 'r') as file:
        content = file.read()
        print("File content successfully read.")
        return content


@handle_exceptions
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


if __name__ == "__main__":
    # content = read_file("non_existent_file.txt")
    authenticate_user("admin", "wrong_password")
    authenticate_user("wrong_username", "secret")

