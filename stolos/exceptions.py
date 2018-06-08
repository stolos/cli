from click.exceptions import ClickException


class NoInternetException(ClickException):
    def __init__(self):
        super(NoInternetException, self).__init__("Could not connect to server")


class CLIRequiredException(ClickException):
    def __init__(self, field_name):
        super(CLIRequiredException, self).__init__("Option %s is required" % field_name)


class NotStolosDirectoryException(ClickException):
    def __init__(self):
        super(NotStolosDirectoryException, self).__init__(
            "Current directory is not a Stolos-enabled directory."
        )


class UnknownError(ClickException):
    def __init__(self, status_code, text):
        super(UnknownError, self).__init__(
            "Unknown error.\nStatus code: {status_code}\n{text}".format(
                status_code=status_code, text=text
            )
        )


class ServerError(ClickException):
    def __init__(self, text):
        super(ServerError, self).__init__("Server error:\n{}".format(text))


class Unauthorized(ClickException):
    def __init__(self, result):
        super(Unauthorized, self).__init__("Unauthorized: {}".format(result["detail"]))


class BadRequest(ClickException):
    def __init__(self, result):
        errors = {key: ",".join(result[key]) for key in result}
        message = errors.pop("non_field_errors", "")
        errors_disp = [
            "{key}: {error}".format(key=key, error=errors[key]) for key in errors
        ]
        super(BadRequest, self).__init__(
            "Bad request: {message}\n{errors}".format(
                message=message, errors="\n".join(errors_disp)
            )
        )


class Timeout(ClickException):
    def __init__(self):
        super(Timeout, "Request timed out")


class ResourceDoesNotExist(ClickException):
    def __init__(self, result):
        super(ResourceDoesNotExist, self).__init__(
            "Resource does not exist: {}".format(result)
        )


class NotLoggedInException(ClickException):
    def __init__(self):
        super(NotLoggedInException, self).__init__(
            "You are not logged in, please run stolos login first."
        )


class ResourceAlreadyExists(ClickException):
    def __init__(self):
        super(ResourceAlreadyExists, self).__init__("Resource already exists.")
