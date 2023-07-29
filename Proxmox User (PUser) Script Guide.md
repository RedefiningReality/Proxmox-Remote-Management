# Proxmox User (PUser) Script Guide

### Sample Usage
Assume we have file *creds.txt* with the following contents:
```
david
graduatingjohn
wonjae
admin,Sup3rS3cr3tP@ss123!
jafar
xinrui
```
Specifying a password (comma-separated) for admin overrides the default password in the following `puser create` commands.

- `puser create -f creds.txt` ⇒ create users in *creds.txt* with random passwords by default ***OR***
- `puser create -f creds.txt -p changeme` ⇒ create users in *creds.txt* with default password **changeme**
  - You can easly undo the above two commands with `puser destroy -f creds.txt`
- `puser create -f creds.txt -u newstudent -p ijustjoined` ⇒ create user **newstudent** with password **ijustjoined**
- `puser passwd -f creds.txt -pu david -pp changeme -u david -p secretlyAgent47` ⇒ change **david**'s password to **secretlyAgent47** (authenticating as **david**)
- `puser destroy -f creds.txt -u graduatingjohn` ⇒ remove user **graduatingjohn**

All of the above commands push changes to the *creds.txt* file.
It should now look as follows (assuming you ran all of the above except `puser create -f creds.txt`):
```
newstundent,ijustjoined
david,secretlyAgent47
wonjae,changeme
admin,Sup3rS3cr3tP@ss123!
jafar,changeme
xinrui,changeme
```

- `puser destroy -f creds.txt` ⇒ remove all users in *creds.txt* from Proxmox (no changes made to the file)
  - You can easily undo this with `puser create -f creds.txt`

### Documentation
File about

#### Create
`puser create -u [user] -p [password]`
- creates a single user with given password

`puser create -u [user]`
- creates a single user with random password

`puser create -f [file]`
- creates users defined in file (if they don't already exist)
- assigns users their corresponding password specified in file
- if no password is specified in file, assigns random password
- updates passwords in file

`puser create -f [file] -p [password]`
- creates users defined in file (if they don't already exist)
- assigns users their corresponding password specified in file
- if no password is specified in file, assigns provided password `[password]`

`puser create -f [file] -u [user] -p [password]`
- creates a *single user* with given password
- adds the user and password to the file

`puser create -f [file] -u [user]`
- creates a *single user* with random password
- adds the user and password to the file

#### Change Password
**Note:** Proxmox does not support API token authentication for changing passwords, which is used in these scripts by default. To change passwords, you'll have to specify the password for your administrative user with `-pp [password]` or specify the current username and password for the user whose password you're changing with `-pu [user] -pp [password]`. This information will be used for ticket authentication.

`puser passwd -u [user] -p [password]`
- changes password for a single user to the given password

`puser passwd -u [user]`
- changes password for a single user to a random password

`puser passwd -f [file]`
- changes password for all users defined in file
- assigns users their corresponding password specified in file
- if no password is specified in file, assigns random password
- updates passwords in file

`puser passwd -f [file] -p [password]`
- changes password for all users defined in file
- assigns *all users* password `[password]`
- updates passwords in file

`puser passwd -f [file] -u [user] -p [password]`
- changes password for a *single user* with given password
- updates password in file

`puser passwd -f [file] -u [user]`
- changes password for a *single user* with random password
- updates password in file

#### Destroy
`puser destroy -u [user]`
- removes a single user

`puser destroy -f [file]`
- removes users in file (if they exist)
Does not make changes to the file

`puser destroy -f [file] -u [user]`
- removes a *single user*
- deletes user's info from file
