import argparse
import platform
import socket
import os, sys, shutil, subprocess
import pwd

sys.path.append('scripts')
from colors import printc, Color

service = 'apache2'
web_users = ['www-data', 'apache', 'apache2', 'httpd']
sessions = '/var/www/html/sessions'

web_dir = 'web/'
web = ['index.php', 'login.php', 'logout.php', 'password.php', 'register.php', 'scripts.php', 'test.php', 'creds.php']
config = 'config.ini'

tls = ['tls.crt', 'tls.key']
apache_config = 'default.conf'

def replace(file, params):
    print(f'Writing changes to file {file}')
    data = open(file, 'r').read()
    for original, new in params.items():
        data = data.replace(original, new)
    open(file, 'w').write(data)
    print(f'Wrote all changes to file {file}')

def move(source, destination):
    print(f'Moving file {source} to directory {destination}')

    if not os.path.isfile(source):
        printc(f'File {source} not found!', Color.RED)
        exit

    if not os.path.exists(destination):
        os.makedirs(destination)
    
    new = os.path.join(destination, os.path.basename(source))
    try:
        result = shutil.move(source, new)
        print(f'Moved file {source} to directory {destination}')
        return result
    except Exception as e:
        printc(f'Failed to move file {source} to directory {destination}', Color.RED)
        print(f'Exception: {e}')
        exit

def run_command(command):
    print(f'Running command: {command}')
    try:
        subprocess.run(command.split(' '), check=True)
    except subprocess.CalledProcessError as e:
        printc(f'Command failed!', Color.RED)
        print(f'Return code: {e.returncode}')
        print(f'Error output: {e.output}')
        exit

# Parse command line arguments
parser = argparse.ArgumentParser('configure apache2 web server to securely serve web files')

parser.add_argument('-u', '--web-user', type=str, help='user that will be running apache2 (detected automatically if not specified)')
parser.add_argument('-d', '--domain-name', type=str, help='domain name or IP address for website - used to redirect HTTP requests on port 80 to HTTPS on port 443')
parser.add_argument('-tc', '--tls-crt', type=str, help='path to TLS crt file for SSL/TLS on webpages')
parser.add_argument('-tk', '--tls-key', type=str, help='path to TLS key file for SSL/TLS on webpages')
parser.add_argument('-c', '--config-path', type=str, help='desired directory to place web configuration file (config.ini)')

args = parser.parse_args()

if args.web_user:
    web_user = pwd.getpwnam(args.web_user)
    uid = web_user.pw_uid
    gid = web_user.pw_gid
else:
    print('Automatically detecting web user')
    for p in pwd.getpwall():
        if p.pw_name in web_users:
            uid = p.pw_uid
            gid = p.pw_gid
            printc(f'Found web user {p.pw_name}!\n', Color.GREEN)
            break
    else:
        printc('Web user not found!', Color.RED)
        print('Are you sure you installed apache2 correctly?')
        print('If so, please rerun and specify web user with -u [user]')

if args.domain_name is None:
    args.domain_name = input('Enter domain name or IP address used to visit website: ')

printc('It is highly recommended that you create a custom TLS certificate for serving the website securely', Color.YELLOW)
print('This can be self-signed with openssl or a free signed certificate from LetsEncrypt')
print('Using defaults (pressing enter) for the following 2 options will use the self-signed cert packaged in this repo')
print('Note that this cert will present a warning message in browsers since it\'s self-signed, and it may be expired')

if args.tls_crt is None:
    args.tls_crt = input('Enter path to .crt file for TLS certificate (or leave blank): ')

if args.tls_crt == '':
    args.tls_crt = web_dir+tls[0]

if args.tls_key is None:
    args.tls_key = input('Enter path to .key file for TLS certificate (or leave blank): ')

if args.tls_key == '':
    args.tls_key = web_dir+tls[1]

params = {
    'DOMAIN': args.domain_name,
    'TLSCRT': move(args.tls_crt, '/etc/ssl/certs'),
    'TLSKEY': move(args.tls_key, '/etc/ssl/private')
}
replace(web_dir+apache_config, params)
move(web_dir+apache_config, f'/etc/{service}/sites-available')

run_command('a2enmod ssl')
run_command('a2ensite default.conf')
printc('Apache2 configuration created and enabled!\n', Color.GREEN)

if args.config_path is None:
    args.config_path = input('Enter desired destination directory for web configuration file config.ini (default is current directory): ')

if args.config_path == '':
    args.config_path = os.getcwd()

config = move(web_dir+config, args.config_path)
printc('Created website configuration file config.ini!\n', Color.GREEN)

print('Removing existing pages in web directory')
run_command('rm -rf /var/www/html')
print('Removed all existing pages')

print('Updating php scripts and moving them to default web directory')
for file in web:
    replace(web_dir+file, {'config.ini': config})
    move(web_dir+file, '/var/www/html')
    
print('Creating sessions file')
with open(sessions, 'w') as fp:
    pass
print('Setting ownership of sessions file')
os.chown(sessions, uid, gid)
printc('Web directory is now hosting all site files!\n', Color.GREEN)

print('Setting apache2 web service to start on boot')
run_command(f'systemctl enable {service}')
printc('Web service prepared and will start on boot\n', Color.GREEN)

printc(f'To manage site preferences, update your configuration in {config}', Color.YELLOW)
printc(f'Then reboot or run the following to start your webserver: systemctl start {service}', Color.YELLOW)