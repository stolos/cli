# Stolos - Effortless development in the cloud, using your local tools

## Usage

```bash
stolos COMMAND [command options]
```

### Available commands

#### `login`
Simple command that logs you into Stolos, using your username and password. Your access token is being stored in `~/.stolos/token`.

##### Example
```
$ stolos login

Enter your stolos credentials.
Username: paris
Password (typing will be hidden):

Uploading ssh public key /Users/paris/.ssh/id_rsa.pub

Authentication successful.
```

#### `create PROJECT`
Creates a new Stolos project in your account. The only argument that you have to pass is the name of the project that you would like to create.

##### Example
```
$ stolos create sourcelair

Creating project "sourcelair"...                OK.

Project "sourcelair" is ready! Run `stolos services:add sourcelair SERVICE` to add your first services and `stolos up` to launch them!
```

#### `init PROJECT`
Initializes your development environment by creating all local resources needed to develop the given project.

##### Example
```
$ stolos init sourcelair

Fetching services of "sourcelair"...            OK.
Creating local directories...                   OK.

Run "stolos up" to start your services!
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