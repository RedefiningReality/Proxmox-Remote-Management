#!/usr/bin/env python3

import argparse
import time
from threading import Thread
from proxmoxer import ProxmoxAPI
from colors import printc, Color

import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

threads = []

# Convert comma-separated or hyphenated numbers to list of numbers
# ex. "100,200-202" -> [100, 200, 201, 202]
def num_list(arg):
	result = set()
	for part in arg.split(','):
		if '-' in part:
			start, end = map(int, part.split('-'))
			result.update(range(start, end+1))
		else:
			result.add(int(part))
	return sorted(result)

# Check for IDs in ids list that don't exist in Proxmox
def valid_ids(ids):
	if ids is None:
		return []

	valid = []
	for vmid in ids:
		if vmid in vmids:
			valid.append(vmid)
		else:
			printc(f'No virtual machine found with ID {vmid}', Color.YELLOW)
	return valid

# Check virtual machine status every 5 seconds until it is unlocked
def check_locked(vmid,msg):
	while 'lock' in pm.nodes(args.proxmox_node).qemu(vmid).config.get():
		time.sleep(5)
	print(msg)

# Parse command line arguments
parser = argparse.ArgumentParser('rollback Proxmox virtual machines to an existing snapshot')

parser.add_argument('-i', '--ids', type=num_list, help='IDs of virtual machines to roll back (ex: 7 322,491 or 402,500-503)')
parser.add_argument('-c', '--clone-name', type=str, help='rollback virtual machines whose name starts with this (ex. test)')
parser.add_argument('-ss', '--snapshot', type=str, help='name of the snapshot to roll back to (first available snapshot if not provided)')
parser.add_argument('-s', '--start', action='store_true', help='start virtual machines automatically after reverting')
parser.add_argument('-v', '--verbose', action='count', default=0, help='increase the verbosity level')

parser.add_argument('-pH', '--proxmox-host', type=str, default='PROXMOXHOST', help='Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or 216.47.144.123:443)')
parser.add_argument('-pu', '--proxmox-user', type=str, default='PROXMOXUSER', help='Proxmox username for authentication')
parser.add_argument('-ptn', '--proxmox-token-name', type=str, default='PROXMOXTNAME', help='name of Proxmox authentication token for user')
parser.add_argument('-ptv', '--proxmox-token-value', type=str, default='PROXMOXTVAL', help='value of Proxmox authentication token')
parser.add_argument('-ssl', '--verify-ssl', action='store_true', help='verify SSL certificate on Proxmox host')
parser.add_argument('-pn', '--proxmox-node', type=str, default='PROXMOXNODE', help='node containing virtual machines to revert')

args = parser.parse_args()

# Connect to Proxmox server
pm = ProxmoxAPI(args.proxmox_host, user=args.proxmox_user, token_name=args.proxmox_token_name, token_value=args.proxmox_token_value, verify_ssl=args.verify_ssl)

# Get IDs of virtual machines in Proxmox whose name starts with args.clone_name
print('Checking for virtual machines to revert')
vms = pm.nodes(args.proxmox_node).qemu.get()

vmids = []
to_revert = []

if args.clone_name:
	name = args.clone_name.lower().replace(' ','') + '-'
for vm in vms:
	if args.clone_name and vm['name'].startswith(name):
		print(f'Found virtual machine with name {vm["name"]} and ID {vm["vmid"]}')
		to_revert.append(vm['vmid'])
	else:
		vmids.append(vm['vmid'])

if args.ids:
	extra = valid_ids(args.ids)
	to_revert.extend(extra)

print(f'Reverting the following virtual machines: {to_revert}')
start = 1 if args.start else 0
for vmid in to_revert:
	snapshot = args.snapshot
	if snapshot is None:
		print(f'Obtaining snapshots for virtual machine with ID {vmid}')
		snapshots = pm.nodes(args.proxmox_node).qemu(vmid).snapshot.get()
		snapshot = snapshots[0]['name']
		print(f'Selected snapshot with name {snapshot}')

	print(f'Reverting virtual machine with ID {vmid}')
	pm.nodes(args.proxmox_node).qemu(vmid).snapshot(snapshot).rollback.post(start=start)

	thread = Thread(target=check_locked, args=(vmid,f'Virtual machine with ID {vmid} has been reverted'))
	thread.start()
	threads.append(thread)

# Wait for all threads to complete (all virtual machines reverted) to continue
for thread in threads:
	thread.join()
printc('All virtual machines reverted successfully!\n', Color.GREEN)