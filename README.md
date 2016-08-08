# Stolos - Effortless development in the cloud, using your local tools

## Usage

```bash
stolos COMMAND [command options]
```

### Available commands

#### `stolos login [OPTIONS]`
Simple command that logs you into Stolos, using your username and password. Your access token is being stored in `~/.stolos/config.yaml`.

##### Options:
```
--username TEXT    Your Stolos username
--password TEXT    Your stolos password
--stolos-url TEXT  The URL of the Stolos server to use
--help             Show this message and exit.
```

##### Example
```
$ stolos login --stolos-url=https://sourcelair.stolos.io
Username: paris
Password (typing will be hidden):
Authentication successful.
```

#### `stolos projects create [OPTIONS] STACK PROJECT_DIRECTORY` Create a new Stolos project
```
Options:
  --public-url TEXT  The public URL of your project, defaults to random hex
  --stolos-url TEXT  The URL of the Stolos server to use, if not the default
  --help             Show this message and exit.
```

##### Example
```
$ stolos projects create sourcelair/stolos stolos
Assigning random public URL "sourcelair-stolos-akalipetis-czimkp.akalipetis.sourcelair.stolos.io"
Creating project "stolos"...		Ok.
Project "stolos" is ready! Change directory with "cd stolos" and run "stolos up" to launch it!
```

#### `stolos projects connect [OPTIONS] PROJECT_UUID`
Connect the current directory to an existing Stolos project.


##### Options:
```
--stolos-url TEXT  The URL of the Stolos server to use, if not the default
--help             Show this message and exit.
```

##### Example
```
$ stolos projects connect 7c3bc55d-d7d5-40d4-8765-cbc2e41b1978
Connecting to project "7c3bc55d-d7d5-40d4-8765-cbc2e41b1978"...		Ok.
Your project is ready! Run "stolos up" to launch it!
```

#### `stolos projects list [OPTIONS]`
List your projects

##### Options:
```
--stolos-url TEXT  The URL of the Stolos server to use, if not the default
--help             Show this message and exit.
```

##### Example:
```
UUID                                  Stack              Public URL
------------------------------------  -----------------  -------------
7c3bc55d-d7d5-40d4-8765-cbc2e41b1978  sourcelair/stolos  stage.stolos.io
69e5f6bd-76b7-4f6e-acd2-32823716a2d8  sourcelair/stolos  example.stolos.io
```


#### `stolos projects delete [OPTIONS] [PROJECT_UUID]`
Delete a Stolos project

##### Options:
```
--stolos-url TEXT    The URL of the Stolos server to use, if not the default
--help               Show this message and exit.
```

##### Example
```
$ stolos projects delete
Deleting project "69e5f6bd-76b7-4f6e-acd2-32823716a2d8"...		Ok.
```

#### `up`
Runs all your services on Stolos's infrastructure, using your local files. Also updates files on Stolos automatically as you save them.

##### Example
```
$ stolos up

Initializing all services...                    OK.


web        | Some logs here
worker     | Some logs here
ceryx      | Some logs here
proxy      | Some logs here
```

## Development

In order to install this library for development, use:

```bash
pip install --editable ./
```

## Documentation

* [Configuration overview](docs/configuration.md)
