# Proxmox User (PUser) Script Guide

### Sample Usage
Assume we have file *creds.csv* with the following contents:
```
david
graduatingjohn
wonjae
admin,Sup3rS3cr3tP@ss123!
jafar
xinrui
```
Specifying password **Sup3rS3cr3tP@ss123!** for **admin** overrides the default password in the following `puser create` commands.

- `puser create -f creds.csv` ⇒ create users in *creds.csv* with random passwords by default ***OR***
- `puser create -f creds.csv -p changeme` ⇒ create users in *creds.csv* with default password **changeme**
  - You can easly remove these users with `puser destroy -f creds.csv`
- `puser create -f creds.csv -u newstudent -p ijustjoined` ⇒ create user **newstudent** with password **ijustjoined**
- `puser passwd -f creds.csv -pu david -pp changeme -u david -p secretlyAgent47` ⇒ change **david**'s password to **secretlyAgent47** (authenticating as **david**)
- `puser destroy -f creds.csv -u graduatingjohn` ⇒ remove user **graduatingjohn**

All of the above commands push changes to the *creds.csv* file.
It should now look as follows (assuming you ran all of the above except `puser create -f creds.csv`):
```
newstundent,ijustjoined
david,secretlyAgent47
wonjae,changeme
admin,Sup3rS3cr3tP@ss123!
jafar,changeme
xinrui,changeme
```

- `puser destroy -f creds.csv` ⇒ remove all users in *creds.csv* from Proxmox (no changes made to the file)
  - You can easily undo this with `puser create -f creds.csv`

### Documentation
The `-f` option in the following commands allows specifying a credentials file that will be updated according to changes made by this script. Such a file would be useful for administrative purposes (such as checking a user's password) and useful for quickly creating or destroying a large set of users. The file has the following format:
- each user is specified on a separate line in the following format: `[user],[password]`
- passwords must not contain a comma (,)
For example, to specify users **user1** and **user2** with corresponding passwords **password1** and **password2** respectively, the file contents would look as follows:
```
user1,password1
user2,password2
```

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
  - Does not make changes to the file

`puser destroy -f [file] -u [user]`
- removes a *single user*
- deletes user's info from file
