# -*- coding: utf-8 -*-

import os
import textwrap


def enable_startscript(service):
    """Start the given service on boot"""
    ret = os.system('rc-update add {service}'.format(service=service))
    return ret

def get_startupscript_wgfrontend():
    """Get a startup script for wgfrontend"""
    template = r'''
        #!/sbin/openrc-run
        
        depend() {
                need net
        }
        
        name=$RC_SVCNAME
        command="wgfrontend"
        command_args=""
        pidfile="/run/$RC_SVCNAME.pid"
        command_background="yes"
        stopsig="SIGTERM"
        start_stop_daemon_args="--stdout /var/log/wgfrontend.log --stderr /var/log/wgfrontend.err"
        #Let wgfrontend drop privileges so that we keep permission to write to the log files
        #command_user="wgfrontend:wgfrontend"
        '''
    template = textwrap.dedent(template).lstrip()
    return template

def get_startupscript_wginterface(interface_name='wg_rw'):
    """Get a startup script for the WireGuard interface used by wgfrontend"""
    template = r'''
        #!/sbin/openrc-run
        
        depend() {{
                need net
        }}
        
        start() {{
                wg-quick up {interface_name}
        }}
        
        stop() {{
                wg-quick down {interface_name}
        }}
        
        name=$RC_SVCNAME
        '''
    template = textwrap.dedent(template).lstrip()
    return template.format(interface_name=interface_name)

def write_startupscript_wgfrontend():
    """Write a startup script for wgfrontend to /etc/init.d"""
    filename = '/etc/init.d/wgfrontend'
    with open(filename, 'w') as f:
        f.write(get_startupscript_wgfrontend())
    os.chmod(filename, 0o700)

def write_startupscript_wginterface():
    """Write a startup script for the WireGuard interface of wgfrontend to /etc/init.d"""
    filename = '/etc/init.d/wgfrontend_interface'
    with open(filename, 'w') as f:
        f.write(get_startupscript_wginterface())
    os.chmod(filename, 0o700)

def start_wgfrontend_onboot():
    """Enable the start script of wgfrontend"""
    write_startupscript_wgfrontend()
    enable_startscript('wgfrontend')
    
def start_wginterface_onboot():
    """Enable the start script for the WireGuard interface of wgfrontend"""
    write_startupscript_wginterface()
    enable_startscript('wgfrontend_interface') 
