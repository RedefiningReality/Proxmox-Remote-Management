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

All of the above commands commit all changes to the *creds.txt* file, which should now look as follows (assuming you ran the 2nd command instead of the first):
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
