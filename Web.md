# Proxmox and pfSense Remote Management Website

A basic web interface that allows users to manage their access to Proxmox and create/revert/destroy one instance of an environment, within parameters that you define. These paramateres are defined in the [config.ini](web/config.ini) file, which has detailed comments explaining each option. This uses the Python remote management scripts for its backend. More information about the scripts may be found [here](Scripts.md).

### Setup
**Note:** Requires Python 3.9. These instructions are for installing the Python scripts AND the web interface. To install only the Python scripts, consult the setup instructions [here](Scripts.md).
*While this may be installed manually on Windows and has been tested on Windows 11, the setup scripts assume a Linux OS. See automatic web setup requirements below.*

If you ever run into issues with the website, be sure to check the apache error log (`tail /var/log/apache2/error.log` for most Linux distros). It's likely you either specified a path that your web user doesn't have permissions to write the creds file to (**creds_file** in config.ini) or PHP curl isn't installed (`sudo apt/apt-get/yum install php-curl`).
1. Create a new API key on Proxmox to be used by these scripts for remote access
1. (Optional) Create a pfSense virtual machine on Proxmox and enable SSH
1. (Optional but recommended) Purchase a domain name and obtain a TLS certificate for that domain
1. Select a folder to save the scripts in. My recommendation for Linux is `/opt`: `cd /opt`
1. Clone this repository: `git clone https://github.com/RedefiningReality/Proxmox-Remote-Management.git`
1. Enter the cloned directory: `cd Proxmox-Remote-Management`
1. Run the [setup script](setup.py): `sudo setup.py` or `sudo python setup.py`. It will walk you through the process, test your current Proxmox and pfSense installation, and modify the scripts accordingly.
1. Run the [web configuration script](configure.py): `sudo configure.py`. It will configure Apache2 and PHP to securely serve your web files.
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

Additional notes on the setup script:
- You may pass any options as arguments instead of answering the prompts. Prompts associated with options you pass in this way will not be displayed.
- If you don't want to validate connection to Proxmox and/or pfSense (not recommended), you may use `-b` to bypass all checks.
- If you'd like to perform a fully unattended installation (no prompts), be sure to:
  - use `--firewall/--no-firewall` to specify whether you're using a pfSense firewall
  - use `--script-dependencies/--no-script-dependencies` to specify whether you'd like to automatically install Python dependencies
  - use `--web-dependencies/--no-web-dependencies` to specify whether you'd like to automatically install apache2 and php
  - use `--add-to-path/--no-add-to-path` to specify whether you'd like to add links to the finished scripts to your PATH (recommended)
  - specify all other options! Any options you don't specify you'll be prompted to provide.

Requirements for the automatic web setup to work:
 - apt, apt-get, or yum package manager
 - systemd service manager

These requirements will be met on default installations of most popular Linux distros (Debian, Ubuntu, Fedora, RHEL, CentOS, etc.)

### Pages
First of all, some credit where it's due. The HTML for the login pages was taken from here: [https://www.tutorialrepublic.com/php-tutorial/php-mysql-login-system.php](https://www.tutorialrepublic.com/php-tutorial/php-mysql-login-system.php). However, instead of using SQL, all authentication information is directly forwarded to Proxmox (TLS encrypted).
- [config.ini](web/config.ini) ⇒ configuration file containing every parameter that can be modified to suit your needs
- [index.php](web/index.php) ⇒ the main page that provides users with the option to create, access, revert, or destroy their instance as well as change their password or sign out of their account
  - redirects to login.php if user is not logged in or if session expired
  - redirects to password.php if user has a default password that the admin wants changed - see **change_password** option in config.ini
  - prints generic error message if unable to connect to Proxmox and logs details in error log
- [login.php](web/login.php) ⇒ login page that forwards login information to Proxmox and creates a new session for valid users
  - redirects to index.php upon login or if user is already logged in
- [password.php](web/password.php) ⇒ accessible from index.php, allows a user to change their password
  - password information can be automatically updated in an admin-accessible file if desired using the **creds_file** option in config.ini
  - redirects to index.php on successful password change
- [register.php](web/register.php) ⇒ accessible from login.php, allows registering a new user given an instructor-provided access code
  - forwards credentials to Proxmox and creates a new user with limited privileges directly on Proxmox
  - optional and may be disabled with **register** option in config.ini
- [test.php](web/test.php) ⇒ test script to ensure environment options in config.ini have been configured correctly
  - usage explained above in Setup section
  - ***REMOVE OR DISABLE THIS WHEN SATISFIED WITH YOUR CONFIGURATION***
- [scripts.php](web/scripts.php) ⇒ inaccessible to users, dependency that is used by index.php to run scripts from the command line
  - this will render as a blank page and do nothing if accessed from a web browser
- [creds.php](web/creds.php) ⇒ inaccessible to users, dependency that is used by register.php and login.php to update credentials in credentials file
  - credentials file can be set using the **creds_file** option in config.ini
  - this will render as a blank page and do nothing if accessed from a web browser

### Known Vulnerabilities and Why I Don't Care
I created this platform to facilitate teaching cybersecurity, so I should know something about web app vulnerabilities, right?
- Access code on the register.php page can be bruteforced. This would allow anyone to create users, even if they were not initially provided with the access code.
  - If you're worried about this, using a very complex access code (which can be as long as you want by the way) will render this infeasible.
  - If an attacker were able to arbitrarily create users, the only thing they could do is spawn environments, which other than wasting server resources (possible denial of service), doesn't pose a great threat.
  - The puser script allows you to delete created users and their associated environments in a matter of seconds, especially if you're saving credentials to a file, which is set by default.
- Username enumeration for users with access code on register.php
  - I believe the benefits of knowing you've chosen a bad username far outweight the costs of a malicious actor knowing a username is valid in this instance. It would be frustrating for users not to know why they're having trouble registering.
  - The chances someone you trusted with an access code will want to enumerate usernames is slim.
  - There's no way an attacker could leverage this information to do something malicious, at least with the current setup. Except maybe bruteforcing your password, but you should be using secure passwords in the first place.
- Cross-Site Requesty Forgery (CSRF) could allow an attacker to send users a malicious link that would change the user's password, if they are logged into a PHP session.
  - The possibility of this being exploited is extremely unlikely. An attacker would have to craft a malicious URL, disguise it in a way that looks legitimate, and fool a user into clicking it. The user would also have to be signed in to the session at the time, and sessions are capped at 2 hours.
  - The effect of this being exploited is marginal. The attacker would be able to sign in as a user and create/revert/destroy a single instance of a contained environment. The user would probably complain that they cannot log in to the administrator, who would then end active PHP/Proxmox sessions and reset their password. I'll take this risk for the convenience of not having to retype my password every time I want to change it, thank you very much.
- Existing session IDs are saved to a sessions file that is exposed to anyone with a web client. A session ID, in this context, refers to an ID assigned to a specific instance of a user environment that is running (not to be confused with a Proxmox or PHP session), which is primarily used to assign machine names or achieve unique IP addressing across multiple instances.
  - A malicious actor would have to figure out how this file is encoded (probably by consulting the source code) and write a script to decode it. Session IDs also change as users create or destroy their environment.
  - In most use cases, session IDs only tell you the possible IP addresses of a user's contained environment. Where's that going to get you? Nowhere, you don't have access to it anyway. Knowing what session IDs are in use doesn't tell you which one belongs to which user either.
- Users with a valid access code may create unlimited Proxmox users on register.php
  - There's a certain level of trust that goes into providing someone with an access code that they would not want to then deny access to your service. To be fair, I did mention bruteforcing the access code eariler, but also just use a complex access code or implement a web application firewall that throttles requests if you're that worried.
  - Creating users takes up virtually no space in Proxmox. If someone wanted to do actual damage (denial of service), they'd have to start environments for each of those users, and a lot of them for it to actually be effective. This would be an extremely tedious task and probably not yield results in a reasonable timeframe.
  - This is no different from creating multiple accounts on a site like TryHackMe or HackTheBox, except that they have more dedicated hardware for high availability.
