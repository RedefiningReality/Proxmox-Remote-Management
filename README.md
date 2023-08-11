# Proxmox and pfSense Remote Management
Tired of being reliant on external platforms like TryHackMe and HackTheBox? Want to host your own machines on your own servers? This repo is for you! Set up environments the way you like them in a single configuration file and provide students/users with a secure web interface where they can authenticate to start, stop, access, and revert their unique automatically-provisioned copy of the environment. Environments can be as complex as you desire, even with many virtual machines spanning multiple subnets. Integrates directly with the Proxmox web interface for interacting with virtual machines and pfSense for internet access.

- The Python scripts in the [scripts](scripts/) folder, which can be run as ***commands***, interact with the Proxmox API and pfSense command line to perform these changes. They all have comprehensive help text.
- The PHP pages in the [web](web/) directory provide a ***web interface*** where, based on the configurations you specify, users can:
  - manage their access to Proxmox
  - start/stop/revert one instance of an environment you provide
- This all comes with setup scripts for **easy installation**, requiring *no manual installation other than cloning this repo*.

If you're interested in the **command line scripts**, see the **[scripts guide](Scripts.md)**.
If you're interested in the **PHP website**, see the **[web guide](Web.md)**.

The [puser](scripts/puser.py) script, responsible for remotely managing Proxmox users in bulk, has [its own guide](Proxmox%20User%20(PUser)%20Script%20Guide.md) as well.
