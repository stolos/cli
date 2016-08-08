"""
API client for use in the Stolos CLI.
"""
import os.path

import click
import requests

from stolos import exceptions


def authenticate(stolos_url, username, password):
    """
    Authenticate the user to the given Stolos server, using the given
    credentials. Returns the authentication token.
    """
    url = os.path.join(stolos_url, 'api/a0.1/auth/login/')
    try:
        resp = requests.post(url,
                             json={'username': username, 'password': password})
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as err:
        raise click.UsageError(
            'Wrong authentication credentials')
    except requests.exceptions.ConnectionError as err:
        raise exceptions.NoInternetException()


def projects_list(credentials):
    """
    List the projects of the currently logged in user.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/')
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


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


def projects_retrieve(credentials, project_uuid):
    """
    Retrieve the project with the given UUID.
    """
    url = os.path.join(credentials['host'], 'api/a0.1/projects/', project_uuid)
    headers = {'Authorization': 'Token {}'.format(credentials['token'])}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


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
