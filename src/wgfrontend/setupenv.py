#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import getpass
import grp
import ipaddress
import os
import pwd
import string
import subprocess
import textwrap
import wgconfig
import wgconfig.wgexec as wgexec

from . import config
from . import exechelper
from . import setupenv_alpine


def is_root():
    """Returns whether this script is run with user is 0 (root)"""
    return os.getuid() == 0
    
def get_user():
    """Returns the effective user that executes this script"""
    return getpass.getuser()

def check_user(username):
    """Returns a boolean that indicates if the given user exists on the system"""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def create_user(username):
    """Create the given user on the system"""
    if os.path.exists('/usr/sbin/useradd'):
        os.system(f'useradd {username}')
    else:
        os.system(f'adduser {username} -D')
    
def ensure_user(username):
    """Ensures that the given user exists on the system"""
    if not check_user(username):
        create_user(username)

def check_wg():
    """Check whether the wg tool is present"""
    return os.path.isfile('/usr/bin/wg')

def check_wgquick():
    """Check whether the wg-quick tool is present"""
    return os.path.isfile('/usr/bin/wg-quick')

def touch_file(filename, perm=0o640):
    """Touch the given file with the provided permissions"""
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    with os.fdopen(os.open(filename, os.O_WRONLY | os.O_CREAT, perm), 'w') as handle:
        pass

def check_validcharacters(value, valid_chars=string.ascii_letters):
    """Checks whether the provided string only contains the listed characters"""
    invalid = [ k for k in value if k not in valid_chars ]
    if invalid:
        return False
    return True

def chown(username, path):
    """Change file/path ownership to given user"""
    uid = pwd.getpwnam(username).pw_uid
    os.chown(path, uid, -1)

def get_uid_gid(uid_name='nobody', gid_name='nogroup'):
    """Returns uid and gid for the given username and groupname"""
    uid = pwd.getpwnam(uid_name).pw_uid
    gid = grp.getgrnam(gid_name).gr_gid
    return uid, gid

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    """Drop privileges towards the given username and groupname"""
    if not is_root():
        raise ValueError('No privileges present to drop')
    uid, gid = get_uid_gid(uid_name, gid_name) 
    os.setgroups([]) # remove group privileges
    os.setgid(gid)
    os.setuid(uid)

def get_primary_interface():
    """Returns the name of the network interface having the default route"""
    exitcode, interface_name = subprocess.getstatusoutput("ip route | awk '/default/ { print $5 }'")
    if exitcode == 0:
        return interface_name
    else:
        return None

def get_primary_interface_addr4():
    """Returns the first IPv4 address of the network interface having the default route"""
    interface_name = get_primary_interface()
    if interface_name is None:
        return None
    exitcode, output = subprocess.getstatusoutput(f'ip addr show dev {interface_name}' + "| awk '/inet / { print $2 }'")
    if exitcode == 0:
        addr4 = output.partition('\n')[0] # get first line
        return addr4
    else:
        return None


class QueryUser():
    """Interact with the user"""

    def __init__(self):
        """Object initialization"""
        self._expert = None

    def input_yes_no(self, display_text, default='Yes'):
        """Queries the user for a yes or no answer"""
        while True:
            answer = input(f'  {display_text} ')
            answer = answer.strip()
            if not answer:
                answer = default
            answer = answer.lower()
            if answer in ['1', 'y', 'yes']:
                return True
            if answer in ['0', 'n', 'no']:
                return False
            print('   Invalid answer. Please answer yes or no.') 

    def query_expert(self):
        """Queries the user on whether he wants expert configuration"""
        expert = self.input_yes_no('Do you want to use expert configuration? [No]:', default='No')
        return expert

    @property
    def expert(self):
        """Query user on first run on whether expert configuration is desired and remember result"""
        if self._expert is None:
            self._expert = self.query_expert()
        return self._expert

    def get_input(self, display_text):
        """Queries the user for input"""
        userdata = input(f'  {display_text} ')
        userdata = userdata.strip()
        return userdata

    def get_and_validate_input(self, display_text, default=None, check_function=None, expert_question=False):
        """Queries the user for input and validates it"""
        if expert_question and not self.expert:
            return default
        ok = False
        while not ok:
            userdata = self.get_input(display_text)
            if not userdata:
                userdata = default
            if check_function is None:
                ok = True
            else:
                userdata = check_function(userdata)
                if userdata:
                    ok = True
        if userdata:
            return userdata
        else:
            return default

    def get_wg_configfile(self):
        """Query the user for the path of the WireGuard config file"""
        return self.get_and_validate_input('Please specify the WireGuard config file to be used [/etc/wireguard/wg_rw.conf]:', default='/etc/wireguard/wg_rw.conf', expert_question=True)

    def get_system_user(self):
        """Query the user for the system user for the web frontend"""
        return self.get_and_validate_input('Please specify the system user for the web frontend [wgfrontend]:', default='wgfrontend', expert_question=True)

    def get_socket_host(self):
        """Query the user for the listening interface for the web server"""

        def check(userdata):
            if check_validcharacters(userdata, string.hexdigits + '.:'):
                return userdata
            print('    Invalid characters entered. Please enter anew.')
            return None

        return self.get_and_validate_input('Please specify the listening interface for the web server [0.0.0.0]:', default='0.0.0.0', check_function=check, expert_question=True)

    def get_socket_port(self):
        """Query the user for the listening port for the web server"""

        def check(userdata):
            if (not userdata) or userdata.isdigit():
                return userdata
            print('    You need to provide a port number. Please enter anew.')
            return None

        return self.get_and_validate_input('Please specify the listening port for the web server [8080]:', default='8080', check_function=check, expert_question=True)

    def get_frontend_username(self):
        """Query the user for the username for the web frontend user"""

        def check(userdata):
            if check_validcharacters(userdata, string.ascii_letters + '_'):
                return userdata
            print('    Username must only contain letters and underscores. Please enter anew.')
            return None

        return self.get_and_validate_input('Please specify the username for your web frontend user [admin]:', default='admin', check_function=check, expert_question=False)

    def get_frontend_password(self):
        """Query the user for the password for the web frontend user"""

        def check(userdata):
            if len(userdata) >= 8:
                return userdata
            print('    Password must have at least eight characters. Please enter anew.')
            return None

        return self.get_and_validate_input('Please specify the password for your web frontend user:', check_function=check, expert_question=False)

    def get_wg_listenport(self):
        """Query the user for the listen port of the WireGuard interface"""

        def check(userdata):
            if str(userdata).isdigit():
                return int(userdata)
            print('    You need to provide a numeric port number. Please enter anew.')
            return None

        return self.get_and_validate_input('Please specify the listen port of the WireGuard interface [51820]:', default=51820, check_function=check, expert_question=False)

    def get_endpoint(self):
        """Query the user for the endpoint hostname (and optionally port) to reach the WireGuard server"""

        def check(userdata):
            if len(userdata) > 0:
                return userdata
            print('    You need to enter an endpoint hostname. Please enter anew.')
            return None

        print('  You need to specify the endpoint hostname (and optionally port) to reach your WireGuard server.')
        print('  In a home environment, this is usually a DynDNS name denoting your Internet router.')
        return self.get_and_validate_input('Please specify the endpoint hostname (and optionally port) to reach your WireGuard server:', default='', check_function=check, expert_question=False)

    def get_wg_address(self):
        """Query the user for the IP address of the WireGuard interface incl. prefix length"""

        def check(userdata):
            try:
                userdata = ipaddress.ip_interface(userdata)
                return userdata
            except e:
                print('  Exception: {text}'.format(text=str(e)))
            return None

        return self.get_and_validate_input('Please specify the IP address of the WireGuard interface incl. prefix length [192.168.0.1/24]:', default='192.168.0.1/24', check_function=check, expert_question=False)

    def get_wg_networks(self):
        """Query the user for the network ranges that the clients shall route to the WireGuard server"""
        return self.get_and_validate_input('Please specify the network ranges that the clients shall route to the WireGuard server [192.168.0.0/16]:', default='192.168.0.0/16', expert_question=False)


def setup_environment():
    """Environment setup assistant"""
    cfg = config.Configuration()
    if is_root():
        qu = QueryUser()
        print('Welcome to Towalink WireGuard Frontend')
        print('======================================')
        print('You are executing "wgfrontend" as root user. We\'ll now make sure that everything is properly installed.')
        if check_wg():
            print('Wireguard (wg) is available. Ok.')
        else:
            print('Wireguard (wg) is not available. FAIL.')
        if check_wg():
            print('Wireguard (wg-quick) is available. Ok.')
        else:
            print('Wireguard (wg-quick) is not available. FAIL.')
        if cfg.exists():
            print(f'Config file {cfg.filename} already exists. Ok.')
        else:
            print(f'Config file {cfg.filename} does not yet exist. Let\'s create one...')
            print('  Press enter to select defaults.')
            wg_configfile = qu.get_wg_configfile()
            user = qu.get_system_user()
            socket_host = qu.get_socket_host() # listening interface for the web server
            socket_port = qu.get_socket_port() # listening port for the web server
            username = qu.get_frontend_username()
            password = qu.get_frontend_password()
            touch_file(cfg.filename, perm=0o640) # create without world read permissions
            cfg.write_config(wg_configfile=wg_configfile, socket_host=socket_host, socket_port=socket_port, user=user, users={username: password})
            print('  Config file written. Ok.')
        print(f'Ensuring that system user "{cfg.user}" exists.')
        ensure_user(cfg.user)
        print(f'Ensuring ownership of config file {cfg.filename}.')
        chown(cfg.user, cfg.filename)
        if os.path.exists(cfg.libdir):
            print(f'Directory {cfg.libdir} already exists. Ok.')
        else:
            print(f'Directory {cfg.libdir} does not yet exist. Let\'s create it...')
            os.makedirs(cfg.libdir, mode=0o750, exist_ok=True)
            print('  Directory created. Ok.')
        print(f'Ensuring ownership of directory {cfg.libdir}.')
        chown(cfg.user, cfg.libdir)
        if os.path.exists(cfg.wg_configfile):
            print(f'WireGuard config file {cfg.wg_configfile} already exists. Ok.')
        else:
            print(f'WireGuard config file {cfg.wg_configfile} does not yet exist. Let\'s create one...')
            print('  For documentation on possible setups, please refer to')
            print('  https://github.com/towalink/wgfrontend/tree/main/doc/network-integration')
            print('  Automated configuration is only supported for the ProxyARP setup.')
            print('  For this, choose an unused subrange of your local network for WireGuard.')
            print('  Press enter to select defaults.')
            wg_listenport = qu.get_wg_listenport()
            endpoint = qu.get_endpoint()
            wg_address_obj = qu.get_wg_address()
            wg_networks = qu.get_wg_networks()
            # Check for ProxyARP setup
            proxy_arp_interface = None
            eth_address = get_primary_interface_addr4()
            if (eth_address is not None) and (len(eth_address) > 0):
                eth_address_obj = ipaddress.ip_interface(eth_address)
                if wg_address_obj.network.subnet_of(eth_address_obj.network):
                    interface_name = get_primary_interface()
                    print('  Setup for ProxyARP detected.')
                    if qu.input_yes_no(f'7e) Do you want to configure ProxyARP on interface {interface_name} when bringing up the WireGuard interface? [Yes]: '):
                        proxy_arp_interface = interface_name
                else:
                    print('  Please configure your network setup based on the documentation referenced above.')
            # Write WireGuard config file
            wc = wgconfig.WGConfig(cfg.wg_configfile)
            wc.initialize_file('# This file has been created and is managed by wgfrontend. Only change manually if you know what you\'re doing.')
            if not ':' in endpoint:
                endpoint += ':51820'
            wc.add_attr(None, 'ListenPort', wg_listenport, '# Endpoint = ' + endpoint, append_as_line=True)
            wc.add_attr(None, 'PrivateKey', wgexec.generate_privatekey())
            wc.add_attr(None, 'Address', wg_address_obj.compressed, '# Networks = ' + wg_networks, append_as_line=True)
            if proxy_arp_interface is not None:
                wc.add_attr(None, 'PostUp', f'sysctl -w net.ipv4.conf.{proxy_arp_interface}.proxy_arp=1', append_as_line=True)
            wc.write_file()
            print('  Config file written. Ok.')
            eh = exechelper.ExecHelper()
            if qu.input_yes_no(f'Would you like to allow the system user of the web frontend to reload WireGuard on config on changes (using sudo)? [Yes]:'):
                sudoers_content = textwrap.dedent(f'''\
                    {cfg.user}  ALL=(root) NOPASSWD: /etc/init.d/wgfrontend_interface start, /etc/init.d/wgfrontend_interface stop, /etc/init.d/wgfrontend_interface restart
                    {cfg.user}  ALL=(root) NOPASSWD: /usr/bin/wg-quick down {cfg.wg_configfile}, /usr/bin/wg-quick up {cfg.wg_configfile}
                ''')    
                if os.path.isdir('/etc/sudoers.d'):
                    with open('/etc/sudoers.d/wgfrontend', 'w') as sudoers_file:
                        sudoers_file.write(sudoers_content)
                else:
                    print('  Sorry, "/etc/sudoers.d" does not exist so that sudo could not be configured. Maybe "sudo" is not installed.')
            if qu.input_yes_no(f'Would you like to activate the WireGuard interface "{cfg.wg_interface}" now? [Yes]:'):
                eh.run_wgquick('up', cfg.wg_interface)
            if qu.input_yes_no(f'Would you like to activate the WireGuard interface "{cfg.wg_interface}" on boot? [Yes]:'):
                if eh.os_id == 'alpine':
                    setupenv_alpine.start_wginterface_onboot()
                else:
                    eh.enable_service(f'wg-quick@{cfg.wg_interface}')
            if qu.input_yes_no(f'Would you like to start wgfrontend on boot? [Yes]:'):
                if eh.os_id == 'alpine':
                    setupenv_alpine.start_wgfrontend_onboot()
                else:
                    print('  Sorry, this can\'t be configured by this assistant on your platform yet.')
        print(f'Ensuring list permission of WireGuard config directory {os.path.dirname(cfg.wg_configfile)}.')
        os.chmod(os.path.dirname(cfg.wg_configfile), 0o711)
        print(f'Ensuring ownership of WireGuard config file {cfg.wg_configfile}.')
        chown(cfg.user, cfg.wg_configfile)
        if os.path.exists(cfg.sslcertfile):
            print(f'Ensuring ownership of server certificate file {cfg.sslcertfile}.')
            chown(cfg.user, cfg.sslcertfile)
        if os.path.exists(cfg.sslkeyfile):
            print(f'Ensuring ownership of server private key file {cfg.sslkeyfile}.')
            chown(cfg.user, cfg.sslkeyfile)    
        print()
        print('Attempting to start web frontend...')
    return cfg


if __name__ == '__main__':
    setup_environment()
