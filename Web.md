# Proxmox and pfSense Remote Management Website

A basic web interface that allows users to . Environment and user options are configured by you in the [config.ini](web/config.ini) file, which has detailed comments explaining each option. This uses the Python remote management scripts for its backend. More information about the scripts may be found [here](Scripts.md).

### Setup
**Note:** Requires Python 3. These instructions are for installing the Python scripts AND the web interface. To install only the Python scripts, consult the setup instructions [here](Scripts.md).
*While this may be installed on Windows and has been tested on Windows 11, the setup scripts assume a Linux OS.*

pip installation to be created in the near future
1. Select a folder to save the scripts in. My recommendation for Linux is `/opt`: `cd /opt`
1. Clone this repository: `git clone https://github.com/RedefiningReality/Proxmox-Remote-Management.git`
1. Enter the cloned directory: `cd Proxmox-Remote-Management`
1. Run the [setup script](setup-web.py): `setup-web.py` or `python setup-web.py`. It will walk you through the process, test your current Proxmox and pfSense installation, modify the Python scripts accordingly, and prepare the web files to be served using Apache2 and PHP.
1. Modify [config.ini](web/config.ini) to reflect your desired configuration. This will let you determine how users authenticate, what the cloning process looks like, and where to log output, among other things.
1. (Optional) You may test out your configuration by navigating to test.php in a web browser (https://localhost/test.php)
   - The commands to be issued for creating, reverting, and destroying environments will be shown at the top.
   - You may test out each of these individually by clicking the corresponding button underneath. These may take some time to run, and you will not see a countdown timer. Please be patient. When finished, the output will display along with the return code and execution time. You may use the execution time as a reference when determining appropriate values for **create_time**, **revert_time**, and **destroy_time** in the config.ini file. These determine the duration of the countdown timer users will see - more information in [config.ini](web/config.ini).
   - ***IMPORTANT:*** Remove test.php from your web directory when finished! `rm [path to web directory]/test.php` (eg. `rm /var/www/html/test.php`)
1. (Optional) If you plan to use the command line scripts directly as well, modify [easyclone.sh](scripts/easyclone.sh) and [easypurge.sh](scripts/easypurge.sh) to your liking. See comments in each script.
You can add these to your PATH so that they may be executed as commands with the following:
```
ln -s easyclone.sh /usr/bin/easyclone
ln -s easypurge.sh /usr/bin/easypurge
```

Additional notes about the setup script:
- You may pass any options as arguments instead of answering the prompts. Prompts associated with options you pass in this way will not be displayed.
- If you don't want to validate connection to Proxmox and/or pfSense (not recommended), you may use `-b` to bypass all checks.
- If you'd like to perform a fully unattended installation (no prompts), use `-f [True/False]` to specify whether you're using a pfSense firewall, `-d [True/False]` to specify whether you'd like to automatically install Python dependencies using pip, and `-p [True/False]` to specify whether you'd like to add the finished scripts to your PATH (Linux only) -> be sure you specify all other options!

### Pages
