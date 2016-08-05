## stolosctl requirements
- ssh
- python
- pip
- unison

### Unix installation process
1. Download unison binary from [to update with our mirror]
2. `pip install stolosctl`

### Windows installation process
1. Download cygwin from https://cygwin.com/install.html
2. Run cygwin setup.exe and make sure to install the following:
    - `openssh` from Net
    - `python` from Python
    - `unison2.48` from Utils
3. Run `python -m ensurepip` in Cygwin Terminal to install pip
4. `pip install stolosctl`
