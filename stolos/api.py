"""
API client for use in the Stolos CLI.
"""
import os.path
from functools import wraps

import click
import requests

from stolos import exceptions


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
                raise exceptions.ResourceDoesNotExist(err.response.json())
            else:
                raise exceptions.UnknownError(
                    err.response.status_code, err.response.text)
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
    url = os.path.join(stolos_url, 'api/a0.1/auth/login/')
    resp = requests.post(
        url, json={'username': username, 'password': password})
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def change_password(credentials, current_password, new_password):
    """
    Change a user's password.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/auth/password/')
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.post(url, headers=headers, json={
        'current_password': current_password,
        'new_password': new_password,
        're_new_password': new_password,
    })
    resp.raise_for_status()


@handle_api_errors
def projects_list(credentials):
    """
    List the projects of the currently logged in user.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/')
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_create(credentials, stack, public_url):
    """
    Create a new project, using the given stack and public URL.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/')
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.post(url, headers=headers, json={
        'set_stack': stack,
        'routing_config': {
            'domain': public_url,
            'config': {
                'subdomains': False,
            },
        },
    })
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_retrieve(credentials, project_uuid):
    """
    Retrieve the project with the given UUID.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/', project_uuid)
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


@handle_api_errors
def projects_remove(credentials, project_uuid):
    """
    Remove the proejct with the given UUID.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/', project_uuid)
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.delete(url, headers=headers)
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if not resp.status_code == 404:
            raise
