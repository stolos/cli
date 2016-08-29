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

#### `stolos password [OPTIONS]`
Change your Stolos password

##### Options:
```
--password TEXT      Your current stolos password
--new-password TEXT  Your new stolos password
--stolos-url TEXT    The URL of the Stolos server to use, if not the default
--help               Show this message and exit.
```

##### Example
```
$ stolos password
Current password (typing will be hidden):
New password (typing will be hidden):
Repeat for confirmation:
Password successfully updated.
```

#### `stolos up`
Run all your services and sync your files

##### Options:                                                                                                                                                                  
-d, --detach        Sync files once and run services in the background
--logs / --no-logs  Do not print services logs.
--build             Build the services before starting them.
--help              Show this message and exit
```

##### Example
```
$ stolos up
Syncing...
Okay.
Starting services...
Starting 84b22c56c7664334b6d8912fc98c2835_cache_1
Starting 84b22c56c7664334b6d8912fc98c2835_db_1
Starting 84b22c56c7664334b6d8912fc98c2835_worker_1
Starting 84b22c56c7664334b6d8912fc98c2835_web_1
Starting 84b22c56c7664334b6d8912fc98c2835_watcher_1
Started services at sourcelair-stolos-akalipetis-zzqouw.sourcelair.stolos.io
db_1       | Logs here...
cache_1    | Logs here...
worker_1   | Logs here...
web_1      | Logs here...
```

#### `stolos launch`
Open the public URL of the current project

##### Example
```
$ stolos launch
Opening http://sourcelair-stolos-akalipetis-zzqouw.sourcelair.stolos.io...
```

#### `stolos info`
Get information about your current project

##### Example
```
$ stolos info
UUID                                  Stack              Public URL
------------------------------------  -----------------  --------------------------------------------------------
84b22c56-c766-4334-b6d8-912fc98c2835  sourcelair/stolos  sourcelair-stolos-akalipetis-zzqouw.sourcelair.stolos.io
```

#### `stolos sync [OPTIONS]`
Sync your files

##### Options:
```
  --repeat / --oneoff  If the sync should run continuously, defaults to true
```

##### Example
```
$ stolos sync --oneoff
Syncing...
Okay.
```

#### `stolos compose [COMPOSE_ARGS]`
Run Docker Compose commands in Stolos

##### Example
```
$ stolos compose ps
                   Name                                 Command               State                 Ports
------------------------------------------------------------------------------------------------------------------------
84b22c56c7664334b6d8912fc98c2835_cache_1     docker-entrypoint.sh redis ...   Up      6379/tcp
84b22c56c7664334b6d8912fc98c2835_db_1        /docker-entrypoint.sh postgres   Up      5432/tcp
84b22c56c7664334b6d8912fc98c2835_watcher_1   ./check_n_run.sh make watch      Up
84b22c56c7664334b6d8912fc98c2835_wdb_1       /bin/sh -c wdb.server.py - ...   Up      0.0.0.0:32796->1984/tcp, 19840/tcp
84b22c56c7664334b6d8912fc98c2835_web_1       ./check_n_run.sh make dev        Up      0.0.0.0:32797->8000/tcp
84b22c56c7664334b6d8912fc98c2835_worker_1    ./check_n_run.sh make worker     Up
```

#### `stolos projects create [OPTIONS] STACK PROJECT_DIRECTORY`
Create a new Stolos project

##### Options:
```
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

## Development

In order to install this library for development, use:

```bash
pip install --editable ./
```

## Documentation

* [Configuration overview](docs/configuration.md)
