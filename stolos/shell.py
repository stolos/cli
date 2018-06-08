"""
Helper functions for detecting the user's current shell.
"""
import os
import os.path

import click


ENV_TEMPLATE = """
{env_vars}\
{usage_hint}
"""


def detect():
    """
    Detects the shell the user is currently using. The logic is picked from
    Docker Machine
    https://github.com/docker/machine/blob/master/libmachine/shell/shell.go#L13
    """
    shell = os.getenv("SHELL")
    if not shell:
        return None
    if os.getenv("__fish_bin_dir"):
        return "fish"
    return os.path.basename(shell)


def shell_config(shell):
    """
    Returns a dict in the following form, depending on the given shell:
    return {
        'prefix': '<preffix-to-use>',
        'suffix': 'suffix-to-use',
        'delimiter': '<delimiter-to-use>',
    }
    Logic from Docker Machine:
    https://github.com/docker/machine/blob/master/commands/env.go#L125
    """
    if shell == "fish":
        return {"prefix": "set -gx ", "suffix": '";\n', "delimiter": ' "'}

    elif shell == "powershell":
        return {"prefix": "$Env:", "suffix": '"\n', "delimiter": ' = "'}

    elif shell == "cmd":
        return {"prefix": "SET ", "suffix": "\n", "delimiter": "="}

    elif shell == "tcsh":
        return {"prefix": "setenv ", "suffix": '";\n', "delimiter": ' "'}

    elif shell == "emacs":
        return {"prefix": '(setenv "', "suffix": '")\n', "delimiter": '" "'}

    else:
        return {"prefix": "export ", "suffix": '"\n', "delimiter": '="'}


def usage_hint(command, shell):
    """
    Returns the usage hint and comment, for the given shell.
    """
    if shell == "fish":
        return ("eval ({command})".format(command=command), "#")
    elif shell == "powershell":
        return (
            "{command} | ForEach-Object {{If (-Not[string]::IsNullOrEmpty($_)) {{ $_ | Invoke-Expression }}}}".format(
                command=command
            ),
            "#",
        )
    elif shell == "cmd":
        return (
            '\t@FOR /f "tokens=*" %i IN ({command}) DO @%i'.format(command=command),
            "REM",
        )
    elif shell == "emacs":
        return (
            "(with-temp-buffer (shell-command {command} (current-buffer))"
            "(eval-buffer))".format(command=command),
            ";;",
        )
    elif shell == "tcsh":
        return ("eval `{command}`".format(command=command), ":")
    else:
        return ("eval $({command})".format(command=command), "#")


def print_env_eval(command, shell, env_dict):
    """
    Prints the environment evaluation snippet, given a shell and an environment
    dict.
    """
    if not shell:
        shell = detect()
    if not shell:
        click.echo("Shell could not be detected, falling back to bash", err=True)
    config = shell_config(shell)
    hint, comment = usage_hint(command, shell)
    uhint = "{} Run this command to configure your shell: \n{} {}\n".format(
        comment, comment, hint
    )
    config["usage_hint"] = uhint
    env_vars = ""
    for key in sorted(env_dict.keys()):
        config["key"] = key
        config["val"] = env_dict[key]
        env_vars = env_vars + "{prefix}{key}{delimiter}{val}{suffix}".format(**config)
    config["env_vars"] = env_vars
    msg = ENV_TEMPLATE.format(**config)
    click.echo(msg)
