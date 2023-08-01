# Proxmox and pfSense Remote Management
Manage users in bulk, create templates from virtual machines, clone environments (groups of virtual machines) for a set of users, revert environments, and destroy environments
- The Python scripts in the [scripts](scripts/) folder interact with the Proxmox API and pfSense command line to perform these changes. They all have comprehensive help text.
- The PHP pages in the [web](web/) directory provide a web interface where, based on the **configurations you specify**, users can:
  - manage their access to Proxmox
  - start/stop/revert one instance of an environment you provide
- This all comes with setup scripts for **easy installation**, requiring *no manual installation other than cloning this repo*.

If you're interested in the **command line scripts**, see the **[scripts guide](Scripts.md)**.
If you're interested in the **PHP website**, see the **[web guide](Web.md)**.
