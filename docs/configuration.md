# Stolos CLI configuration files and directories

`stolosctl` has two layers of configuration files which are merged before running each command:

* `$PWD/.stolos/config.yaml` - used for project specific configuration options, like the project ID and the server it belongs
* `[OS Specific Application directory]/Stolos/config.yaml` - used for user specific configuration options, like the user token
  * this is using [Click's application specific directories](http://click.pocoo.org/5/utils/#finding-application-folders)

Also, the following files exist inside the project directory

* `$PWD/.stolos/ca.pem` - the Certificate Authority Certificate to use for connecting to Docker
* `$PWD/.stolos/cert.pem` - the Docker Certificate to use for connecting to Docker
* `$PWD/.stolos/key.pem` - the key to use for authentication with Docker
* `$PWD/.stolos/id_rsa` - the private key to use for SSHing for Unison

When the CLI is triggered, the user specific options are initialized, they're merged with the project specific ones and in case of conflict, the project specific ones have precedence.

## Supported options

### `user`

User specific options, under partitioned under a key identifying each API host

* `user.[stolos-server-host].username` - the username of this API server user
* `user.[stolos-server-host].token` - the authentication token of this API server user
* `user.[stolos-server-host].host` - the host of the Stolos API server, including the protocol scheme

### `default-server` - the default API server to use, if not provided

### `project`

Project specific options

* `project.uuid` - the UUID of the current project
* `project.stack` - the Stack of the current project
* `project.public-url` - the base public URL of the current project

#### `server` - the Stolos server to use

* `server.host` - the host of the Stolos server to user

## Example

Below is a typical example of a user and a project configuration

### `$PWD/.stolos/config.yaml`

```yaml
project:
  uuid: a80d28e4-8e2f-46e3-9437-6c7a5d011886
  stack: sourcelair/stolos
  public-url: stolos.akalipetis.stolos.io
server:
  host: 52.59.88.19
```

### `[OS Specific Application directory]/Stolos/config.yaml`

```yaml
user:
  sourcelair.stolos.io:
    host: https://sourcelair.stolos.io
    username: akalipetis
    token: 07a0471964099d146579be5d2368b2dd613bda57
default-api-server: sourcelair.stolos.io
```
