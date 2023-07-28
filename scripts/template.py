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

# Check virtual machine status every 5 seconds until it has stopped running
def check_shutdown(vmid):
	while pm.nodes(args.proxmox_node).qemu(vmid).status.current.get()['status'] != 'stopped':
		time.sleep(5)
	print(f'Virtual machine {vmid} has been shut down')

# Parse command line arguments
parser = argparse.ArgumentParser('convert Proxmox virtual machines into clonable templates')

parser.add_argument('ids', type=num_list, help='IDs of virtual machines to template (ex: 7 322,491 or 402,500-503)')
parser.add_argument('-r', '--remove-network', action='store_true', help='remove all network devices from virtual machine templates')
parser.add_argument('-v', '--verbose', action='count', default=0, help='increase the verbosity level')

parser.add_argument('-pH', '--proxmox-host', type=str, default='PROXMOXHOST', help='Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or 216.47.144.123:443)')
parser.add_argument('-pu', '--proxmox-user', type=str, default='PROXMOXUSER', help='Proxmox username for authentication')
parser.add_argument('-ptn', '--proxmox-token-name', type=str, default='PROXMOXTNAME', help='name of Proxmox authentication token for user')
parser.add_argument('-ptv', '--proxmox-token-value', type=str, default='PROXMOXTVAL', help='value of Proxmox authentication token')
parser.add_argument('-ssl', '--verify-ssl', action='store_true', help='verify SSL certificate on Proxmox host')
parser.add_argument('-pn', '--proxmox-node', type=str, default='PROXMOXNODE', help='node containing virtual machines to template')

args = parser.parse_args()

# Print command line arguments (for debugging)
'''
print("IDs:", args.ids)
print("Verbose:", args.verbose)
print("Host:", args.host)
print("User:", args.user)
print("Token Name:", args.token_name)
print("Token Value:", args.token_value)
print("Verify SSL:", args.verify_ssl)
print("Node:", args.proxmox_node)
'''

# Connect to Proxmox server
pm = ProxmoxAPI(args.proxmox_host, user=args.proxmox_user, token_name=args.proxmox_token_name, token_value=args.proxmox_token_value, verify_ssl=args.verify_ssl)

# Get IDs and template status of virtual machines in Proxmox
vms = pm.nodes(args.proxmox_node).qemu.get()

templated = {}
for vm in vms:
    templated[vm['vmid']] = 1 if 'template' in vm and vm['template'] == 1 else 0
vmids = list(templated.keys())

# Check for IDs in args.ids list that don't exist in Proxmox
ids = []
all_ids = []
for vmid in args.ids:
	if vmid in vmids:
		if templated[vmid]:
			printc(f'Virtual machine with ID {vmid} is already a template', Color.YELLOW)
		else:
			ids.append(vmid)
		all_ids.append(vmid)
	else:
		printc(f'No virtual machine found with ID {vmid}', Color.YELLOW)

print('Shutting down virtual machines')
for vmid in ids:
	print(f'Checking state of virtual machine with ID {vmid}')
	status = pm.nodes(args.proxmox_node).qemu(vmid).status.current.get()['status']

	if status == 'stopped':
		print('Virtual machine is already powered off')
	else:
		print(f'Shutting down virtual machine with ID {vmid}')
		pm.nodes(args.proxmox_node).qemu(vmid).status.shutdown.post(forceStop=1)
		# Create thread that runs until virtual machine has shut down
		thread = Thread(target=check_shutdown, args=(vmid,))
		thread.start()
		threads.append(thread)
	
# Wait for all threads to complete (all virtual machines shut down) to continue
for thread in threads:
	thread.join()
printc('All specified virtual machines have been shut down!\n', Color.GREEN)

print('Converting virtual machines to templates')
for vmid in ids:
	print(f'Templating virtual machine with ID {vmid}')
	pm.nodes(args.proxmox_node).qemu(vmid).template.post()

# Ensure all virtual machines are now listed as templates
success = True
for vmid in ids:
	if pm.nodes(args.proxmox_node).qemu(vmid).status.current.get()['template'] != 1:
		printc(f'Failed to create template for virtual machine with ID {vmid}', Color.RED)
		success = False

if success:
	printc(f'All specified virtual machines have been converted to templates!\n', Color.GREEN)

	if args.remove_network:
		print('Removing network devices from all templates')
		
		for vmid in all_ids:
			print(f'Retrieving network devices from virtual machine templates with ID {vmid}')
			config = pm.nodes(args.proxmox_node).qemu(vmid).config.get()
			devices = [device for device in config if device.startswith('net')]

			print(f'Removing network devices: {devices}')
			for device in devices:
				pm.nodes(args.proxmox_node).qemu(vmid).config.put(delete=device)
			print(f'Removed all network devices for virtual machine templates with ID {vmid}')
		
		printc('Removed network devices from all templates!', Color.GREEN)
