import os
import platform
import random
import re
import shutil
import signal
import stat
import string
import subprocess
import sys
import time

import click
import yaml
from six import iteritems
from tabulate import tabulate

from six.moves import urlparse
from stolos import VERSION, api, config, exceptions, shell


@click.group()
def cli():
    pass


def _get_hostname(url):
    """Strip url from protocol and trailing slash, in order to use it as config
    key
    """
    url = api._ensure_protocol(url)
    return urlparse(url).hostname


@cli.command(help="Print the version of the CLI")
def version():
    click.echo(VERSION)


@cli.command(help="Log in to a Stolos environment")
@click.option("--username", prompt=True, help="Your Stolos username")
@click.option(
    "--password",
    prompt="Password (typing will be hidden)",
    hide_input=True,
    help="Your stolos password",
)
@click.option(
    "--stolos-url",
    default="https://api.stolos.io",
    help="The URL of the Stolos server to use",
)
@click.pass_context
def login(ctx, **kwargs):
    stolos_url = api._ensure_protocol(kwargs["stolos_url"])
    host = _get_hostname(stolos_url)
    cnf = config.get_user_config()
    identity_file = cnf.get("user", {}).get(host, {}).get("identity-file")
    auth_response = api.authenticate(**kwargs)
    new_config = {
        "token": auth_response["auth_token"],
        "key-pem": auth_response["docker_key_pem"],
        "cert-pem": auth_response["docker_cert_pem"],
        "username": kwargs["username"],
        "host": stolos_url,
    }
    if identity_file:
        new_config["identity-file"] = identity_file
    config.update_user_config({"user": {host: new_config}})
    if "default-api-server" not in config.get_user_config()["user"]:
        config.update_user_config({"user": {"default-api-server": host}})
    click.echo("Authentication successful.")
    if identity_file is not None:
        return
    home = os.path.expanduser("~")
    key_path = os.path.join(home, ".ssh", "id_rsa")
    public_key_path = key_path + ".pub"
    if os.path.exists(key_path) and os.path.exists(public_key_path):
        ctx.invoke(upload, public_key_path=public_key_path, stolos_url=host)
    else:
        click.echo(
            "No ssh key was found. To enable stolos syncing, upload a public ssh key using the following command:"
        )
        click.secho("\tstolos keys upload [PUBLIC_KEY_PATH]\n", bold=True)


@cli.command(help="Change your Stolos password")
@click.option(
    "--password",
    prompt="Current password (typing will be hidden)",
    hide_input=True,
    help="Your current stolos password",
)
@click.option(
    "--new-password",
    prompt="New password (typing will be hidden)",
    hide_input=True,
    help="Your new stolos password",
    confirmation_prompt=True,
)
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
def password(**kwargs):
    cnf = config.get_config()
    stolos_url = kwargs.get("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    _ensure_logged_in(stolos_url)
    api.change_password(
        cnf["user"][_get_hostname(stolos_url)],
        kwargs["password"],
        kwargs["new_password"],
    )
    click.echo("Password successfully updated.")


@cli.command(help="Run all your services and sync your files")
@click.option(
    "-d",
    "--detach",
    default=False,
    is_flag=True,
    help="Sync files once and run services in the background.",
)
@click.option(
    "--logs/--no-logs", default=True, help="Print/Do not print services logs."
)
@click.option(
    "--build",
    default=False,
    is_flag=True,
    help="Build service images before starting service containers.",
)
def up(detach, logs, build):
    _ensure_stolos_directory()
    _ensure_logged_in()
    cnf = config.get_config()
    _config_environ(cnf)
    click.echo("Syncing...")
    if _sync(False).wait() != 0:
        click.echo("There was an error with the sync")
        return
    click.echo("Okay.")
    click.echo("Starting services...")
    compose_args = ["up", "-d", "--remove-orphans"]
    if build:
        compose_args.append("--build")
    if _compose(compose_args).wait() != 0:
        click.echo("There was an error with starting your services")
        return
    click.echo("Started services at {}".format(cnf["project"]["public-url"]))
    if detach:
        return
    handler = InteruptHandler()
    signal.signal(signal.SIGINT, handler)
    processes = [("Syncing", _sync(True))]
    if logs:
        compose_args = ["logs", "--tail=20", "-f"]
        if _is_windows():
            compose_args.append("--no-color")
        processes.append(("Services", _compose(compose_args)))
    exit = ""
    while not exit:
        for process_name, process in processes:
            if process.poll():
                if handler.state == 0:
                    exit = '{} exited with exit code "{}"'.format(
                        process_name, process.returncode
                    )
                    for _, p in processes:
                        if p is not process:
                            p.terminate()
                else:
                    exit = "Terminated by user"
                    break
        time.sleep(1)
    for _, p in processes:
        p.wait()
    click.echo(exit)


@cli.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
    help="Run Docker Compose commands in Stolos",
)
@click.pass_context
def compose(ctx):
    _ensure_stolos_directory()
    cnf = config.get_config()
    _config_environ(cnf)
    _compose(ctx.args).wait()


@cli.command(help="Sync your files")
@click.option(
    "--repeat/--oneoff",
    default=True,
    help="If the sync should run continuously, defaults to true",
)
def sync(repeat):
    _ensure_stolos_directory()
    cnf = config.get_config()
    _config_environ(cnf)
    click.echo("Syncing...")
    _sync(repeat).wait()
    if not repeat:
        click.echo("Okay.")


@cli.command(
    name="open",
    help="Open the public URL of the current project. Optionally provide service and port",
)
@click.argument("service", required=False)
@click.argument("port", required=False)
def launch(**kwargs):
    _ensure_stolos_directory()
    cnf = config.get_config()
    public_url = _get_url_for_service_port(cnf, **kwargs)
    click.echo("Opening http://{}...".format(public_url))
    click.launch("http://{}".format(public_url))


@cli.command(help="Get information about your current project")
def info(**kwargs):
    _ensure_stolos_directory()
    cnf = config.get_config()
    stolos_url = cnf["user"]["default-api-server"]
    _ensure_logged_in(stolos_url)
    headers = ["UUID", "Stack", "Public URL"]
    project = api.projects_retrieve(
        cnf["user"][_get_hostname(stolos_url)], cnf["project"]["uuid"]
    )
    uuid = project["uuid"]
    stack = "-"
    if project["stack"]:
        stack = project["stack"]["slug"]
    domain = project["routing_config"]["domain"]
    projects = [(uuid, stack, domain)]
    click.echo(tabulate(projects, headers=headers))


@cli.command(
    help="Display the commands to set up the environment for the " "Docker client"
)
@click.option("--shell", help="Give the shell of your choice")
def env(**kwargs):
    _ensure_stolos_directory()
    cnf = config.get_config()
    stolos_url = cnf["user"]["default-api-server"]
    _ensure_logged_in(stolos_url)
    env_dict = _get_environ(cnf)
    command = "stolos env"
    if kwargs["shell"]:
        command = "stolos env --shell={}".format(kwargs["shell"])
    shell.print_env_eval(command, kwargs["shell"], env_dict)


@cli.group(help="Manage your Stolos stacks")
def stacks():
    pass


@stacks.command(name="list", help="List your stacks")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
def stacks_list(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    cnf = config.get_config()
    stolos_url = kwargs.get("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    headers = ["Stack name", "Slug", "Description"]
    stacks = [
        (stack["name"], stack["slug"], stack.get("description"))
        for stack in api.stacks_list(cnf["user"][_get_hostname(stolos_url)])
    ]
    click.echo(tabulate(stacks, headers=headers))


@cli.group(help="Manage your Stolos projects")
def projects():
    pass


@projects.command(name="list", help="List your projects")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
def projects_list(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    cnf = config.get_config()
    stolos_url = kwargs.get("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    headers = ["UUID", "Stack", "Public URL"]
    projects = []
    for project in api.projects_list(cnf["user"][_get_hostname(stolos_url)]):
        uuid = project["uuid"]
        stack = "-"
        if project["stack"]:
            stack = project["stack"]["slug"]
        domain = project["routing_config"]["domain"]
        projects.append((uuid, stack, domain))
    click.echo(tabulate(projects, headers=headers))


@projects.command(help="Create a new Stolos project")
@click.option(
    "--public-url", help="The public URL of your project, defaults to random hex"
)
@click.option(
    "--subdomains/--no-subdomains",
    default=False,
    help="If this project should use subdomains for services, defaults to false",
)
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.option("--stack", help="The stack to use for this project, defaults to no stack")
@click.argument("project_directory")
def create(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    cnf = config.get_config()
    stolos_url = kwargs.pop("stolos_url")
    project_directory = kwargs.pop("project_directory")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    if not kwargs["public_url"]:
        if kwargs["stack"]:
            company, stack_name = kwargs["stack"].split("/")
            fmt_str = "{company}-{stack_name}-{username}-{hex}.{server}"
            kwargs["public_url"] = fmt_str.format(
                company=company,
                stack_name=stack_name,
                username=cnf["user"][_get_hostname(stolos_url)]["username"],
                hex="".join([random.choice(string.ascii_lowercase) for _ in range(6)]),
                server=stolos_url,
            )
        else:
            fmt_str = "{username}-{hex}.{server}"
            kwargs["public_url"] = fmt_str.format(
                username=cnf["user"][_get_hostname(stolos_url)]["username"],
                hex="".join([random.choice(string.ascii_lowercase) for _ in range(6)]),
                server=stolos_url,
            )
        click.echo('Assigning random public URL "{}"'.format(kwargs["public_url"]))
    click.echo('Creating project "{}"...'.format(project_directory), nl=False)
    project = api.projects_create(cnf["user"][_get_hostname(stolos_url)], **kwargs)
    if not os.path.exists(project_directory):
        os.makedirs(project_directory)
    os.chdir(project_directory)
    _initialize_project(stolos_url, project)
    click.echo("\t\tOk.")
    _initialize_services()
    if project_directory == ".":
        click.echo('Your project is ready! Run "stolos up" to launch it!')
        return
    click.echo(
        (
            'Your project is ready! Change directory with "cd {0}" and run '
            '"stolos up" to launch it!'
        ).format(
            project_directory
        )
    )


@projects.command(help="Connect the current directory to an existing Stolos project")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.argument("project_uuid")
def connect(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    cnf = config.get_config()
    stolos_url = kwargs.pop("stolos_url")
    project_uuid = kwargs.pop("project_uuid")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    click.echo('Connecting to project "{}"...'.format(project_uuid), nl=False)
    project = api.projects_retrieve(
        cnf["user"][_get_hostname(stolos_url)], project_uuid
    )
    _initialize_project(stolos_url, project)
    _initialize_services()
    click.echo("\t\tOkay.")
    click.echo('Your project is ready! Run "stolos up" to launch it!')


@projects.command(help="Delete a Stolos project")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.argument("project-uuid", required=False)
def delete(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    project_uuid = kwargs.pop("project_uuid")
    if (
        not project_uuid
        and not _ensure_stolos_directory(base_directory=None, raise_exc=False)
    ):
        raise exceptions.CLIRequiredException("project-uuid")
    cnf = config.get_config()
    stolos_url = kwargs.pop("stolos_url")
    remove_directory = False
    if not project_uuid:
        project_uuid = cnf["project"]["uuid"]
        remove_directory = True
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    click.echo('Deleting project "{}"...'.format(project_uuid), nl=False)
    api.projects_remove(cnf["user"][_get_hostname(stolos_url)], project_uuid)
    click.echo("\t\tOkay.")
    if remove_directory:
        click.echo("Clearing up Docker resources...")
        # Also, remove any leftover project resources.
        _config_environ(cnf)
        _compose(["down"]).wait()
        _deinitialize_project()
        click.echo("Okay.")


@cli.group(help="Manage your Stolos public keys")
def keys():
    pass


@keys.command(help="Upload an SSH public key to Stolos")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.option("--name", help="The name of this key, default to this machine's hostname")
@click.argument(
    "public_key_path", required=False, type=click.Path(), default="~/.ssh/id_rsa.pub"
)
def upload(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    public_key_path = kwargs["public_key_path"]
    if not public_key_path.endswith(".pub"):
        click.confirm(
            (
                "Key {} appears to be a private, not a public key. "
                "Are you sure you want to continue?"
            ).format(
                public_key_path
            ),
            abort=True,
        )
    expanded_public_key_path = os.path.expanduser(public_key_path)
    if not os.path.exists(expanded_public_key_path):
        raise click.exceptions.ClickException(
            "File {} does not exist".format(public_key_path)
        )

    cnf = config.get_config()
    stolos_url = kwargs.pop("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]

    name = kwargs.get("name")
    if not name:
        name = platform.node()

    with open(expanded_public_key_path, "r") as fin:
        api.keys_create(
            cnf["user"][_get_hostname(stolos_url)], ssh_public_key=fin.read(), name=name
        )

    updated_conf = cnf["user"][_get_hostname(stolos_url)]
    updated_conf["identity-file"] = os.path.abspath(
        re.sub(".pub$", "", expanded_public_key_path)
    )
    config.update_user_config({"user": {stolos_url: updated_conf}})
    click.echo("Public key {} uploaded successfully".format(public_key_path))


@keys.command(name="list", help="List your SSH public keys")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.option(
    "--md5/--sha256", default=True, help="The hasing algorithm to use, defaults to MD5"
)
def keys_list(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    cnf = config.get_config()
    stolos_url = kwargs.get("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    algorithm = "md5"
    if not kwargs["md5"]:
        algorithm = "sha256"
    headers = ["UUID", "Name", algorithm.upper()]
    keys = [
        (key["uuid"], key["name"], key[algorithm])
        for key in api.keys_list(cnf["user"][_get_hostname(stolos_url)])
    ]
    click.echo(tabulate(keys, headers=headers))


@keys.command(help="Delete an SSH public key")
@click.option(
    "--stolos-url", help="The URL of the Stolos server to use, if not the default"
)
@click.argument("public-key-uuid", required=True)
def keys_delete(**kwargs):
    _ensure_logged_in(kwargs["stolos_url"])
    public_key_uuid = kwargs.get("public_key_uuid")
    cnf = config.get_config()
    stolos_url = kwargs.pop("stolos_url")
    if not stolos_url:
        stolos_url = cnf["user"]["default-api-server"]
    click.echo('Deleting SSH public key "{}"...'.format(public_key_uuid), nl=False)
    api.keys_remove(cnf["user"][_get_hostname(stolos_url)], public_key_uuid)
    click.echo("\t\tOkay.")


def _initialize_project(stolos_url, project):
    """
    Initialize a Stolos project with the needed files, using the response from
    the server.
    """
    config.update_project_config(
        {
            "project": {
                "uuid": project["uuid"],
                "stack": project["stack"]["slug"] if project["stack"] else None,
                "public-url": project["routing_config"]["domain"],
                "subdomains": project["routing_config"]["config"]["subdomains"],
            },
            "user": {"default-api-server": stolos_url},
            "server": {"host": project["server"]["host"]},
        }
    )
    with open(".stolos/ca.pem", "w+") as ca_pem:
        ca_pem.write(project["server"]["docker_ca_pem"])
        os.chmod(".stolos/ca.pem", 0o600)
    if project["stack"]:
        with open("docker-compose.yaml", "w+") as docker_compose:
            docker_compose.write(project["stack"]["docker_compose_file"])
    with open(".stolos/default.prf", "w+") as default_profile:
        default_profile.write(
            """
# Default unison profile for UNIX systems
include common

"""
        )
    with open(".stolos/win.prf", "w+") as windows_profile:
        windows_profile.write(
            """
# Unison profile for Windows systems
perms = 0

include common

"""
        )
    with open(".stolos/common", "w+") as common:
        common.write(
            string.Template(
                """
# Roots of the synchronization
root = .
root = ssh://stolos@${STOLOS_SERVER}//mnt/stolos/${STOLOS_PROJECT_ID}

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
                STOLOS_PROJECT_ID=project["uuid"],
                STOLOS_SERVER=project["server"]["host"],
            )
        )


def _initialize_services():
    compose_file_path = os.path.join(os.getcwd(), "docker-compose.yaml")
    if not os.path.exists(compose_file_path):
        return
    clone_urls = {}
    if not os.path.exists(compose_file_path):
        return
    with open(compose_file_path, "r") as fin:
        compose_file = yaml.load(fin)
    services = compose_file.get("services", {})
    valid = re.compile(r"^([^=]+)=(.+)")
    for service, service_details in iteritems(services):
        if "environment" not in service_details:
            continue
        environment = service_details["environment"]
        if type(environment) == list:
            environment = {}
            for var in service_details["environment"]:
                match = valid.match(var)
                if match is None:
                    continue
                environment[match.group(1)] = match.group(2)
        if "STOLOS_REPO_URL" not in environment:
            continue
        clone_urls[service] = environment["STOLOS_REPO_URL"]
    results = {"success": [], "failure": []}
    if len(clone_urls) == 0:
        return
    click.secho("Initializing services", bold=True)
    for service, url in iteritems(clone_urls):
        service_dir = url.rstrip().split(" ")[-1]
        if os.path.exists(service_dir):
            results["success"].append(
                'Service "{}" is already initialized.'.format(service)
            )
            continue
        if url.startswith("git+"):
            scm = "git"
            clone_url = url[4:]
        elif url.startswith("hg+"):
            scm = "hg"
            clone_url = url[3:]
        else:
            results["failure"].append(
                'Service "{}" initialization failed.\nPattern of repository url "{}" could not be resolved.'.format(
                    service, url
                )
            )
            continue
        try:
            init_process = subprocess.Popen(
                [scm, "clone"] + clone_url.strip().split(" "),
                stdout=sys.stdout,
                stderr=sys.stderr,
                stdin=sys.stdin,
            )
        except OSError as e:
            if e.errno == 2:
                results["failure"].append(
                    'Service "{}" initialization from "{}" failed.\nPlease install {} and attempt to manually initialize.'.format(
                        service, clone_url.strip().split(" ")[0], scm
                    )
                )
            else:
                results["failure"].append(
                    'Service "{}" initialization from "{}" failed with the following error:\n\t{}}'.format(
                        service, clone_url.strip().split(" ")[0], e
                    )
                )
            continue
        if init_process.wait() == 0:
            results["success"].append(
                'Service "{}" was successfully initialized.'.format(service)
            )
        else:
            results["failure"].append(
                'Service "{}" initialization from "{}" failed.\nPlease attempt to manually initialize.'.format(
                    service, clone_url.strip().split(" ")[0]
                )
            )

    # Inform about successful initializations
    for success in results["success"]:
        click.echo(success)

    # Inform about failed initializations
    for failure in results["failure"]:
        click.secho(failure, bold=True)


def _deinitialize_project():
    """
    Deinitialize a Stolos project, deleting the `.stolos` directory.
    """
    if os.path.isdir(".stolos"):
        shutil.rmtree(".stolos", ignore_errors=True)


def _get_environ(cnf):
    """
    Gets the needed environment for Stolos.
    """
    for filename in [".stolos.yml", "docker-compose.yaml", "docker-compose.yml"]:
        compose_file_path = os.path.join(os.getcwd(), filename)
        if os.path.isfile(compose_file_path):
            break
    public_url = cnf["project"]["public-url"]
    env = {
        "STOLOS_PUBLIC_URL": public_url,
        "STOLOS_UUID": cnf["project"]["uuid"],
        "COMPOSE_PROJECT_NAME": cnf["project"]["uuid"].replace("-", ""),
        "COMPOSE_FILE": compose_file_path,
        "DOCKER_HOST": "tcp://{}:2376".format(cnf["server"]["host"]),
        "DOCKER_CERT_PATH": os.path.join(os.getcwd(), ".stolos"),
        "DOCKER_TLS_VERIFY": "1",
        "STOLOS_REMOTE_DIR": "/mnt/stolos/{}/".format(cnf["project"]["uuid"]),
        "UNISON": os.path.join(os.getcwd(), ".stolos"),
    }
    if cnf["project"]["stack"]:
        env["STOLOS_STACK_SLUG"] = cnf["project"]["stack"]
        env["STOLOS_STACK_NAME"] = os.path.basename(cnf["project"]["stack"])
    if os.path.exists(compose_file_path):
        with open(compose_file_path, "r") as fin:
            compose_file = yaml.load(fin)
        services = compose_file.get("services", {})
        for service, service_details in iteritems(services):
            if "ports" not in service_details:
                continue
            normalized_service = re.sub(r"[^a-zA-Z0-9_]", "_", service.upper())
            service_key = "STOLOS_PUBLIC_URL_{}".format(normalized_service)
            env[service_key] = _get_url_for_service_port(cnf, service)
            for port in service_details["ports"]:
                service_port_key = "{}_{}".format(service_key, port)
                env[service_port_key] = _get_url_for_service_port(cnf, service, port)
    return env


def _config_environ(cnf):
    """
    Configures the environment with any needed environment variables for compose
    and Unison. Also updates the docker certificates to the latest valid from
    user config.
    """
    cnf = config.get_config()
    server = cnf["user"]["default-api-server"]
    with open(".stolos/cert.pem", "w+") as cert_pem:
        cert_pem.write(cnf["user"][server].get("cert-pem", ""))
        os.chmod(".stolos/cert.pem", 0o600)
    with open(".stolos/key.pem", "w+") as key_pem:
        key_pem.write(cnf["user"][server].get("key-pem", ""))
    os.environ.update(_get_environ(cnf))


def _compose(args):
    """
    Run Docker Compose, with the given arguments. These arguments should be in
    array form `['-d', '--build']`, not as a single string.
    """
    p = subprocess.Popen(
        ["docker-compose"] + args, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin
    )
    return p


def _sync(repeat):
    """
    Starts a project sync using Unison. Takes an extra parameter, which makes
    the synchronization repeat using Unison `-repeat` or not.
    """
    cnf = config.get_config()
    _config_environ(cnf)
    identity_file = cnf["user"][cnf["user"]["default-api-server"]].get("identity-file")
    if identity_file is None:
        click.echo(
            click.style("[WARNING] ", bold=True)
            + "No public key was found. Your user's default key will be used."
        )
        click.echo("To upload a public ssh key, use the following command:")
        click.secho("\tstolos keys upload [PUBLIC_KEY_PATH]\n", bold=True)
        home = os.path.expanduser("~")
        identity_file = os.path.join(home, ".ssh", "id_rsa")
    args = []
    args.insert(0, "-i {}".format(identity_file))
    args.insert(0, "-sshargs")
    if repeat:
        args.insert(0, "2")
        args.insert(0, "-repeat")
    else:
        args.insert(0, "false")
        args.insert(0, "-fastcheck")
    if _is_windows():
        args.insert(0, "win")
    p = subprocess.Popen(
        ["unison"] + args, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin
    )
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
    if os.path.exists(os.path.join(base_directory, ".stolos")):
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
    return {"win32": True, "cygwin": True}.get(sys.platform, False)


def _get_url_for_service_port(cnf, service=None, port=None):
    public_url = cnf["project"]["public-url"]
    subdomain, _, domain = public_url.partition(".")
    if service is None and port is None:
        return "{public_url}".format(public_url=public_url)
    token = service
    if port is not None:
        token = "{token}-{port}".format(token=token, port=port)
    use_subdomains = cnf["project"].get("subdomains", False)
    if use_subdomains:
        return "{token}.{public_url}".format(token=token, public_url=public_url)
    else:
        return "{subdomain}-{token}.{domain}".format(
            subdomain=subdomain, token=token, domain=domain
        )


def _ensure_logged_in(stolos_url=None):
    """
    Ensures the user is logged in, at the given `stolos_url` Stolos server.
    Raises an exception if not.
    """
    cnf = config.get_config()
    if "user" not in cnf:
        raise exceptions.NotLoggedInException()
    if "default-api-server" not in cnf["user"] and not stolos_url:
        raise exceptions.NotLoggedInException()
    stolos_url = stolos_url or cnf["user"]["default-api-server"]
    if stolos_url not in cnf["user"]:
        raise exceptions.NotLoggedInException()


class InteruptHandler(object):
    """
    Helper class, for handling incoming signals and propagating them.
    """

    def __init__(self):
        self.state = 0

    def __call__(self, *args, **kwargs):
        self.state = self.state + 1
