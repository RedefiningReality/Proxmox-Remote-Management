#!/usr/bin/env python3

import argparse
from proxmoxer import ProxmoxAPI, AuthenticationError
from colors import printc, Color
import random, string
import subprocess

import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Parse command line arguments
parser = argparse.ArgumentParser('manage Proxmox users')

parser.add_argument('action', choices=['create', 'passwd', 'destroy'], help='create new user, change an existing user\'s password, or destroy an existing user')

parser.add_argument('-u', '--username', type=str, help='name of user')
parser.add_argument('-f', '--users-file', type=str, help='path to file containing users - each user on a separate line with format <username> or <username>,<password>')

parser.add_argument('-p', '--password', type=str, help='password to assign to user')
parser.add_argument('-g', '--groups', type=str, nargs='+', help='groups to add new Proxmox user(s) to (space-separated)')

parser.add_argument('-c', '--purge-command', type=str, nargs='?', const='purge', help='destroy environments for removed users - specify purge script location if not in path')
parser.add_argument('-b', '--remove-bridges', action='store_true', help='remove Linux bridges with USERNAME as their description')
parser.add_argument('-bv', '--bridged-vms', type=str, help='check virtual machines with the specified IDs for bridge (requires -c)')
parser.add_argument('-fw', '--firewall', action='store_true', help='remove interface and DHCP from pfSense firewall configuration (requires -c)')

parser.add_argument('-pH', '--proxmox-host', type=str, default='PROXMOXHOST', help='Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or 216.47.144.123:443)')
parser.add_argument('-pu', '--proxmox-user', type=str, default='PROXMOXUSER', help='Proxmox username for authentication')
parser.add_argument('-pp', '--proxmox-password', type=str, help='Proxmox password for authentication')
parser.add_argument('-ptn', '--proxmox-token-name', type=str, default='PROXMOXTNAME', help='name of Proxmox authentication token for user')
parser.add_argument('-ptv', '--proxmox-token-value', type=str, default='PROXMOXTVAL', help='value of Proxmox authentication token')
parser.add_argument('-ssl', '--verify-ssl', action='store_true', help='verify SSL certificate on Proxmox host')

args = parser.parse_args()

users = {}

if args.username is not None:
    users[args.username] = args.password

if args.users_file is not None:
    print(f'Reading users from file {args.users_file}')
    file = open(args.users_file, 'r')
    for line in file.readlines():
        if ',' in line:
            user, password = line.strip().split(',')
        else:
            user = line.strip()
            password = None
        users[user] = password
    file.close()

# Connect to Proxmox server
if args.action == 'passwd':
    # Password authentication
    if args.proxmox_password is None:
        print('Proxmox does not support API token authentication for changing passwords')
        print('Changing passwords requires password authentication')
        printc('Please provide password with -pp option and change the login user with -pu if necessary', Color.YELLOW)
        exit()
    try:
        pm = ProxmoxAPI(args.proxmox_host, user=args.proxmox_user, password=args.proxmox_password, verify_ssl=args.verify_ssl)
    except AuthenticationError:
        printc('Incorrect username or password for authentication!', Color.RED)
        exit()
else:
    # Token authentication
    pm = ProxmoxAPI(args.proxmox_host, user=args.proxmox_user, token_name=args.proxmox_token_name, token_value=args.proxmox_token_value, verify_ssl=args.verify_ssl)
pusers = pm.access.users.get()
userids = [user['userid'] for user in pusers]

def create_user(user, password):
    userid = user + '@pve'
        
    if userid in userids:
        printc(f'Proxmox VE user {userid} already exists!', Color.YELLOW)
    else:
        params = {}
            
        params['userid'] = userid
        params['groups'] = ','.join(args.groups) if args.groups and len(args.groups)>0 else ''
            
        if password is None:
            print(f'Generating random password for {user}')
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            print(f'Randomly-generated password: {password}')
        
        users[user] = password
        params['password'] = password
                
        pm.access.users.post(expire=0, **params)
        print(f'Created Proxmox VE user {userid}')

def change_password(user, password):
    userid = user + '@pve'

    if userid in userids:
        print(f'Changing password for user {userid}')
        users[user] = password
        pm.access.password.put(userid=userid, password=password)
        print(f'Password changed')
    else:
        printc(f'User {userid} does not exist!', Color.YELLOW)

def remove_user(user):
    if args.purge_command:
        command = args.purge_command.split(' ')
        command.extend([user, '-u'])

        if args.remove_bridges or args.bridged_vms is not None or args.firewall:
            command.append('-b')
        if args.bridged_vms is not None:
            command.append('-bv')
            command.append(args.bridged_vms)
        if args.firewall:
            command.append('-f')

        print(command)
        subprocess.run(command)
    else:
        userid = user + '@pve'
        print(f'Removing Proxmox VE user {userid}')
    
        if userid in userids:
            pm.access.users(userid).delete()
            print(f'Removed Proxmox VE user {userid}')
        else:
            printc(f'User {userid} does not exist!', Color.YELLOW)

if args.action == 'create':
    print('Creating new Proxmox users')

    if args.username is None:
        for user, password in users.items():
            if password is None:
                create_user(user, args.password)
            else:
                create_user(user, password)
    else:
        create_user(args.username, args.password)

    printc('Finished creating all Proxmox users!', Color.GREEN)

elif args.action == 'passwd':
    print('Changing passwords for specified Proxmox users')

    if args.username is None:
        for user, password in users.items():
            if args.password is None:
                change_password(user, password)
            else:
                change_password(user, args.password)
    else:
        change_password(args.username, args.password)

    printc('Finished changing all passwords!', Color.GREEN)

else:
    print('Removing specified Proxmox users')

    if args.username is None:
        for user in users.keys():
            remove_user(user)
    else:
        remove_user(args.username)
        del users[args.username]

    printc('Finished removing Proxmox users!', Color.GREEN)

if args.users_file:
    print(f'\nUpdating file {args.users_file}')
    file = open(args.users_file, 'w')
    for user, password in users.items():
        file.write(f'{user},{password}\n')
    file.close()
    printc('Finished writing changes to file!', Color.GREEN)