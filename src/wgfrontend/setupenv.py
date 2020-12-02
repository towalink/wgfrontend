#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import getpass
import grp
import os
import pwd
import string
import wgconfig
import wgconfig.wgexec as wgexec

from . import config


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

def drop_privileges(uid_name='nobody', gid_name='nogroup'):
    """"""
    if not is_root():
        raise ValueError('No privileges present to drop')
    uid = pwd.getpwnam(uid_name).pw_uid
    gid = grp.getgrnam(gid_name).gr_gid
#    os.setgroups([]) # remove group privileges
    os.setgid(gid)
    os.setuid(uid)

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
                username = input(f'2c) Please specify the username for your web frontend user [admin]: ')
                if check_validcharacters(username, string.ascii_letters + '_'):
                    ok = True
                else:
                    print('    Username must only contain letters and underscores. Please enter anew.')
            ok = False
            while not ok:
                password = input(f'2d) Please specify the password for your web frontend user: ')
                if len(password) >= 8:
                    ok = True
                else:
                    print('    Password must have at least eight characters. Please enter anew.')            
            touch_file(cfg.filename, perm=0o640) # create without world read permissions
            cfg.write_config(wg_configfile=wg_configfile, user=user, users={username: password})
            print('    Config file written. Ok.')
        print(f'3)  Ensuring that system user "{cfg.user}" exists.')
        ensure_user(cfg.user)
        print(f'4)  Ensuring ownership of config file {cfg.filename}.')
        chown(cfg.user, cfg.filename)
        if os.path.exists(cfg.libdir):
            print(f'5)  Directory {cfg.libdir} already exists. Ok.')
        else:
            print(f'5)  Directory {cfg.libdir} does not yet exist. Let\'s create it...')
            os.makedirs(cfg.libdir, mode=0o640, exist_ok=True)
            print('    Directory created. Ok.')
        print(f'6)  Ensuring ownership of directory {cfg.libdir}.')
        chown(cfg.user, cfg.libdir)
        if os.path.exists(cfg.wg_configfile):
            print(f'7)  WireGuard config file {cfg.wg_configfile} already exists. Ok.')
        else:
            print(f'7)  WireGuard config file {cfg.wg_configfile} does not yet exist. Let\'s create one...')
            wg_listenport = input(f'7a) Please specify the listen port of the WireGuard interface [51820]: ')
            if not wg_listenport.strip():
                wg_listenport = 51820
            ok = False
            while not ok:
                endpoint = input(f'7b) Please specify the endpoint hostname (and optionally port) to reach your WireGuard server: ')
                if len(endpoint) > 0:
                    ok = True
                else:
                    print('    You need to enter an endpoint hostname.')
            wg_address = input(f'7c) Please specify the IP address of the WireGuard interface incl. prefix length [192.168.0.1/24]: ')
            if not wg_address.strip():
                wg_address = '192.168.0.1/24'
            wg_networks = input(f'7d) Please specify the network ranges that the clients shall route to the WireGuard server [192.168.0.0/16]: ')
            if not wg_networks.strip():
                wg_networks = '192.168.0.0/16'
            wc = wgconfig.WGConfig(cfg.wg_configfile)
            wc.initialize_file('# This file has been created and is managed by wgfrontend. Only change manually if you know what you\'re doing.')
            if not ':' in endpoint:
                endpoint += ':51820'
            wc.add_attr(None, 'ListenPort', wg_listenport, '# Endpoint = ' + endpoint, append_as_line=True)
            wc.add_attr(None, 'PrivateKey', wgexec.generate_privatekey())
            wc.add_attr(None, 'Address', wg_address, '# Networks = ' + wg_networks, append_as_line=True)
            wc.write_file()
            print('    Config file written. Ok.')
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
        print(f'9)  Dropping root privileges to user/group "{cfg.user}".')
        drop_privileges(cfg.user, cfg.user)
        print(f'Attempting to start web frontend...')
    return cfg


if __name__ == '__main__':
    setup_environment()
