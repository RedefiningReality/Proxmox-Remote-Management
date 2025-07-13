# Proxmox and pfSense Remote Management
YouTube Playlist: https://youtube.com/playlist?list=PLSpsCUl2cY8at6Dr0c28G6-yC1exBnqrR

Tired of being reliant on external platforms like TryHackMe and HackTheBox? Want to host your own machines on your own servers? This repo is for you! Set up environments the way you like them in a single configuration file and provide students/users with a secure web interface where they can authenticate to start, stop, access, and revert their unique automatically-provisioned copy of the environment. Environments can be as complex as you desire, even with many virtual machines spanning multiple subnets. Integrates directly with the Proxmox web interface for interacting with virtual machines and pfSense for internet access and network logging/management.

If you're interested in the **command line scripts**, see the **[Scripts Guide](Scripts.md)**.
If you're interested in the **PHP website**, see the **[Web Guide](Web.md)**.

The [puser](scripts/puser.py) script, responsible for remotely managing Proxmox users in bulk, has [its own guide](Proxmox%20User%20(PUser)%20Script%20Guide.md) as well.

- The Python scripts in the [scripts](scripts/) folder, which can be run as ***commands***, interact with the Proxmox API and pfSense command line to perform these changes. They all have comprehensive help text.
- The PHP pages in the [web](web/) directory provide a ***web interface*** where, based on the configurations you specify, users can:
  - manage their access to Proxmox
  - start/stop/revert one instance of an environment you provide
- This all comes with setup scripts for **easy installation**, requiring *no manual installation other than cloning this repo*.

### User
![control panel](https://github.com/RedefiningReality/Proxmox-Remote-Management/assets/9508666/d3ba7d12-7851-4d53-9a52-8943e21b64db)
![john login](https://github.com/RedefiningReality/Proxmox-Remote-Management/assets/9508666/e3ea2c3e-a29b-4e7d-b525-b8756ea081e5)

### Administrator
![creds](https://github.com/RedefiningReality/Proxmox-Remote-Management/assets/9508666/c579e9ed-0935-4a34-b4ec-717939e3b974)
![config ini](https://github.com/RedefiningReality/Proxmox-Remote-Management/assets/9508666/5376b85d-c563-4adb-876f-44fac48ee0b9)
![proxmox](https://github.com/RedefiningReality/Proxmox-Remote-Management/assets/9508666/b2b1208e-7b66-4e15-bed6-c038f86b05a2)
