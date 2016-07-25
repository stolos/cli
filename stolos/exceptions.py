from click.exceptions import ClickException

class CLIRequiredException(ClickException):
    def __init__(self, field_name):
        super(CLIRequiredException, self).__init__(
            'Option %s is required' % field_name)
