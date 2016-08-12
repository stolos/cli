## stolosctl requirements
- ssh
- python
- pip
- unison

### Unix installation process
1. Download the unison binary:
    - [unison 2.48.3 - ocaml 4.02](https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/unison/unison-2.48.3-4.02)
2. `pip install https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/stolosctl-0.1.zip#egg=stolos[compose]`

### OSX installation process
1. `brew install unison`
2. `pip install https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/stolosctl-0.1.zip#egg=stolos[compose]`

### Windows installation process
1. Download cygwin from https://cygwin.com/install.html
2. Run cygwin setup.exe and make sure to install the following:
    - `openssh` from Net
    - `python` from Python
    - `unison2.48` from Utils
    - `wget` from Web 
3. Run `python -m ensurepip` in Cygwin Terminal to install pip
4. `pip install https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/stolosctl-0.1.zip#egg=stolos` in Cygwin Terminal to install Stolos
5. `wget https://github.com/docker/compose/releases/download/1.8.0/docker-compose-Windows-x86_64.exe -O /usr/bin/docker-compose` in Cygwin Terminal to install Docker Compose for Windows

### Security

For extra security, use `pip install -U https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/stolosctl-0.1.zip#egg=stolos[security]`. Beware that this might not work as expected behind NATed networks.
