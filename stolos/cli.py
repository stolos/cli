import os
import os.path
import random
import shutil
import signal
import stat
import string
import subprocess
import sys
import time
from urlparse import urlparse

import click
from tabulate import tabulate

from stolos import api, config, exceptions


@click.group()
def cli():
    pass


@cli.command(help='Log in to a Stolos environment')
@click.option('--username', prompt=True, help='Your Stolos username')
@click.option('--password', prompt='Password (typing will be hidden)',
              hide_input=True, help='Your stolos password')
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


@cli.command(help='Change your Stolos password')
@click.option('--password', prompt='Current password (typing will be hidden)',
              hide_input=True, help='Your current stolos password')
@click.option('--new-password', prompt='New password (typing will be hidden)',
              hide_input=True, help='Your new stolos password',
              confirmation_prompt=True)
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
def password(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.get('stolos_url')
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    _ensure_logged_in(stolos_url)
    api.change_password(
        cnf['user'][stolos_url], kwargs['password'], kwargs['new_password'])
    click.echo('Password successfully updated.')


@cli.command(help='Run all your services and sync your files')
@click.option('-d', '--detach', default=False, is_flag=True,
              help='Sync files once and run services in the background.')
@click.option('--logs/--no-logs', default=True,
              help='Print/Do not print services logs.')
@click.option('--build', default=False, is_flag=True,
              help='Build the services before starting them.')
def up(detach, logs, build):
    _ensure_stolos_directory()
    _ensure_logged_in()
    cnf = config.get_config()
    _config_environ(cnf)
    click.echo('Syncing...')
    if _sync(False).wait() != 0:
        click.echo('There was an error with the sync')
        return
    click.echo('Okay.')
    click.echo('Starting services...')
    compose_args = ['up', '-d', '--remove-orphans']
    if build:
        compose_args.append('--build')
    if _compose(compose_args).wait() != 0:
        click.echo('There was an error with starting your services')
        return
    click.echo('Started services at {}'.format(cnf['project']['public-url']))
    if detach:
        return
    handler = InteruptHandler()
    signal.signal(signal.SIGINT, handler)
    processes = [('Syncing', _sync(True))]
    if logs:
        processes.append(('Services', _compose(['up'])))
    exit = ''
    while not exit:
        for process_name, process in processes:
            if process.poll():
                if handler.state == 0:
                    exit = '{} exited with exit code "{}"'.format(
                        process_name, process.returncode)
                    for _, p in processes:
                        if p is not process:
                            p.terminate()
                else:
                    exit = 'Terminated by user'
                break
        time.sleep(1)
    for _, p in processes:
        p.wait()
    click.echo(exit)


@cli.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True),
    help='Run Docker Compose commands in Stolos')
@click.pass_context
def compose(ctx):
    _ensure_stolos_directory()
    cnf = config.get_config()
    _config_environ(cnf)
    _compose(ctx.args).wait()


@cli.command(help='Sync your files')
@click.option('--repeat/--oneoff', default=True,
              help='If the sync should run continuously, defaults to true')
def sync(repeat):
    _ensure_stolos_directory()
    cnf = config.get_config()
    _config_environ(cnf)
    click.echo('Syncing...')
    _sync(repeat).wait()
    if not repeat:
        click.echo('Okay.')


@cli.command(help='Open the public URL of the current project')
def launch(**kwargs):
    _ensure_stolos_directory()
    cnf = config.get_config()
    public_url = 'http://{}'.format(cnf['project']['public-url'])
    click.echo('Opening {}...'.format(public_url))
    click.launch(public_url)


@cli.command(help='Get information about your current project')
def info(**kwargs):
    _ensure_stolos_directory()
    cnf = config.get_config()
    stolos_url = cnf['user']['default-api-server']
    _ensure_logged_in(stolos_url)
    headers = ['UUID', 'Stack', 'Public URL']
    projects = [
        (p['uuid'], p['stack']['slug'], p['routing_config']['domain'])
        for p in [api.projects_retrieve(
            cnf['user'][stolos_url], cnf['project']['uuid'])]
    ]
    click.echo(tabulate(projects, headers=headers))


@cli.group(help='Manage your Stolos projects')
def projects():
    pass


@projects.command(help='List your projects')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
def list(**kwargs):
    _ensure_logged_in(kwargs['stolos_url'])
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
@click.option('--public-url',
              help='The public URL of your project, defaults to random hex')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.argument('stack')
@click.argument('project_directory')
def create(**kwargs):
    _ensure_logged_in(kwargs['stolos_url'])
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    project_directory = kwargs.pop('project_directory')
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    if not kwargs['public_url']:
        company, stack_name = kwargs['stack'].split('/')
        fmt_str = '{company}-{stack_name}-{username}-{hex}.{server}'
        kwargs['public_url'] = fmt_str.format(
            company=company, stack_name=stack_name,
            username=cnf['user'][stolos_url]['username'],
            hex=''.join(
                [random.choice(string.ascii_lowercase) for _ in range(6)]),
            server=stolos_url,
        )
        click.echo(
            'Assigning random public URL "{}"'.format(kwargs['public_url']))
    click.echo('Creating project "{}"...'.format(project_directory), nl=False)
    project = api.projects_create(cnf['user'][stolos_url], **kwargs)
    if not os.path.exists(project_directory):
        os.makedirs(project_directory)
    os.chdir(project_directory)
    _initialize_project(stolos_url, project)
    click.echo('\t\tOk.')
    click.echo(
        ('Your project is ready! Change directory with "cd {0}" and run '
         '"stolos up" to launch it!').format(project_directory))


@projects.command(
    help='Connect the current directory to an existing Stolos project')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.argument('project_uuid')
def connect(**kwargs):
    _ensure_logged_in(kwargs['stolos_url'])
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    project_uuid = kwargs.pop('project_uuid')
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    click.echo('Connecting to project "{}"...'.format(project_uuid), nl=False)
    project = api.projects_retrieve(cnf['user'][stolos_url], project_uuid)
    _initialize_project(stolos_url, project)
    click.echo('\t\tOkay.')
    click.echo('Your project is ready! Run "stolos up" to launch it!')


@projects.command(help='Delete a Stolos project')
@click.option('--stolos-url',
              help='The URL of the Stolos server to use, if not the default')
@click.argument('project-uuid', required=False)
def delete(**kwargs):
    _ensure_logged_in(kwargs['stolos_url'])
    project_uuid = kwargs.pop('project_uuid')
    if not project_uuid and not _ensure_stolos_directory(base_directory=None,
                                                         raise_exc=False):
        raise exceptions.CLIRequiredException('project-uuid')
    cnf = config.get_config()
    stolos_url = kwargs.pop('stolos_url')
    remove_directory = False
    if not project_uuid:
        project_uuid = cnf['project']['uuid']
        remove_directory = True
    if not stolos_url:
        stolos_url = cnf['user']['default-api-server']
    click.echo('Deleting project "{}"...'.format(project_uuid), nl=False)
    api.projects_remove(cnf['user'][stolos_url], project_uuid)
    click.echo('\t\tOkay.')
    if remove_directory:
        click.echo('Clearing up Docker resources...')
        # Also, remove any leftover project resources.
        _config_environ(cnf)
        _compose(['down']).wait()
        _deinitialize_project()
        click.echo('Okay.')


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
    with open('.stolos/default.prf', 'w+') as default_profile:
        default_profile.write(
            """
# Default unison profile for UNIX systems
include common

"""
        )
    with open('.stolos/win.prf', 'w+') as windows_profile:
        windows_profile.write(
            """
# Unison profile for Windows systems
perms = 0

include common

"""
        )
    with open('.stolos/common', 'w+') as common:
        common.write(
            string.Template(
                """
# Roots of the synchronization
root = .
root = ssh://stolos@${STOLOS_SERVER}//mnt/stolos/${STOLOS_PROJECT_ID}

sshargs = -i .stolos/id_rsa

ui = text
addversionno = true
prefer = newer
fastcheck = true
ignore = Path .stolos
silent = true

# Enable this option and set it to 'all' or 'verbose' for debugging
# debug = verbose

"""
            ).substitute(
                STOLOS_PROJECT_ID=project['uuid'],
                STOLOS_SERVER=project['server']['host']
            )
        )


def _deinitialize_project():
    """
    Deinitialize a Stolos project, deleting the `.stolos` directory.
    """
    if os.path.isdir('.stolos'):
        shutil.rmtree('.stolos', ignore_errors=True)


def _config_environ(cnf):
    """
    Configures the environment with any needed environment variables for compose
    and Unison.
    """
    os.environ.update({
        'COMPOSE_PROJECT_NAME': cnf['project']['uuid'],
        'COMPOSE_FILE': 'docker-compose.yaml',
        'DOCKER_HOST': 'tcp://{}:2376'.format(cnf['server']['host']),
        'DOCKER_CERT_PATH': '.stolos',
        'DOCKER_TLS_VERIFY': '1',
        'STOLOS_REMOTE_DIR': '/mnt/stolos/{}/'.format(cnf['project']['uuid']),
        'UNISON': '.stolos',
    })


def _compose(args):
    """
    Run Docker Compose, with the given arguments. These arguments should be in
    array form `['-d', '--build']`, not as a single string.
    """
    p = subprocess.Popen(
        ['docker-compose'] + args,
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=sys.stdin)
    return p


def _sync(repeat):
    """
    Starts a proejct sync using Unison. Takes an extra parameter, which makes
    the synchronization repeat using Unison `-repeat` or not.
    """
    args = []
    if repeat:
        args.insert(0, '2')
        args.insert(0, '-repeat')
    else:
        args.insert(0, 'false')
        args.insert(0, '-fastcheck')
    if _is_windows():
        args.insert(0, 'win')
    p = subprocess.Popen(
        ['unison'] + args,
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=sys.stdin)
    return p


def _ensure_stolos_directory(base_directory=None, raise_exc=True):
    """
    Ensures the existance of a Stolos directory. Either raises an exception, or
    returns the result.

    If the current directory is not a Stolos directory, recursively traverses
    towards the parent until it finds one.
    """
    if base_directory is None:
        base_directory = os.getcwd()
    parent = os.path.abspath(os.path.join(base_directory, os.pardir))
    if os.path.exists(os.path.join(base_directory, '.stolos')):
        os.chdir(base_directory)
        return True
    if parent == base_directory:
        if raise_exc:
            raise exceptions.NotStolosDirectoryException()
        return False
    return _ensure_stolos_directory(parent, raise_exc)


def _is_windows():
    """
    Detects the current platform, returning True if running in Windows or
    Cygwin.
    """
    return {
        'win32': True,
        'cygwin': True,
    }.get(sys.platform, False)


def _ensure_logged_in(stolos_url=None):
    """
    Ensures the user is logged in, at the given `stolos_url` Stolos server.
    Raises an exception if not.
    """
    cnf = config.get_config()
    if 'user' not in cnf:
        raise exceptions.NotLoggedInException()
    if 'default-api-server' not in cnf['user'] and not stolos_url:
        raise exceptions.NotLoggedInException()
    stolos_url = stolos_url or cnf['user']['default-api-server']
    if stolos_url not in cnf['user']:
        raise exceptions.NotLoggedInException()



class InteruptHandler(object):
    """
    Helper class, for handling incoming signals and propagating them.
    """
    def __init__(self):
        self.state = 0

    def __call__(self, *args, **kwargs):
        self.state = self.state + 1
