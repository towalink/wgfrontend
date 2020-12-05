# -*- coding: utf-8 -*-

import configparser
import logging
import os
import textwrap

from . import pwdtools


logger = logging.getLogger(__name__)

config_filename = '/etc/wgfrontend/wgfrontend.conf'


class Configuration():
    """Class for reading/writing the configuration file"""
    _config = None

    def exists(self):
        """Checks whether the config file exists"""
        return os.path.isfile(self.filename)
  
    def read_config(self):
        """Reads the config file"""
        try:
            logger.debug('Attempting to read config file [{0}]'.format(self.filename))
            cfg = configparser.ConfigParser()
            cfg.read(self.filename)
            self._config = dict(cfg['general'])
            self._users = dict(cfg['users'])
        except Exception as e:
            logger.warning('Config file [{0}] could not be read [{1}], using defaults'.format(self.filename, str(e)))
            self._config = dict()
    
    def write_config(self, wg_configfile='', user='', users={}):
        """Writes a new config file with the given attributes"""
        # Set default values
        if not wg_configfile.strip():
            wg_configfile = '/etc/wireguard/wg_rw.conf'
        if not user.strip():
            user = 'wgfrontend'
        users = { username if username.strip() else 'admin': password for username, password in users.items() }
        username = next(iter(users.keys()))
        password = pwdtools.hash_password(users[username])
        # Config file content
        config_content = textwrap.dedent(f'''\
        ### Config file of the Towalink WireGuard Frontend ###
        [general]
        # The WireGuard config file to read and write
        wg_configfile = {wg_configfile}

        # The command to be executed when the WireGuard config has changed
        # on_change_command =
        # Example: on_change_command = "sudo /etc/init.d/wgfrontend_interface restart"

        # The interface to bind to for the web server
        # socket_host = 0.0.0.0

        # The port to bind to for the web server
        # socket_port = 8080
        
        # The system user to be used for the frontend
        user = {user}
        
        [users]
        {username} = {password}
        ''')
        # Write to file system
        try:
            with open(self.filename, 'w') as config_file:
                config_file.write(config_content)
        except OSError as e:
            logger.error('Could not write config file [{0}], [{1}]'.format(self.filename, str(e)))

    @property
    def filename(self):
        """Return the name of the config file (incl. path)"""
        return config_filename

    @property
    def config(self):
        """Return the config dictionary"""
        if self._config is None:
            self.read_config()
        return self._config

    @property
    def users(self):
        """Return the users dictionary"""
        if self._users is None:
            self.read_config()
        return self._users

    @property
    def wg_configfile(self):
        """The filename incl. path of the config file for the WireGuard interface"""
        return self.config.get('wg_configfile', '/etc/wireguard/wg_rw.conf')

    @property
    def sslcertfile(self):
        """The filename incl. path for the server certificate"""
        return os.path.join(os.path.dirname(self.filename), 'server.pem')

    @property
    def sslkeyfile(self):
        """The filename incl. path for the server private key"""
        return os.path.join(os.path.dirname(self.filename), 'key.pem')

    @property
    def libdir(self):
        """The directory for the generated config files"""
        return '/var/lib/wgfrontend'

    @property
    def on_change_command(self):
        """The command to be executed on config changes"""
        return self.config.get('on_change_command')

    @property
    def socket_host(self):
        """The interface to bind to"""
        return self.config.get('socket_host', '0.0.0.0')

    @property
    def socket_port(self):
        """The port to bind to"""
        return int(self.config.get('socket_port', 8080))

    @property
    def user(self):
        """The configured name for the wgfrontend system user"""
        return self.config.get('user', 'wgfrontend')
