## stolosctl requirements
- ssh
- python
- pip
- unison

### Unix installation process
1. Download unison binary from one of the following sources (preferably one with 4.02 ocaml version):
    - [unison 2.48.3 - ocaml 4.02](https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/unison/unison-2.48.3-4.02)
    - [unison 2.48.3 - ocaml 4.01](https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/unison/unison-2.48.3-4.01)
    - [unison 2.40.102 ocaml 4.02](https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/unison/unison-2.40.102-4.02)
    - [unison 2.40.102 ocaml 4.01](https://cf979153cd14525475d4-f860d1dda29fa1b9bcbf643d12472ae9.ssl.cf1.rackcdn.com/unison/unison-2.40.102-4.01)
2. `pip install stolosctl`

### OSX installation process
1. `brew install unison`
2. `pip install stolosctl`

### Windows installation process
1. Download cygwin from https://cygwin.com/install.html
2. Run cygwin setup.exe and make sure to install the following:
    - `openssh` from Net
    - `python` from Python
    - `unison2.48` from Utils
3. Run `python -m ensurepip` in Cygwin Terminal to install pip
4. `pip install stolosctl`
