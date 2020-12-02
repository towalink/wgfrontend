#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import cherrypy
import jinja2
import os
import random
import string

from . import pwdtools
from . import wgcfg


class WebApp():

    def __init__(self, cfg):
        """Instance initialization"""
        self.cfg = cfg
        self.jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')))
        self.wg = wgcfg.WGCfg(self.cfg.wg_configfile, self.cfg.libdir)

    @cherrypy.expose
    def index(self, action=None, id=None, description=None):
        if (action == 'delete') and id:
            peer, peerdata = self.wg.get_peer_byid(id)
            self.wg.delete_peer(peer)
        peers = self.wg.get_peers()
        tmpl = self.jinja_env.get_template('index.html')
        return tmpl.render(sessiondata=cherrypy.session, peers=peers)

    @cherrypy.expose
    def config(self, action=None, id=None, description=None):
        peerdata = None
        if (action == 'save') and id:
            peer, peerdata = self.wg.get_peer_byid(id)
            peerdata = self.wg.update_peer(peer, description)
        if (action == 'save') and not id:
            peer = self.wg.create_peer(description)
            peerdata = self.wg.get_peer(peer)
        if not peerdata:
            peer, peerdata = self.wg.get_peer_byid(id)
        tmpl = self.jinja_env.get_template('config.html')
        return tmpl.render(sessiondata=cherrypy.session, peerdata=peerdata)

    @cherrypy.expose
    def edit(self, action='edit', id=None, description=None):
        if id: # existing client
            peer, peerdata = self.wg.get_peer_byid(id)
            if description:
                peerdata = self.wg.update_peer(peer, description)
        else:
            if not description:
                description = 'My new client'
            if action == 'new': # default values for new client
                peerdata = { 'Description': description, 'Id': '' }
            else: # save changes
                raise ValueError()
        tmpl = self.jinja_env.get_template('edit.html')
        return tmpl.render(sessiondata=cherrypy.session, peerdata=peerdata)

    @cherrypy.expose
    def download(self, id):
        """Provide the WireGuard config for the client with the given identifier for download"""
        peer, peerdata = self.wg.get_peer_byid(id)
        config, peerdata = self.wg.get_peerconfig(peer)
        cherrypy.response.headers['Content-Disposition'] = f'attachment; filename=wg_{id}.conf'
        cherrypy.response.headers['Content-Type'] = 'text/plain' # 'application/x-download' 'application/octet-stream'
        return config.encode('utf-8')

    def check_username_and_password(self, username, password):
        """Check whether provided username and password are valid when authenticating"""
        if (username in self.cfg.users) and (pwdtools.verify_password(self.cfg.users[username], password)):
            return
        return 'invalid username/password'

    def login_screen(self, from_page='..', username='', error_msg='', **kwargs):
        """Shows a login form"""
        tmpl = self.jinja_env.get_template('login.html')
        return tmpl.render(from_page=from_page, username=username, error_msg=error_msg).encode('utf-8')

    @cherrypy.expose
    def logout(self):
        username = cherrypy.session['username']
        cherrypy.session.clear()
        cherrypy.response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        cherrypy.response.headers['Pragma'] = 'no-cache'
        cherrypy.response.headers['Expires'] = '0'
        raise cherrypy.HTTPRedirect('/', 302)        
        return '"{0}" has been logged out'.format(username)


def run_webapp(cfg):
    """Runs the CherryPy web application with the provided configuration data"""
    script_path = os.path.dirname(os.path.abspath(__file__))
    app = WebApp(cfg)
    app_conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.join(script_path, 'webroot'),
            'tools.session_auth.on': True,
            'tools.session_auth.login_screen': app.login_screen,
            'tools.session_auth.check_username_and_password': app.check_username_and_password,
            },
        '/configs': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': None,
            'tools.staticdir.dir': cfg.libdir
        },
        '/static': {
            'tools.session_auth.on': False,
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        },
        '/favicon.ico':
        {
            'tools.session_auth.on': False,
            'tools.staticfile.on': True,
            'tools.staticfile.filename': os.path.join(script_path, 'webroot', 'static', 'favicon.ico')
        }
    }
    if os.path.exists(cfg.sslcertfile) and os.path.exists(cfg.sslkeyfile):
        cherrypy.server.ssl_module = 'builtin'
        cherrypy.server.ssl_certificate = cfg.sslcertfile
        cherrypy.server.ssl_private_key = cfg.sslkeyfile
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 8080,
                           })
    cherrypy.quickstart(app, '/', app_conf)


if __name__ == '__main__':
    pass
