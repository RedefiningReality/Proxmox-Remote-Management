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
			print(f'\033[33mNo virtual machine or template found with ID {vmid}\033[0m')
	return valid

# Check virtual machine status every 5 seconds until it has stopped running
def check_stop(vmid):
	while pm.nodes(args.proxmox_node).qemu(vmid).status.current.get()['status'] != 'stopped':
		time.sleep(5)
	print(f'Virtual machine {vmid} has been stopped')

# Parse command line arguments
parser = argparse.ArgumentParser('purge Proxmox virtual machines and corresponding Linux bridge')

parser.add_argument('clone_name', type=str, help='remove virtual machines whose name starts with this (ex. test)')
parser.add_argument('-u', '--user', type=str, nargs='?', const='[CLONE_NAME]', help='remove Proxmox VE user with specified username')
parser.add_argument('-b', '--remove-bridges', action='store_true', help='remove Linux bridges with CLONE_NAME as their description')
parser.add_argument('-bv', '--bridged-vms', type=num_list, help='check virtual machines with the specified IDs for bridge (requires -b)')
parser.add_argument('-f', '--firewall', action='store_true', help='remove interface and DHCP from pfSense firewall configuration (requires -b)')
parser.add_argument('-v', '--verbose', action='count', default=0, help='increase the verbosity level')

parser.add_argument('-pH', '--proxmox-host', type=str, default='PROXMOXHOST', help='Proxmox hostname and/or port number (ex: cyber.ece.iit.edu or 216.47.144.123:443)')
parser.add_argument('-pu', '--proxmox-user', type=str, default='PROXMOXUSER', help='Proxmox username for authentication')
parser.add_argument('-ptn', '--proxmox-token-name', type=str, default='PROXMOXTNAME', help='name of Proxmox authentication token for user')
parser.add_argument('-ptv', '--proxmox-token-value', type=str, default='PROXMOXTVAL', help='value of Proxmox authentication token')
parser.add_argument('-ssl', '--verify-ssl', action='store_true', help='verify SSL certificate on Proxmox host')
parser.add_argument('-pn', '--proxmox-node', type=str, default='PROXMOXNODE', help='node containing virtual machines to template')

parser.add_argument('-fH', '--firewall-host', type=str, default='FIREWALLHOST', help='hostname of pfSense firewall to configure DHCP on through SSH (requires -f)')
parser.add_argument('-fP', '--firewall-port', type=int, default=FIREWALLPORT, help='SSH port for the pfSense firewall (default is 22)')
parser.add_argument('-fu', '--firewall-user', type=str, default='FIREWALLUSER', help='username for the pfSense firewall (requires -f)')
parser.add_argument('-fp', '--firewall-password', type=str, default='FIREWALLPASS', help='password for the pfSense firewall (requires -f)')
parser.add_argument('-ft', '--firewall-timeout', type=float, default=FIREWALLTIMEOUT, help='time in seconds before connection to pfSense times out (default is 5)')
parser.add_argument('-fc', '--firewall-config', type=str, default='FIREWALLCONFIG', help='path to configuration file in pfSense - this should be /cf/conf/config.xml (default) unless using a customised pfSense instance')

args = parser.parse_args()

# Print command line arguments (for debugging)
'''
print("Clone Name:", args.clone_name)
print("Remove Bridges:", args.remove_bridges)
print("Bridged VMs:", args.bridged_vms)
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

if args.user:
	if args.user == '[CLONE_NAME]':
		userid = args.clone_name + '@pve'
	else:
		userid = args.user + '@pve'

	print(f'Removing Proxmox VE user {userid}')
	pm.access.users(userid).delete()
	printc(f'Removed Proxmox VE user {userid}!\n', Color.GREEN)

# Get IDs of virtual machines in Proxmox whose name starts with args.clone_name
print('Checking for virtual machines to remove')
vms = pm.nodes(args.proxmox_node).qemu.get()

vmids = []
clone_ids = []
name = args.clone_name.lower().replace(' ','') + '-'
for vm in vms:
	if vm['name'].startswith(name):
		print(f'Found virtual machine with name {vm["name"]} and ID {vm["vmid"]}')
		clone_ids.append(vm['vmid'])
	else:
		vmids.append(vm['vmid'])

bridged = valid_ids(args.bridged_vms)

print('\nStopping virtual machines')
for vmid in clone_ids:
	print(f'Checking state of virtual machine with ID {vmid}')
	status = pm.nodes(args.proxmox_node).qemu(vmid).status.current.get()['status']

	if status == 'stopped':
		print('Virtual machine is already powered off')
	else:
		print(f'Stopping virtual machine with ID {vmid}')
		pm.nodes(args.proxmox_node).qemu(vmid).status.stop.post()
		# Create thread that runs until virtual machine has stopped
		thread = Thread(target=check_stop, args=(vmid,))
		thread.start()
		threads.append(thread)

# Wait for all threads to complete (all virtual machines shut down) to continue
for thread in threads:
	thread.join()
printc('All specified virtual machines have been stopped!\n', Color.GREEN)

print('Removing virtual machines')
for vmid in clone_ids:
	print(f'Removing virtual machine with ID {vmid}')
	purge_params = {
		'purge': 1,
		'destroy-unreferenced-disks': 1
	}
	pm.nodes(args.proxmox_node).qemu(vmid).delete(**purge_params)
printc(f'Removed all virtual machines whose name started with {name}!\n', Color.GREEN)

if args.remove_bridges:
	print('Checking for Linux bridges to remove')
	networks = pm.nodes(args.proxmox_node).network.get()

	bridges = []
	for network in networks:
		if 'comments' in network and network['comments'] == args.clone_name+'\n':
			bridges.append(network['iface'])
			print(f'Removing Linux bridge {network["iface"]}')
			pm.nodes(args.proxmox_node).network(network['iface']).delete()

	print("Committing changes to the node's interfaces file")
	pm.nodes(args.proxmox_node).network.put()
	printc(f'Removed all Linux bridges with comment {args.clone_name}!\n', Color.GREEN)

	print('Checking specified virtual machines for any network devices associated with removed bridges')
	for vmid in bridged:
		print(f'Checking virtual machine {vmid} for any network devices')
		config = pm.nodes(args.proxmox_node).qemu(vmid).config.get()

		# Every device attached to virtual machine
		for device in config:
			# If the device is a network device, check if it's a bridge
			if device.startswith('net'):
				name_index = config[device].find('bridge=')
				# If it is a bridge, get the name of the bridge device
				if name_index != -1:
					name = config[device][(name_index+7):]
					# Check if the name is in the list of removed bridges
					for bridge in bridges:
						# If it is, remove that network device
						if name.startswith(bridge):
							print(f'Network device {device} found connected to removed bridge {bridge}')
							print(f'Removing network device {device} from virtual machine {vmid}')
							pm.nodes(args.proxmox_node).qemu(vmid).config.put(delete=device)
	printc('Removed all network devices associated with removed bridges!\n', Color.GREEN)

if args.firewall:
	import paramiko
	from scp import SCPClient, SCPException
	import xml.etree.ElementTree as ET

	print(f'Connecting to pfSense firewall at {args.firewall_host} through SSH on port {args.firewall_port}')
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	success = True
	try:
		ssh.connect(args.firewall_host, args.firewall_port, args.firewall_user, args.firewall_password, timeout=args.firewall_timeout)
	except TimeoutError:
		print('Unable to connect to pfSense firewall! Ensure you specified the correct host, port, user, and password and that the firewall is accessible')
		success = False

	if success:
		print('Retrieving configuration file from pfSense')
		scp = SCPClient(ssh.get_transport())
		try:
			scp.get(args.firewall_config, local_path='config.xml')
		except SCPException:
			print('Unable to retrieve configuration file from pfSense! Ensure you specified the correct path')
			scp.close()
			success = False
			
	if success:
		print('Reading retrieved configuration file')
		tree = ET.parse('config.xml')
		root = tree.getroot()

		print('Writing configuration changes to new configuration file')
		interfaces = root.find('interfaces')

		to_remove = []
		for opt in interfaces.findall(f"./*[descr='{args.clone_name}']"):
			to_remove.append(opt.tag)
			interfaces.remove(opt)
		interfaces[len(interfaces)-1].tail = '\n\t'

		dhcpd = root.find('dhcpd')
		for opt in to_remove:
			dhcpd.remove(dhcpd.find(opt))
		if len(dhcpd) > 0:
			dhcpd[len(dhcpd)-1].tail = '\n\t'

		firewall = root.find('filter')
		for opt in to_remove:
			for element in firewall.findall(f"./rule[interface='{opt}']"):
				firewall.remove(element)
		firewall[len(firewall)-1].tail = '\n\t'

		tree.write('config.xml', xml_declaration=True, method='xml', short_empty_elements=False)

		print('Uploading new configuration file to pfSense')
		try:
			scp.put('config.xml', args.firewall_config)
		except SCPException:
			print('Unable to upload configuration file to pfSense!')
		scp.close()
	
	if success:
		print('Reloading pfSense interfaces, firewall rules, and DHCP')
		ssh.exec_command('rm /tmp/config.cache')
			
		command = 'global $debug;'
		command += '$debug = 1;'
		command += 'require_once("filter.inc");'
		command += 'require_once("interfaces.inc");'
		command += 'require_once("services.inc");'
		command += 'require_once("gwlb.inc");'
		command += 'require_once("rrd.inc");'
		command += 'require_once("shaper.inc");'
		for opt in to_remove:
			command += 'interface_bring_down("'+opt+'", true);'
		command += 'services_snmpd_configure();'
		command += 'setup_gateways_monitor();'
		command += 'clear_subsystem_dirty("interfaces");'
		command += 'if (filter_configure() == 0) clear_subsystem_dirty("filter");'
		command += 'enable_rrd_graphing();'
		command += 'if (is_subsystem_dirty("staticroutes") && (system_routing_configure() == 0)) clear_subsystem_dirty("staticroutes");'
		command += 'services_dhcpd_configure();'
		_, _, stderr = ssh.exec_command("/usr/local/bin/php -r '"+command+"'")

		error = stderr.read()
		if len(error) > 0:
			print(f'Reloading pfSense failed! pfSense returned with error {error}')
			success = False
		else:
			print('Reloaded pfSense interfaces, firewall rules, and DHCP')

		ssh.exec_command('exit')
		ssh.close()

	if success:
		printc(f'All destroyed interfaces removed from pfSense configuration!', Color.GREEN)
	else:
		printc('pfSense firewall not configured! Please see errors above.', Color.RED)