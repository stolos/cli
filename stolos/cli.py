import os
import os.path
import shutil
import stat
from urlparse import urlparse

import click

from tabulate import tabulate

from stolos import api, config, exceptions


@click.group()
def cli():
    pass


@cli.command(help='Log in to a Stolos environment')
@click.option('--username', prompt=True, help='Your Stolos username')
@click.option('--password', prompt=True, hide_input=True,
              help='Your stolos password')
@click.option('--stolos-url', default='https://api.stolos.io',
              help='The URL of the Stolos server to use')
def login(**kwargs):
    host = urlparse(kwargs['stolos_url']).hostname
    config.update_user_config({
        'user': {
            host: {
                'token': api.authenticate(**kwargs)['auth_token'],
                'username': kwargs['username'],
                'host': kwargs['stolos_url'],
            },
        },
    })
    if 'default-api-server' not in config.get_user_config()['user']:
        config.update_user_config({
            'user': {
                'default-api-server': host,
            },
        })
    click.echo('Authentication successful.')


@cli.group(help='Manage your Stolos projects')
def projects():
    pass


@projects.command(help='List your projects')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
def list(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.get('stolos_url')
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    headers = ['UUID', 'Stack', 'Public URL']
    projects = [
        (p['uuid'], p['stack']['slug'], p['routing_config']['domain'])
        for p in api.projects_list(cnf['user'][stolos_url])
    ]
    click.echo(tabulate(projects, headers=headers))


@projects.command(help='Create a new Stolos project')
@click.option('--stack', help='[Required] The Stack to use for your project')
@click.option('--public-url', help='[Required] The public URL of your project')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.argument('project_name')
def create(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    project_name = kwargs.pop('project_name')
    if os.path.exists(project_name):
        raise click.ClickException(
            'Directory "{}" already exists'.format(project_name))
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    for option in ['public_url', 'stack']:
        if not kwargs[option]:
            raise exceptions.CLIRequiredException(option)
    click.echo('Creating project "{}"...'.format(project_name), nl=False)
    project = api.projects_create(cnf['user'][stolos_url], **kwargs)
    os.makedirs(project_name)
    os.chdir(project_name)
    _initialize_project(stolos_url, project)
    click.echo('\t\tOk.')
    click.echo(
        ('Project "{0}" is ready! Change directory with "cd {0}" and run '
         '"stolos up" to launch it!').format(project_name))


@projects.command(help='Initialize an existing Stolos project')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.argument('project_uuid')
def init(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    project_uuid = kwargs.pop('project_uuid')
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    click.echo('Initializing project "{}"...'.format(project_uuid), nl=False)
    project = api.projects_retrieve(cnf['user'][stolos_url], project_uuid)
    _initialize_project(stolos_url, project)
    click.echo('\t\tOk.')
    click.echo('Your project is initialized! Run "stolos up" to launch it!')


@projects.command(help='Delete a Stolos project')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.option('--project-uuid',
              help='The UUID of the project to delete, defaults current one')
def delete(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    project_uuid = kwargs.pop('project_uuid')
    remove_directory = False
    if not project_uuid:
        project_uuid = cnf['project']['uuid']
        remove_directory = True
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    if not project_uuid:
        raise exceptions.CLIRequiredException('project-uuid')
    click.echo('Deleting project "{}"...'.format(project_uuid), nl=False)
    api.projects_remove(cnf['user'][stolos_url], project_uuid)
    click.echo('\t\tOk.')
    if remove_directory:
        _deinitialize_project()


def _initialize_project(stolos_url, project):
    """
    Initialize a Stolos project with the needed files, using the response from
    the server.
    """
    config.update_project_config({
        'project': {
            'uuid': project['uuid'],
            'stack': project['stack']['slug'],
            'public-url': project['routing_config']['domain'],
        },
        'user': {
            'default-api-server': stolos_url,
        },
        'server': {
            'host': project['server']['host'],
        },
    })
    with open('.stolos/ca.pem', 'w+') as ca_pem:
        ca_pem.write(project['server']['docker_ca_pem'])
        os.chmod('.stolos/ca.pem', 0600)
    with open('.stolos/cert.pem', 'w+') as cert_pem:
        cert_pem.write(project['server']['docker_cert_pem'])
        os.chmod('.stolos/cert.pem', 0600)
    with open('.stolos/key.pem', 'w+') as key_pem:
        key_pem.write(project['server']['docker_key_pem'])
        os.chmod('.stolos/key.pem', 0600)
    with open('.stolos/id_rsa', 'w+') as id_rsa:
        id_rsa.write(project['server']['unison_id_rsa'])
        os.chmod('.stolos/id_rsa', 0600)
    with open('docker-compose.yaml', 'w+') as docker_compose:
        docker_compose.write(project['stack']['docker_compose_file'])


def _deinitialize_project():
    """
    Deinitialize a Stolos project, deleting the `.stolos` directory.
    """
    if os.path.isdir('.stolos'):
        shutil.rmtree('.stolos', ignore_errors=True)
