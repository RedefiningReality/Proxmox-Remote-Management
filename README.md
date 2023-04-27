# Automated Environment Scripts
Converts a set of Proxmox virtual machines to templates, which can then be dynamically provisioned for a set of users. The intended purpose of this project is for teaching cybersecurity hands-on, allowing an instructor to set up a cybersecurity practice environment that can be easily cloned to provide each student with access to their own copy.

### Setup
**Note:** Requires Python 3
1. Select a folder to save the scripts in. My recommendation for Linux is `/opt`: `cd /opt`
2. Clone this repository: `git clone https://github.com/RedefiningReality/Automated-Environment-Scripts.git`
3. Enter the cloned directory: `cd Automated-Environment-Scripts`
4. Modify the `[REDACTED]` text in each script and any other default values for arguments (look for the word `default`) so that it works with your Proxmox instance (this should be self-explanatory)
5. Create links to base scripts so they can be run as commands:
```
ln -s template.py /usr/bin/template
ln -s clone.py /usr/bin/clone
ln -s purge.py /usr/bin/purge
```
6. Modify [easyclone.sh](easyclone.sh) and [easypurge.sh](easypurge.sh) to your liking and create links to those as well. See comments in each script:
```
ln -s easyclone.sh /usr/bin/easyclone
ln -s easypurge.sh /usr/bin/easypurge
```

### Commands
- [template](template.py) ⇒ convert Proxmox virtual machines into clonable templates
- [clone](clone.py) ⇒ clone Proxmox virtual machine templates, adding corresponding Linux bridge and Proxmox user for access
- [purge](purge.py) ⇒ remove Proxmox virtual machines and corresponding Linux bridge, performing cleanup
- [easyclone](easyclone.sh) ⇒ template bash script that runs [clone](clone.py) with a set of predefined arguments
- [easypurge](easypurge.sh) ⇒ template bash script that runs [purge](purge.py) with a set of predefined arguments

### Command examples
`template 500-505 -r`

`clone 500-505 -c doge -i 600 -u -n "Your Mom" -e memes4dayz@totallyvaliddomain.com -p Password123 -b -bs 10.0.21.0/24 -bv 400,402,500-503 -f -fi 10.0.21.254 -db 10.0.21.10 -de 10.0.21.245 -dd 1.1.1.1 8.8.8.8 -ds 500,10.0.21.3 -s`

`purge doge -u -b -bv 400,402 -f`

### Usage information
#### [Template](template.py)
```
usage: convert Proxmox virtual machines into clonable templates [-h] [-r] [-v] [-pH PROXMOX_HOST]
                                                                [-pu PROXMOX_USER]
                                                                [-ptn PROXMOX_TOKEN_NAME]
                                                                [-ptv PROXMOX_TOKEN_VALUE] [-ssl]
                                                                [-pn PROXMOX_NODE]
                                                                ids

positional arguments:
  ids                   IDs of virtual machines to template (ex: 7 322,491 or 402,500-503)

options:
  -h, --help            show this help message and exit
  -r, --remove-network  remove all network devices from virtual machine templates
  -v, --verbose         increase the verbosity level
  -pH PROXMOX_HOST, --proxmox-host PROXMOX_HOST
                        Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or
                        216.47.144.123:443)
  -pu PROXMOX_USER, --proxmox-user PROXMOX_USER
                        Proxmox username for authentication
  -ptn PROXMOX_TOKEN_NAME, --proxmox-token-name PROXMOX_TOKEN_NAME
                        name of Proxmox authentication token for user
  -ptv PROXMOX_TOKEN_VALUE, --proxmox-token-value PROXMOX_TOKEN_VALUE
                        value of Proxmox authentication token
  -ssl, --verify-ssl    verify SSL certificate on Proxmox host
  -pn PROXMOX_NODE, --proxmox-node PROXMOX_NODE
                        node containing virtual machines to template
```
#### [Clone](clone.py)
```
usage: clone Proxmox virtual machine templates [-h] [-c CLONE_NAME] [-i CLONE_BEGIN_ID]
                                               [-t {linked,full}] [-s] [-u [USER]] [-n NAME]
                                               [-e EMAIL] [-p PASSWORD] [-g GROUPS [GROUPS ...]]
                                               [-r ROLES] [-b] [-bs BRIDGE_SUBNET] [-bp BRIDGE_PORTS]
                                               [-bv ADD_BRIDGED_VMS]
                                               [-cs CLOUD_INIT_STATIC [CLOUD_INIT_STATIC ...]] [-f]
                                               [-fi FIREWALL_IP] [-db DHCP_BEGIN] [-de DHCP_END]
                                               [-dd DHCP_DNS [DHCP_DNS ...]]
                                               [-ds DHCP_STATIC [DHCP_STATIC ...]] [-v]
                                               [-pH PROXMOX_HOST] [-pu PROXMOX_USER]
                                               [-ptn PROXMOX_TOKEN_NAME] [-ptv PROXMOX_TOKEN_VALUE]
                                               [-ssl] [-pn PROXMOX_NODE] [-fH FIREWALL_HOST]
                                               [-fP FIREWALL_PORT] [-fu FIREWALL_USER]
                                               [-fp FIREWALL_PASSWORD] [-ft FIREWALL_TIMEOUT]
                                               [-fc FIREWALL_CONFIG]
                                               ids

positional arguments:
  ids                   IDs of virtual machines to clone (ex: 7 322,491 or 402,500-503)

options:
  -h, --help            show this help message and exit
  -c CLONE_NAME, --clone-name CLONE_NAME
                        name prepended to virtual machine clones
  -i CLONE_BEGIN_ID, --clone-begin-id CLONE_BEGIN_ID
                        clones will be assigned the first available ID after this number (ex. 500 or
                        600)
  -t {linked,full}, --clone-type {linked,full}
                        the type of clone to create (default is linked)
  -s, --start-clone     start cloned virtual machines automatically both on boot and after cloning
  -u [USER], --user [USER]
                        create a new Proxmox VE user for managing the cloned virtual machines - if not
                        specified, this will default to the clone name
  -n NAME, --name NAME  full name of new Proxmox user (first and last)
  -e EMAIL, --email EMAIL
                        email of new Proxmox user
  -p PASSWORD, --password PASSWORD
                        password for new Proxmox user (default is a randomly-generated string)
  -g GROUPS [GROUPS ...], --groups GROUPS [GROUPS ...]
                        groups to add the new Proxmox user to (space-separated)
  -r ROLES, --roles ROLES
                        roles to assign to the user (default is builtin PVEVMUser)
  -b, --create-bridge   create a new Linux bridge for these virtual machines
  -bs BRIDGE_SUBNET, --bridge-subnet BRIDGE_SUBNET
                        add new bridge with subnet specified in CIDR notation (ex: 10.0.2.0/24)
  -bp BRIDGE_PORTS, --bridge-ports BRIDGE_PORTS
                        attach ports/slaves to the new bridge (ex. eno1)
  -bv ADD_BRIDGED_VMS, --add-bridged-vms ADD_BRIDGED_VMS
                        add the new bridge to the virtual machines with the specified IDs or clones of
                        templates with the specified IDs (requires -b)
  -cs CLOUD_INIT_STATIC [CLOUD_INIT_STATIC ...], --cloud-init-static CLOUD_INIT_STATIC [CLOUD_INIT_STATIC ...]
                        IP address for bridged VM with specified ID or clone created from template
                        with specified ID - VM MUST have cloud-init installed - format is <ID>,<IP>
                        (ex. 500,10.0.2.2 402,10.0.2.3)
  -f, --firewall        configure pfSense firewall to serve DHCP on newly-created bridge (requires -b)
  -fi FIREWALL_IP, --firewall-ip FIREWALL_IP
                        local IPv4 address of the pfSense firewall (subnet ending in .1 if not
                        specified)
  -db DHCP_BEGIN, --dhcp-begin DHCP_BEGIN
                        DHCP pool begin address
  -de DHCP_END, --dhcp-end DHCP_END
                        DHCP pool end address
  -dd DHCP_DNS [DHCP_DNS ...], --dhcp-dns DHCP_DNS [DHCP_DNS ...]
                        DNS servers to use for this subnet - served with DHCP (ex. 1.1.1.1 8.8.8.8)
  -ds DHCP_STATIC [DHCP_STATIC ...], --dhcp-static DHCP_STATIC [DHCP_STATIC ...]
                        DHCP static lease for bridged VM with specified ID or clone created from
                        template with specified ID - format is <ID>,<IP> (ex. 500,10.0.2.2
                        402,10.0.2.3)
  -v, --verbose         increase the verbosity level
  -pH PROXMOX_HOST, --proxmox-host PROXMOX_HOST
                        Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or
                        216.47.144.123:443)
  -pu PROXMOX_USER, --proxmox-user PROXMOX_USER
                        Proxmox username for authentication
  -ptn PROXMOX_TOKEN_NAME, --proxmox-token-name PROXMOX_TOKEN_NAME
                        name of Proxmox authentication token for user
  -ptv PROXMOX_TOKEN_VALUE, --proxmox-token-value PROXMOX_TOKEN_VALUE
                        value of Proxmox authentication token
  -ssl, --verify-ssl    verify SSL certificate on Proxmox host
  -pn PROXMOX_NODE, --proxmox-node PROXMOX_NODE
                        node containing virtual machines to template
  -fH FIREWALL_HOST, --firewall-host FIREWALL_HOST
                        hostname of pfSense firewall to configure DHCP on through SSH (requires -f)
  -fP FIREWALL_PORT, --firewall-port FIREWALL_PORT
                        SSH port for the pfSense firewall (default is 22)
  -fu FIREWALL_USER, --firewall-user FIREWALL_USER
                        username for the pfSense firewall (requires -f)
  -fp FIREWALL_PASSWORD, --firewall-password FIREWALL_PASSWORD
                        password for the pfSense firewall (requires -f)
  -ft FIREWALL_TIMEOUT, --firewall-timeout FIREWALL_TIMEOUT
                        time in seconds before connection to pfSense times out (default is 5)
  -fc FIREWALL_CONFIG, --firewall-config FIREWALL_CONFIG
                        path to configuration file in pfSense - this should be /cf/conf/config.xml
                        (default) unless using a customised pfSense instance
```
#### [Purge](purge.py)
```
usage: purge Proxmox virtual machines and corresponding Linux bridge [-h] [-u [USER]] [-b]
                                                                     [-bv BRIDGED_VMS] [-f] [-v]
                                                                     [-pH PROXMOX_HOST]
                                                                     [-pu PROXMOX_USER]
                                                                     [-ptn PROXMOX_TOKEN_NAME]
                                                                     [-ptv PROXMOX_TOKEN_VALUE] [-ssl]
                                                                     [-pn PROXMOX_NODE]
                                                                     [-fH FIREWALL_HOST]
                                                                     [-fP FIREWALL_PORT]
                                                                     [-fu FIREWALL_USER]
                                                                     [-fp FIREWALL_PASSWORD]
                                                                     [-ft FIREWALL_TIMEOUT]
                                                                     [-fc FIREWALL_CONFIG]
                                                                     clone_name

positional arguments:
  clone_name            remove virtual machines whose name starts with this (ex. test)

options:
  -h, --help            show this help message and exit
  -u [USER], --user [USER]
                        remove Proxmox VE user with specified username
  -b, --remove-bridges  remove Linux bridges with CLONE_NAME as their description
  -bv BRIDGED_VMS, --bridged-vms BRIDGED_VMS
                        check virtual machines with the specified IDs for bridge (requires -b)
  -f, --firewall        remove interface and DHCP from pfSense firewall configuration (requires -b)
  -v, --verbose         increase the verbosity level
  -pH PROXMOX_HOST, --proxmox-host PROXMOX_HOST
                        Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or
                        216.47.144.123:443)
  -pu PROXMOX_USER, --proxmox-user PROXMOX_USER
                        Proxmox username for authentication
  -ptn PROXMOX_TOKEN_NAME, --proxmox-token-name PROXMOX_TOKEN_NAME
                        name of Proxmox authentication token for user
  -ptv PROXMOX_TOKEN_VALUE, --proxmox-token-value PROXMOX_TOKEN_VALUE
                        value of Proxmox authentication token
  -ssl, --verify-ssl    verify SSL certificate on Proxmox host
  -pn PROXMOX_NODE, --proxmox-node PROXMOX_NODE
                        node containing virtual machines to template
  -fH FIREWALL_HOST, --firewall-host FIREWALL_HOST
                        hostname of pfSense firewall to configure DHCP on through SSH (requires -f)
  -fP FIREWALL_PORT, --firewall-port FIREWALL_PORT
                        SSH port for the pfSense firewall (default is 22)
  -fu FIREWALL_USER, --firewall-user FIREWALL_USER
                        username for the pfSense firewall (requires -f)
  -fp FIREWALL_PASSWORD, --firewall-password FIREWALL_PASSWORD
                        password for the pfSense firewall (requires -f)
  -ft FIREWALL_TIMEOUT, --firewall-timeout FIREWALL_TIMEOUT
                        time in seconds before connection to pfSense times out (default is 5)
  -fc FIREWALL_CONFIG, --firewall-config FIREWALL_CONFIG
                        path to configuration file in pfSense - this should be /cf/conf/config.xml
                        (default) unless using a customised pfSense instance
```
