# Proxmox and pfSense Remote Management Scripts

Scripts for managing users in bulk, creating templates from virtual machines, cloning environments for a set of users, reverting virtual machines, and destroying cloned environments. This serves as the backend for the web interface, which may be found [here](Web.md).

### Setup
**Note:** Requires Python 3. These instructions are for installing ONLY the Python scripts. To install these scripts along with the web interface, consult the setup instructions [here](Web.md).

pip installation to be created in the near future
1. Select a folder to save the scripts in. My recommendation for Linux is `/opt`: `cd /opt`
1. Clone this repository: `git clone https://github.com/RedefiningReality/Proxmox-Remote-Management-Scripts.git`
1. Enter the cloned directory: `cd Proxmox-Remote-Management`
1. Run the [setup script](setup-scripts.py): `setup-scripts.py` or `python setup-scripts.py`. It will walk you through the process, test your current Proxmox installation, and modify the other scripts accordingly.
1. Modify [easyclone.sh](scripts/easyclone.sh) and [easypurge.sh](scripts/easypurge.sh) to your liking. See comments in each script.
You can add these to your PATH so that they may be executed as commands with the following:
```
ln -s easyclone.sh /usr/bin/easyclone
ln -s easypurge.sh /usr/bin/easypurge
```

Additional notes about the setup script:
- You may pass any options as arguments instead of answering the prompts. Prompts associated with options you pass in this way will not be displayed.
- If you don't want to validate connection to Proxmox and/or pfSense (not recommended), you may use `-b` to bypass all checks.
- If you'd like to perform a fully unattended installation (no prompts), use `-f [True/False]` to specify whether you're using a pfSense firewall, `-d [True/False]` to specify whether you'd like to automatically install Python dependencies using pip, and `-p [True/False]` to specify whether you'd like to add the finished scripts to your PATH (Linux only) -> be sure you specify all other options!
