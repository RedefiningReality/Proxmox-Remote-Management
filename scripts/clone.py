#!/usr/bin/env python3

import argparse
import time
from threading import Thread
from proxmoxer import ProxmoxAPI
from colors import printc, Color

import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

threads = []
static = {}
cloudinit = {}

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

def static_ip(arg):
	args = arg.split(',')
	return [int(args[0]),args[1]]

# Check for IDs in ids list that don't exist in Proxmox
def valid_ids(ids, accept=[]):
	if ids is None:
		return []

	valid = []
	for vmid in ids:
		if vmid in vmids or vmid in accept:
			valid.append(vmid)
		else:
			printc(f'No virtual machine or template found with ID {vmid}', Color.YELLOW)
	return valid

# Check virtual machine status every 5 seconds until it has finished cloning
def check_cloned(vmid):
	while 'lock' in pm.nodes(args.proxmox_node).qemu(vmid).config.get():
		time.sleep(5)
	print(f'Virtual machine template {vmid} has finished cloning')

# Parse command line arguments
parser = argparse.ArgumentParser('clone Proxmox virtual machine templates')

parser.add_argument('ids', type=num_list, help='IDs of virtual machines to clone (ex: 7 322,491 or 402,500-503)')
parser.add_argument('-c', '--clone-name', type=str, help='name prepended to virtual machine clones')
parser.add_argument('-i', '--clone-begin-id', type=int, default=600, help='clones will be assigned the first available ID after this number (ex. 500 or 600)')
parser.add_argument('-t', '--clone-type', choices=['linked','full'], default='linked', help='the type of clone to create (default is linked)')
parser.add_argument('-s', '--start-clone', action='store_true', help='start cloned virtual machines automatically both on boot and after cloning')

parser.add_argument('-u', '--user', type=str, nargs='?', const='[CLONE_NAME]', help='create a new Proxmox VE user for managing the cloned virtual machines - if not specified, this will default to the clone name')
parser.add_argument('-n', '--name', type=str, help='full name of new Proxmox user (first and last)')
parser.add_argument('-e', '--email', type=str, help='email of new Proxmox user')
parser.add_argument('-p', '--password', type=str, help='password for new Proxmox user (default is a randomly-generated string)')
parser.add_argument('-g', '--groups', type=str, nargs='+', help='groups to add the new Proxmox user to (space-separated)')
parser.add_argument('-r', '--roles', type=str, default='PVEVMUser', help='roles to assign to the user (default is builtin PVEVMUser)')

parser.add_argument('-b', '--create-bridge', action='store_true', help='create a new Linux bridge for these virtual machines')
parser.add_argument('-bs', '--bridge-subnet', type=str, help='add new bridge with subnet specified in CIDR notation (ex: 10.0.2.0/24)')
parser.add_argument('-bp', '--bridge-ports', type=str, help='attach ports/slaves to the new bridge (ex. eno1)')
parser.add_argument('-bv', '--add-bridged-vms', type=num_list, help='add the new bridge to the virtual machines with the specified IDs or clones of templates with the specified IDs (requires -b)')
parser.add_argument('-cs', '--cloud-init-static', type=static_ip, default=[], nargs='+', help='IP address for bridged VM with specified ID or clone created from template with specified ID - VM MUST have cloud-init installed - format is <ID>,<IP> (ex. 500,10.0.2.2 402,10.0.2.3)')

parser.add_argument('-f', '--firewall', action='store_true', help='configure pfSense firewall to serve DHCP on newly-created bridge (requires -b)')
parser.add_argument('-fi', '--firewall-ip', type=str, help='local IPv4 address of the pfSense firewall (subnet ending in .1 if not specified)')
parser.add_argument('-db', '--dhcp-begin', type=str, help='DHCP pool begin address')
parser.add_argument('-de', '--dhcp-end', type=str, help='DHCP pool end address')
parser.add_argument('-dd', '--dhcp-dns', type=str, nargs='+', help='DNS servers to use for this subnet - served with DHCP (ex. 1.1.1.1 8.8.8.8)')
parser.add_argument('-ds', '--dhcp-static', type=static_ip, nargs='+', help='DHCP static lease for bridged VM with specified ID or clone created from template with specified ID - format is <ID>,<IP> (ex. 500,10.0.2.2 402,10.0.2.3)')
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

clone_name = '' if args.clone_name is None else args.clone_name
if args.user:
	if args.user == '[CLONE_NAME]':
		if args.clone_name:
			userid = args.clone_name + '@pve'
		else:
			exit('Must specify username for new Proxmox VE user with either -u or -c')
	else:
		userid = args.user + '@pve'

# Print command line arguments (for debugging)
'''
print("IDs:", args.ids)
print("Clone Name:", args.clone_name)
print("Clone Begin ID:", args.clone_begin_id)
print("Clone Type:", args.clone_type)
print("Start Clone:", args.start_clone)
print("Create Bridge:", args.create_bridge)
print("Bridge Subnet:", args.bridge_subnet)
print("DHCP Begin:", args.dhcp_begin)
print("DHCP End:", args.dhcp_end)
print("Add Bridged VMs:", args.add_bridged_vms)
print("Firewall Host:", args.firewall_host)
print("Firewall Port:", args.firewall_port)
print("Firewall Username:", args.firewall_username)
print("Firewall Password:", args.firewall_password)
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

# Get IDs and names of virtual machines in Proxmox
vms = pm.nodes(args.proxmox_node).qemu.get()
vm_names = {}
for vm in vms:
    vm_names[vm['vmid']] = vm['name']
vmids = list(vm_names.keys())

ids = valid_ids(args.ids)
bridged = valid_ids(args.add_bridged_vms, accept=ids)

# cloud-init will contain args.cloud_init_static as dictionary with only valid IDs
for pair in args.cloud_init_static:
	if pair[0] in bridged or pair[0] in ids:
		cloudinit[pair[0]] = pair[1]

# static will contain args.dhcp_static as dictionary with only valid IDs
if args.firewall and args.dhcp_static is not None:
	for pair in args.dhcp_static:
		if pair[0] in bridged or pair[0] in ids:
			static[pair[0]] = pair[1]

if args.create_bridge:
	print(f'Determining next available Linux bridge name')
	networks = pm.nodes(args.proxmox_node).network.get()
	ifaces = [network['iface'] for network in networks]

	# Get biggest number after 'vmbr' in names of existing bridges (used to create new bridge name)
	biggest = -1
	for iface in ifaces:
		if iface.startswith('vmbr'):
			num = int(iface[4:])
			if num > biggest:
				biggest = num
	iface = 'vmbr' + str(biggest+1)
	print(f'Next available Linux bridge name: {iface}')

	params = {
		'type': 'bridge',
		'iface': iface,
		'cidr': args.bridge_subnet,
		'autostart': 1,
		'comments': clone_name
	}

	if args.bridge_ports:
		params['bridge_ports'] = args.bridge_ports

	print(f'Creating new Linux bridge')
	pm.nodes(args.proxmox_node).network.post(**params)
	pm.nodes(args.proxmox_node).network.put()
	printc(f'Created new Linux bridge with name {iface}!\n', Color.GREEN)

print(f'Finding available IDs for clones, starting at ID {args.clone_begin_id}')
clone_ids = []
clone_id = args.clone_begin_id
for _ in range(len(ids)):
	while clone_id in vmids:
		clone_id += 1
	clone_ids.append(clone_id)
	clone_id += 1
print(f'Found available IDs for clones: {clone_ids}')

print('Cloning virtual machine templates')
for i, vmid in enumerate(ids):
	newid = clone_ids[i]
	if args.clone_name is None:
		name = vm_names[vmid]
	else:
		name = args.clone_name.lower().replace(' ','') + '-' + vm_names[vmid]
	full = 1 if args.clone_type == 'full' else 0

	print(f'Cloning virtual machine template with ID {vmid} to {newid}')
	pm.nodes(args.proxmox_node).qemu(vmid).clone.post(newid=newid, name=name, full=full)

	if vmid in bridged:
		bridged.append(newid)
		bridged.remove(vmid)

	# Replace template ID with clone ID
	# cloudinit will contain ID: IP address for all VMs
	if vmid in cloudinit.keys():
		cloudinit[newid] = cloudinit[vmid]
		del cloudinit[vmid]

	# Replace template ID with clone ID
	# static will contain ID: IP address for all VMs
	if args.firewall and vmid in static.keys():
		static[newid] = static[vmid]
		del static[vmid]
	
	thread = Thread(target=check_cloned, args=(newid,))
	thread.start()
	threads.append(thread)

# Wait for all threads to complete (all virtual machines cloned) to continue
for thread in threads:
	thread.join()
printc('All virtual machine templates cloned successfully!\n', Color.GREEN)

if args.create_bridge:
	#bridged += clone_ids
	print(f'Adding new Linux bridge to the desired virtual machines')

	for vmid in bridged:
		print(f'Determining next available network device name for virtual machine with ID {vmid}')
		config = pm.nodes(args.proxmox_node).qemu(vmid).config.get()

		# Get biggest number after 'net' in names of existing devices (used to create new device name)
		biggest = -1
		for device in config:
			if device.startswith('net'):
				num = int(device[3:])
				if num > biggest:
					biggest = num
		device = 'net' + str(biggest+1)
		print(f'Next available device name: {device}')

		print(f'Adding Linux bridge to virtual machine with ID {vmid}')
		bridge = 'virtio,bridge='+iface+',firewall=1'
		params = {device: bridge}

		# Assign cloud-init IP if applicable
		if vmid in cloudinit.keys():
			ipconfig = 'ipconfig'+str(biggest+1)
			_, subnet = args.bridge_subnet.split('/')
			ip = 'ip='+cloudinit[vmid]+'/'+subnet
			params[ipconfig] = ip

		pm.nodes(args.proxmox_node).qemu(vmid).config.put(**params)

		# Replace ID with MAC address
		# static will contain MAC address: IP address for all VMs
		if args.firewall and vmid in static.keys():
			print(f'Retreiving MAC address of network device {device}')
			config = pm.nodes(args.proxmox_node).qemu(vmid).config.get()
			dev = config[device]
			idx = dev.index('virtio=')+7
			mac = dev[idx:idx+17]
			ip = static[vmid]
			print(f'MAC address: {mac}')

			print(f'Saving DHCP static configuration {mac}<=>{ip}')
			static[mac] = ip
			del static[vmid]

	printc('Linux bridge added to all desired virtual machines!\n', Color.GREEN)

	if args.firewall:
		import paramiko
		from scp import SCPClient, SCPException
		import xml.etree.ElementTree as ET

		def subelement(elt, tag, text='', tail='\n\t\t\t'):
			""" Create and return new XML configuration element  """
			new = ET.SubElement(elt, tag)
			# Attempt to preserve some of the formatting of pfSense's config.xml
			new.text = text
			new.tail = tail
			return new

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
			print('Retrieving interfaces from pfSense')
			# print out lines starting with vtnet and get part before : (vtnet[num])
			_, stdout, _ = ssh.exec_command("ifconfig | grep -E '^vtnet' | cut -d':' -f1")
			lines = stdout.readlines()
			interface = lines[len(lines)-1][:-1]
			print(f'Found newly created interface {interface}')

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
			last = interfaces[len(interfaces)-1]

			num = 0
			if last.tag.startswith('opt'):
				num = int(last.tag[3:])+1
			new_name = 'opt' + str(num)

			last.tail = '\n\t\t'
			new = subelement(interfaces, new_name, text='\n\t\t\t', tail='\n\t')

			netaddr, subnet = args.bridge_subnet.split('/')
			ipaddr = args.firewall_ip if args.firewall_ip else netaddr[:-1] + str(int(netaddr[-1:])+1)

			#subelement(new, 'descr', text=ET.CDATA(args.clone_name))
			subelement(new, 'descr', text=args.clone_name)
			subelement(new, 'if', text=interface)
			subelement(new, 'enable')
			subelement(new, 'ipaddr', text=ipaddr)
			subelement(new, 'subnet', text=subnet)
			subelement(new, 'spoofmac', tail='\n\t\t')

			if (args.dhcp_begin and args.dhcp_end) or args.dhcp_static:
				dhcpd = root.find('dhcpd')
				if len(dhcpd) == 0:
					dhcpd.text = '\n\t\t'
				else:
					dhcpd[len(dhcpd)-1].tail = '\n\t\t'
				opt = subelement(dhcpd, new_name, text='\n\t\t\t', tail='\n\t')

				ip_range = subelement(opt, 'range', text='\n\t\t\t\t')
				from_text = args.dhcp_begin if args.dhcp_begin else ''
				to_text = args.dhcp_end if args.dhcp_end else ''
				subelement(ip_range, 'from', text=from_text, tail='\n\t\t\t\t')
				subelement(ip_range, 'to', text=to_text)

				common = ['defaultleasetime',
					'maxleasetime', 'gateway', 'domain', 'domainsearchlist',
					'ddnsdomain', 'ddnsdomainprimary', 'ddnsdomainsecondary',
					'ddnsdomainkeyname', 'ddnsdomainkey',
					'tftp', 'ldap', 'nextserver', 'filename', 'filename32', 'filename64',
					'filename32arm', 'filename64arm', 'uefihttpboot', 'rootpath',
					'numberoptions']

				to_add = common + ['enable', 'failover_peerip','netmask', 'mac_allow', 'mac_deny']
				for tag in to_add:
					subelement(opt, tag)
				subelement(opt, 'ddnsdomainkeyalgorithm', text='hmac-md5')
				last = subelement(opt, 'ddnsclientupdate', text='allow')
				for dnsserver in args.dhcp_dns:
					last = subelement(opt, 'dnsserver', text=dnsserver)

				to_add = common + ['cid', 'hostname', 'descr']
				for mac in static.keys():
					last = subelement(opt, 'staticmap', text='\n\t\t\t\t')
					for tag in to_add:
						subelement(last, tag, tail='\n\t\t\t\t')
					subelement(last, 'mac', text=mac, tail='\n\t\t\t\t')
					subelement(last, 'ipaddr', text=static[mac])
				last.tail = '\n\t\t'

			start = int(time.time())

			firewall = root.find('filter')
			#firewall[len(firewall)-2].tail = '\n\t\t'
			
			separator = firewall.find('separator')
			if separator:
				separator[len(separator)-1].tail = '\n\t\t\t'
				subelement(separator, new_name, tail='\n\t\t')

			rule = ET.Element('rule')
			rule.text = '\n\t\t\t'
			rule.tail = '\n\t\t'
			firewall.insert(len(firewall)-1, rule)

			subelement(rule, 'type', text='pass')
			subelement(rule, 'ipprotocol', text='inet')
			subelement(rule, 'descr', text='Default allow LAN to any rule')
			subelement(rule, 'interface', text=new_name)
			subelement(rule, 'tracker', text=str(start))
			source = subelement(rule, 'source', text='\n\t\t\t\t')
			destination = subelement(rule, 'destination', text='\n\t\t\t\t', tail='\n\t\t')
			subelement(source, 'network', text=new_name)
			subelement(destination, 'any')

			rule = ET.Element('rule')
			rule.text = '\n\t\t\t'
			rule.tail = '\n\t\t'
			firewall.insert(len(firewall)-1, rule)

			subelement(rule, 'type', text='pass')
			subelement(rule, 'ipprotocol', text='inet6')
			subelement(rule, 'descr', text='Default allow LAN IPv6 to any rule')
			subelement(rule, 'interface', text=new_name)
			subelement(rule, 'tracker', text=str(start+1))
			source = subelement(rule, 'source', text='\n\t\t\t\t')
			destination = subelement(rule, 'destination', text='\n\t\t\t\t', tail='\n\t\t')
			subelement(source, 'network', text=new_name)
			subelement(destination, 'any')

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
			command += 'interface_bring_down("'+new_name+'", false);'
			command += 'interface_configure("'+new_name+'", true);'
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
			printc(f'pfSense firewall configured and serving DHCP for bridge {iface}!\n', Color.GREEN)
		else:
			printc('pfSense firewall not configured! Please see errors above.\n', Color.RED)

if args.user:
	print(f'Creating Proxmox VE user {userid}')

	users = pm.access.users.get()
	userids = [user['userid'] for user in users]

	if userid in userids:
		print(f'Proxmox VE user {userid} already exists!\n', Color.YELLOW)
	else:
		params = {}

		params['userid'] = userid
		params['groups'] = ','.join(args.groups) if args.groups and len(args.groups)>0 else ''
		params['email'] = args.email if args.email else ''

		proxmox_name = args.name if args.name else ''
		words = proxmox_name.split(' ')
		if len(words) < 2:
			params['firstname'] = proxmox_name
			params['lastname'] = ''
		else:
			params['firstname'] = words[0]
			params['lastname'] = words[len(words)-1]

		if args.password:
			params['password'] = args.password
		else:
			import random, string
			print('Generating random password for Proxmox user')
			password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
			print(f'Randomly-generated password: {password}')
			params['password'] = password

		pm.access.users.post(expire=0, **params)
		printc(f'Created Proxmox VE user {userid}!\n', Color.GREEN)
	
	print('Assigning permissions to user')
	for vmid in clone_ids:
		print(f'Granting access to virtual machine with ID {vmid}')
		params.clear()

		params['path'] = '/vms/' + str(vmid)
		params['users'] = userid
		params['roles'] = args.roles

		pm.access.acl.put(propagate=1, **params)
	printc(f'User {userid} granted access to all cloned virtual machines!\n', Color.GREEN)

if args.start_clone:
	print('Starting virtual machine clones')

	for vmid in clone_ids:
		print(f'Setting virtual machine with ID {vmid} to start on boot')
		pm.nodes(args.proxmox_node).qemu(vmid).config.put(onboot=1)
		print(f'Starting virtual machine with ID {vmid}')
		pm.nodes(args.proxmox_node).qemu(vmid).status.start.post()
	
	printc('All virtual machine clones have been started!', Color.GREEN)
