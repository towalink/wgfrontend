#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipaddress
import logging
import os
import qrcode
import textwrap
import wgconfig
import wgconfig.wgexec as wgexec


logger = logging.getLogger(__name__)


class WGCfg():
    """Class for reading/writing the WireGuard configuration file"""

    def __init__(self, filename, libdir, on_change_func=None):
        """Initialize instance for the given config file"""
        self.filename = filename
        self.libdir = libdir
        self.on_change_func = on_change_func
        self.wc = wgconfig.WGConfig(self.filename)
        self.wc.read_file()

    def get_interface(self):
        """Get WireGuard interface data"""
        return self.wc.interface

    def transform_to_clientdata(self, peer, peerdata):
        """Transform data of a single peer from server into a dictionary of client config data"""
        result = dict()
        description = peerdata['_rawdata'][0]
        if description[0] == '#':
            description = description[2:]
        else:
            description = 'Peer: ' + peer
        result['Description'] = description
        for item in peerdata['_rawdata']:
            if item.startswith('# PrivateKey = '):
                result['PrivateKey'] = item[15:]
        result['PublicKey'] = peer
        result['PresharedKey'] = peerdata['PresharedKey']
        address = peerdata['AllowedIPs'].partition(',')[0] # get first allowed ip range
        address = address.partition('/')[0] + '/' + self.get_interface()['Address'].partition('/')[2] # take prefix length from interface address
        result['Address'] = address
        result['Id'] = address.partition('/')[0].replace('.', '-')
        result['QRCode'] = os.path.join(self.libdir, result['Id'] + '.png')
        return result

    def get_peer(self, peer):
        """Get data of the given WireGuard peer"""
        if peer is None:
            return None
        return self.transform_to_clientdata(peer, self.wc.peers[peer])

    def get_peers(self):
        """Get data of all WireGuard peers"""
        return { peer: self.get_peer(peer) for peer in self.wc.peers.keys() }

    def get_peer_byid(self, id):
        """Get data WireGuard peer with the given id"""
        try:
            peer = next(peer for peer, peerdata in self.get_peers().items() if peerdata['Id'] == id)
        except StopIteration:
            peer = None
        return peer, self.get_peer(peer)

    def get_peerconfig(self, peer):
        """Get config for the given WireGuard peer"""
        if peer is None:
            return None, None
        peerdata = self.get_peer(peer)
        for item in self.get_interface()['_rawdata']:
            if item.startswith('# Endpoint = '):
                endpoint = item[13:]
            if item.startswith('# Networks = '):
                allowed_ips = item[13:]
        public_key = wgexec.get_publickey(peerdata['PrivateKey'])
        public_key_server = wgexec.get_publickey(self.get_interface()['PrivateKey'])
        config = textwrap.dedent(f'''\
            # {peerdata['Description']}
            [Interface]
            ListenPort = 51820
            PrivateKey = {peerdata['PrivateKey']}
            # PublicKey = {public_key}
            Address = {peerdata['Address']}
            
            [Peer]
            Endpoint = {endpoint}
            PublicKey = {public_key_server}
            PresharedKey = {peerdata['PresharedKey']}
            AllowedIPs = {allowed_ips}
            PersistentKeepalive = 25
        ''')
        return config, peerdata

    def create_peer(self, description, ip=None):
        """Create peer with the given description"""
        if ip is None:
            ip = self.find_free_ip()
        private_key = wgexec.generate_privatekey()
        peer = wgexec.get_publickey(private_key)
        self.wc.add_peer(peer, '# ' + description)
        comment = '# PrivateKey = ' + private_key
        self.wc.add_attr(peer, 'PresharedKey', wgexec.generate_presharedkey(), comment, append_as_line=True)
        self.wc.add_attr(peer, 'AllowedIPs', ip + '/32')
        self.wc.add_attr(peer, 'PersistentKeepalive', 25)
        self.wc.write_file()
        self.write_qrcode(peer)
        self.config_change_done()
        return peer
        
    def update_peer(self, peer, description):
        """Update the given peer"""
        peerdata = self.wc.peers[peer]
        first_line = peerdata['_index_firstline']
        if self.wc.lines[first_line][0] != '#':
            raise ValueError(f'Comment expected in first line of config for peer [{peerdata}]')
        self.wc.lines[first_line] = '# ' + description
        self.wc.invalidate_data()
        self.wc.write_file()
        self.write_qrcode(peer)
        self.config_change_done()
        return self.get_peer(peer)
        
    def delete_peer(self, peer):
        """Delete the given peer"""
        self.wc.del_peer(peer)
        self.wc.write_file()
        self.config_change_done()
       
    def find_free_ip(self):
        """Find the first free address in the given network"""
        interface_address = ipaddress.ip_interface(self.get_interface()['Address'])
        network = interface_address.network
        interface_address = interface_address.ip
        addresses = [ ipaddress.ip_interface(peerdata['Address']).ip for peer, peerdata in self.get_peers().items() ]
        ip = None
        for addr in network.hosts():
            if addr == interface_address:
                continue
            if addr in addresses:
                continue
            ip = addr
            break
        if ip is None:
            raise ValueError('No free IP address available any more')
        return str(ip)

    def write_qrcode(self, peer):
        """Generate a QRCode for the given peers configuration file and store in lib directory"""
        config, peerdata = self.get_peerconfig(peer)
        #img = qrcode.make(config)
        qr = qrcode.QRCode(version=15, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=2, border=5)
        qr.add_data(config)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img.save(peerdata['QRCode'])

    def config_change_done(self):
        """React on config changes"""
        if self.on_change_func is not None:
            self.on_change_func()


if __name__ == '__main__':
    import pprint
    wg = WGCfg('/etc/wireguard/wg_rw.conf', '/var/lib/wgfrontend')
    peer = wg.create_peer('This is a first test peer')
    peer2 = wg.create_peer('This is a second test peer')
    wg.update_peer(peer2, 'CHANGED')
    print(wg.get_peerconfig(peer2)[0])
    wg.delete_peer(peer)
    wg.delete_peer(peer2)
