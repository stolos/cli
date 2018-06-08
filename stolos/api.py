"""
API client for use in the Stolos CLI.
"""
from functools import wraps

import click
import requests

from stolos import exceptions


def _urljoin(*args):
    """
    Joins given arguments into a url. Both trailing and leading slashes are
    stripped before joining.
    """
    return "/".join(map(lambda x: str(x).strip("/"), args)) + "/"


def _ensure_protocol(url):
    if not url.startswith("http"):
        return "https://{}".format(url)
    return url


def handle_api_errors(func):
    """
    Decorator for handling API errors. Catches `requests.exceptions.HTTPError`
    and throws the appropriate `exceptions.*` error.
    """

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code / 100 == 5:
                raise exceptions.ServerError(err.response.text)
            elif err.response.status_code in [401, 403]:
                raise exceptions.Unauthorized(err.response.json())
            elif err.response.status_code == 400:
                raise exceptions.BadRequest(err.response.json())
            elif err.response.status_code == 404:
                try:
                    raise exceptions.ResourceDoesNotExist(err.response.json())
                except ValueError:
                    raise exceptions.ResourceDoesNotExist(err.response.text)
            elif err.response.status_code == 409:
                raise exceptions.ResourceAlreadyExists()
            else:
                raise exceptions.UnknownError(
                    err.response.status_code, err.response.text
                )
        except requests.exceptions.ConnectionError as err:
            raise exceptions.NoInternetException()
        except requests.exceptions.Timeout as err:
            raise exceptions.Timeout()

    return func_wrapper


@handle_api_errors
def authenticate(stolos_url, username, password):
    """
    Authenticate the user to the given Stolos server, using the given
    credentials. Returns the authentication token.
    """
    url = _urljoin(stolos_url, "api/a0.1/auth/login/")
    resp = requests.post(
        _ensure_protocol(url), json={"username": username, "password": password}
    )
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def change_password(credentials, current_password, new_password):
    """
    Change a user's password.
    """
    url = _urljoin(credentials["host"], "api/a0.1/auth/password/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.post(
        _ensure_protocol(url),
        headers=headers,
        json={
            "current_password": current_password,
            "new_password": new_password,
            "re_new_password": new_password,
        },
    )
    resp.raise_for_status()


@handle_api_errors
def stacks_list(credentials):
    """
    List the stacks accessible to the currently logged in user.
    """
    url = _urljoin(credentials["host"], "api/a0.1/stacks/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.get(_ensure_protocol(url), headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_list(credentials):
    """
    List the projects of the currently logged in user.
    """
    url = _urljoin(credentials["host"], "api/a0.1/projects/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.get(_ensure_protocol(url), headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_create(credentials, stack, public_url, subdomains):
    """
    Create a new project, using the given stack and public URL.
    """
    url = _urljoin(credentials["host"], "api/a0.1/projects/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.post(
        _ensure_protocol(url),
        headers=headers,
        json={
            "set_stack": stack,
            "routing_config": {
                "domain": public_url,
                "config": {"subdomains": subdomains},
            },
        },
    )
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_retrieve(credentials, project_uuid):
    """
    Retrieve the project with the given UUID.
    """
    url = _urljoin(credentials["host"], "api/a0.1/projects/", project_uuid)
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.get(_ensure_protocol(url), headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_remove(credentials, project_uuid):
    """
    Remove the proejct with the given UUID.
    """
    url = _urljoin(credentials["host"], "api/a0.1/projects/", project_uuid)
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.delete(_ensure_protocol(url), headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if not resp.status_code == 404:
            raise


@handle_api_errors
def keys_create(credentials, ssh_public_key, name=None):
    """
    Create a new SSH public key.
    """
    url = _urljoin(credentials["host"], "api/a0.1/keys/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.post(
        _ensure_protocol(url),
        headers=headers,
        json={"public_key": ssh_public_key, "name": name},
    )
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def keys_list(credentials):
    """
    List the SSH public keys of the currently logged in user.
    """
    url = _urljoin(credentials["host"], "api/a0.1/keys/")
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.get(_ensure_protocol(url), headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def keys_remove(credentials, public_key_uuid):
    """
    Remove the SSH public key with the given UUID.
    """
    url = _urljoin(credentials["host"], "api/a0.1/keys/", public_key_uuid)
    headers = {"Authorization": "Token {}".format(credentials["token"])}
    resp = requests.delete(_ensure_protocol(url), headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if not resp.status_code == 404:
            raise
