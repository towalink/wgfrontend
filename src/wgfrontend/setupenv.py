#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import getpass
import grp
import ipaddress
import os
import pwd
import string
import subprocess
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

def input_yes_no(info, default='Yes'):
    """Queries the user for a yes or no answer"""
    while True:
        answer = input(info)
        if not answer.strip():
            answer = default
        answer = answer.lower()
        if answer in ['1', 'y', 'yes']:
            return True
        if answer in ['0', 'n', 'no']:
            return False
        print('   Invalid answer. Please answer yes or no.') 

def setup_environment():
    """Environment setup assistant"""
    cfg = config.Configuration()
    if is_root():
        print('Welcome to Towalink WireGuard Frontend')
        print('======================================')
        print('You are executing "wgfrontend" as root user. We\'ll now make sure that everything is properly installed.')
        if check_wg():
            print(f'1a) Wireguard (wg) is available. Ok.')
        else:
            print(f'1a) Wireguard (wg) is not available. FAIL.')
        if check_wg():
            print(f'1b) Wireguard (wg-quick) is available. Ok.')
        else:
            print(f'1b) Wireguard (wg-quick) is not available. FAIL.')
        if cfg.exists():
            print(f'2)  Config file {cfg.filename} already exists. Ok.')
        else:
            print(f'2)  Config file {cfg.filename} does not yet exist. Let\'s create one...')
            print(f'    Press enter to select defaults.')
            wg_configfile = input(f'2a) Please specify the WireGuard config file to be used [/etc/wireguard/wg_rw.conf]: ')
            user = input(f'2b) Please specify the system user for the web frontend [wgfrontend]: ')
            ok = False
            while not ok:
                socket_host = input(f'2c) Please specify the listening interface for the web server [0.0.0.0]: ')
                if check_validcharacters(socket_host, string.hexdigits + '.:'):
                    ok = True
                else:
                    print('    Invalid characters entered. Please enter anew.')
            ok = False
            while not ok:
                socket_port = input(f'2d) Please specify the listening port for the web server [8080]: ')
                if (not socket_port.strip()) or socket_port.isdigit():
                    ok = True
                else:
                    print('    You need to provide a port number. Please enter anew.')            
            ok = False
            while not ok:
                username = input(f'2e) Please specify the username for your web frontend user [admin]: ')
                if check_validcharacters(username, string.ascii_letters + '_'):
                    ok = True
                else:
                    print('    Username must only contain letters and underscores. Please enter anew.')
            ok = False
            while not ok:
                password = input(f'2f) Please specify the password for your web frontend user: ')
                if len(password) >= 8:
                    ok = True
                else:
                    print('    Password must have at least eight characters. Please enter anew.')            
            touch_file(cfg.filename, perm=0o640) # create without world read permissions
            cfg.write_config(wg_configfile=wg_configfile, socket_host=socket_host, socket_port=socket_port, user=user, users={username: password})
            print('    Config file written. Ok.')
        print(f'3)  Ensuring that system user "{cfg.user}" exists.')
        ensure_user(cfg.user)
        print(f'4)  Ensuring ownership of config file {cfg.filename}.')
        chown(cfg.user, cfg.filename)
        if os.path.exists(cfg.libdir):
            print(f'5)  Directory {cfg.libdir} already exists. Ok.')
        else:
            print(f'5)  Directory {cfg.libdir} does not yet exist. Let\'s create it...')
            os.makedirs(cfg.libdir, mode=0o750, exist_ok=True)
            print('    Directory created. Ok.')
        print(f'6)  Ensuring ownership of directory {cfg.libdir}.')
        chown(cfg.user, cfg.libdir)
        if os.path.exists(cfg.wg_configfile):
            print(f'7)  WireGuard config file {cfg.wg_configfile} already exists. Ok.')
        else:
            print(f'7)  WireGuard config file {cfg.wg_configfile} does not yet exist. Let\'s create one...')
            print('    For documentation on possible setups, please refer to')
            print('    https://github.com/towalink/wgfrontend/tree/main/doc/network-integration')
            print('    Automated configuration is only supported for the ProxyARP setup.')
            print('    For this, choose an unused subrange of your local network for WireGuard.')
            wg_listenport = input(f'7a) Please specify the listen port of the WireGuard interface [51820]: ')
            if not wg_listenport.strip():
                wg_listenport = 51820
            ok = False
            while not ok:
                endpoint = input('7b) Please specify the endpoint hostname (and optionally port) to reach your WireGuard server: ')
                if len(endpoint) > 0:
                    ok = True
                else:
                    print('    You need to enter an endpoint hostname.')
            ok = False
            while not ok:                
                wg_address = input('7c) Please specify the IP address of the WireGuard interface incl. prefix length [192.168.0.1/24]: ')
                if not wg_address.strip():
                    wg_address = '192.168.0.1/24'
                try:
                    wg_address_obj = ipaddress.ip_interface(wg_address)
                    ok = True
                except e:
                    print('  Exception: {text}'.format(text=str(e)))
            wg_networks = input('7d) Please specify the network ranges that the clients shall route to the WireGuard server [192.168.0.0/16]: ')
            if not wg_networks.strip():
                wg_networks = '192.168.0.0/16'
            # Check for ProxyARP setup
            proxy_arp_interface = None
            eth_address = get_primary_interface_addr4()
            if (eth_address is not None) and (len(eth_address) > 0):
                eth_address_obj = ipaddress.ip_interface(eth_address)
                if wg_address_obj.network.subnet_of(eth_address_obj.network):
                    interface_name = get_primary_interface()
                    print('    Setup for ProxyARP detected.')
                    if input_yes_no(f'7e) Do you want to configure ProxyARP on interface {interface_name} when bringing up the WireGuard interface? [Yes]: '):
                        proxy_arp_interface = interface_name
                else:
                    print('7e) Please configure your network setup based on the documentation referenced above.')
            # Write WireGuard config file
            wc = wgconfig.WGConfig(cfg.wg_configfile)
            wc.initialize_file('# This file has been created and is managed by wgfrontend. Only change manually if you know what you\'re doing.')
            if not ':' in endpoint:
                endpoint += ':51820'
            wc.add_attr(None, 'ListenPort', wg_listenport, '# Endpoint = ' + endpoint, append_as_line=True)
            wc.add_attr(None, 'PrivateKey', wgexec.generate_privatekey())
            wc.add_attr(None, 'Address', wg_address, '# Networks = ' + wg_networks, append_as_line=True)
            if proxy_arp_interface is not None:
                wc.add_attr(None, 'PostUp', f'sysctl -w net.ipv4.conf.{proxy_arp_interface}.proxy_arp=1', append_as_line=True)
            wc.write_file()
            print('    Config file written. Ok.')
            eh = exechelper.ExecHelper()
            if input_yes_no(f'7f) Would you like to activate the WireGuard interface "{cfg.wg_interface}" now? [Yes]: '):
                eh.run_wgquick('up', cfg.wg_interface)
            if input_yes_no(f'7g) Would you like to activate the WireGuard interface "{cfg.wg_interface}" on boot? [Yes]: '):
                if eh.os_id == 'alpine':
                    setupenv_alpine.start_wginterface_onboot()
                else:
                    eh.enable_service(f'wg-quick@{cfg.wg_interface}')
            if input_yes_no(f'7h) Would you like to start wgfrontend on boot? [Yes]: '):
                if eh.os_id == 'alpine':
                    setupenv_alpine.start_wgfrontend_onboot()
                else:
                    print('    Sorry, this can\'t be configured by this assistant on your platform yet.')
        print(f'8a) Ensuring list permission of WireGuard config directory {os.path.dirname(cfg.wg_configfile)}.')
        os.chmod(os.path.dirname(cfg.wg_configfile), 0o711)
        print(f'8b) Ensuring ownership of WireGuard config file {cfg.wg_configfile}.')
        chown(cfg.user, cfg.wg_configfile)
        print(f'8c) Ensuring ownership of server certificate file {cfg.sslcertfile} in case it exists.')
        if os.path.exists(cfg.sslcertfile):
            chown(cfg.user, cfg.sslcertfile)
        print(f'8d) Ensuring ownership of server private key file {cfg.sslkeyfile} in case it exists.')
        if os.path.exists(cfg.sslkeyfile):
            chown(cfg.user, cfg.sslkeyfile)    
        print(f'Attempting to start web frontend...')
    return cfg


if __name__ == '__main__':
    setup_environment()
