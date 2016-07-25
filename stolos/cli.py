import os
import os.path

import click

from stolos import config
from stolos import exceptions


@click.group()
def cli():
    pass


@cli.command(help='Initialize a stolos project.')
@click.argument('directory')
@click.option('--stack',
              help='[Required] The stack to use.')
def init(**kwargs):
    if kwargs['stack'] is None:
        raise exceptions.CLIRequiredException('stack')
    pass
