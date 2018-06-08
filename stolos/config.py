import os

import click
import yaml


def get_user_config():
    """
    Returns the user configuration, taking into account only the user
    directory.
    """
    config = os.path.join(click.get_app_dir("Stolos"), "config.yaml")
    return _get_config(config)


def get_project_config():
    """
    Returns the current project config.
    """
    config = os.path.join(os.getcwd(), ".stolos", "config.yaml")
    return _get_config(config)


def get_config():
    """
    Returns the merged configuration, from the current directory and the user
    directory.
    """
    config = get_user_config()
    update = get_project_config()
    for key in update:
        if key in config and type(config[key]) == dict:
            config[key].update(update[key])
        else:
            config[key] = update[key]
    return config


def update_user_config(update):
    """
    Updates the user configuration with the given parameters.
    """
    config = os.path.join(click.get_app_dir("Stolos"), "config.yaml")
    _update_config(config, update)


def update_project_config(update):
    """
    Updates the project configuration with the given parameters.
    """
    config = os.path.join(os.getcwd(), ".stolos", "config.yaml")
    _update_config(config, update)


def _get_config(path):
    """
    Returns the config from the given file, if exists.
    """
    if os.path.isfile(path):
        with open(path, "r") as fin:
            return yaml.load(fin)
    return {}


def _update_config(path, update):
    config = _get_config(path)
    for key in update:
        if key in config and type(config[key]) == dict:
            config[key].update(update[key])
        else:
            config[key] = update[key]
    parent_dir = os.path.abspath(os.path.join(path, os.pardir))
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    with open(path, "w+") as fout:
        yaml.safe_dump(config, stream=fout, default_flow_style=False, indent=2)
