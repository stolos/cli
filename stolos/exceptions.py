from click.exceptions import ClickException


class NoInternetException(ClickException):
    def __init__(self):
        super(NoInternetException, self).__init__(
            'Could not connect to server')


class CLIRequiredException(ClickException):
    def __init__(self, field_name):
        super(CLIRequiredException, self).__init__(
            'Option %s is required' % field_name)
