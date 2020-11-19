#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import cherrypy
import jinja2
import os
import random
import string

import pwdtools
import wgcfg


def login_screen(from_page='..', username='', error_msg='', **kwargs):
    """Based on https://docs.cherrypy.org/en/latest/_modules/cherrypy/lib/cptools.html"""
    content="""
    <form method="post" action="do_login">
      <div align=center>
        <span class=errormsg>%s</span>
        <table>
          <tr>
            <td>
              Login:
            </td>
            <td>
              <input type="text" name="username" value="%s" size="40" />
            </td>
          <tr>
            <td>
              Password:
            </td>
            <td>
              <input type="password" name="password" size="40" />
              <input type="hidden" name="from_page" value="%s" />
            </td>
          </tr>
          <tr>
            <td colspan=2 align=right>
              <input type="submit" value="Login" />
            </td>
          </tr>
        </table>
      </div>
    </form>
    """ % (error_msg, username, from_page)
    title='Login'
    return ('<html><body>' + content + '</body></html>').encode('utf-8')
#    return cherrypy.tools.encode('<html><body>' + content + '</body></html>')


class WebApp():

    def __init__(self, cfg):
        """Instance initialization"""
        self.cfg = cfg
        self.jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        self.wg = wgcfg.WGCfg(self.cfg.wg_configfile, self.cfg.libdir)

    @cherrypy.expose
    def index(self, action=None, id=None, description=None):
        if (action == 'delete') and id:
            peer, peerdata = self.wg.get_peer_byid(id)
            self.wg.delete_peer(peer)
        peers = self.wg.get_peers()
        tmpl = self.jinja_env.get_template('index.html')
        return tmpl.render(peers=peers)

    @cherrypy.expose
    def config(self, id):
        peer, peerdata = self.wg.get_peer_byid(id)
        tmpl = self.jinja_env.get_template('config.html')
        return tmpl.render(peerdata=peerdata)

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
                peer = self.wg.create_peer(description)
                peerdata = self.wg.get_peer(peer)
        tmpl = self.jinja_env.get_template('edit.html')
        return tmpl.render(peerdata=peerdata)

    @cherrypy.expose
    def download(self, id):
        peer, peerdata = self.wg.get_peer_byid(id)
        config, peerdata = self.wg.get_peerconfig(peer)
        cherrypy.response.headers['Content-Disposition'] = f'attachment; filename=wg_{id}.conf'
        cherrypy.response.headers['Content-Type'] = 'text/plain' # 'application/x-download' 'application/octet-stream'
        return config.encode('utf-8')

    @cherrypy.expose
    def logout(self):
          username = cherrypy.session['username']
          cherrypy.session.clear()
          return '"{0}" has been logged out'.format(username)



def run_webapp(cfg):

    def check_username_and_password(username, password):
        """Check whether provided username and password are valid when authenticating"""
        if (username in cfg.users) and (pwdtools.verify_password(cfg.users[username], password)):
            return
        return 'invalid username/password'

    script_path = os.path.dirname(os.path.abspath(__file__))
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.staticdir.root': os.path.join(script_path, 'webroot'),
#            'tools.session_auth.on': True,
            'tools.session_auth.login_screen': login_screen,
            'tools.session_auth.check_username_and_password': check_username_and_password,
            },
        '/configs': {
            'tools.staticdir.on': True,
            'tools.staticdir.root': None,
            'tools.staticdir.dir': cfg.libdir
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'
        },
        '/favicon.ico':
        {
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
    cherrypy.quickstart(WebApp(cfg), '/', conf)


if __name__ == '__main__':
    pass
