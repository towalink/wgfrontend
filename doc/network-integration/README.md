# WireGuard VPN Server Integration Options

In the follwing subsections, three different options for integrating a WireGuard VPN server for road warriors into a home network are discussed. All three setups work well with "wgfrontend".

The following setups are described:
- Routed Setup
- Masqueraded Setup
- ProxyARP Setup

You can choose one of these setups based on your needs. The basic setup that is used for the explanation of all the three options is presented.

## Basic Scenario

We assume a home network setup as shown in the figure. The home network is connected to the Internet via a home Internet router. In our example, the home network uses the address range 192.168.178.0/24 and the Internet router itself uses the IPv4 address 192.168.178.1 within the home network. As long as no specific static routes are configured on this router, all data packets except ones destined to the home network are routed towards the Internet (i.e. default route towards the Internet Service Provider).

![basic scenario](https://raw.githubusercontent.com/towalink/wgfrontend/main/doc/network-integration/setup_basic.png "Basic scenario")

The figure shows a "Home Device" that is part of this home network. It has the IP address 192.168.178.123. All data packets except ones destined to the home network are sent towards the Internet router. The home network may contain many devices like this since this is the usual configuration. Whether the IP address to such a home device is assigned statically or dynamically does not matter.

The figure also shows a device titled "Raspberry Pi as WireGuard server". This represents a device that hosts our WireGuard server that serves WireGuard road warrior clients. It is connected to the home network with device "eth0" with address 192.168.178.9. It also has a WireGuard interface "wg_rw" as the WireGuard interface serving our road warrior clients.

In the following, we extend this basic scenario in different ways depending on the setup.

## Routed Setup

In a routed setup, a separate IP range is used for the WireGuard server interface and the WireGuard clients. We use 10.1.1.0/28 in the example. The WireGuard clients need to be told that the local network address range 192.168.178.0/24 can be reached via the WireGuard connection, i.e. a route is added for this network. The WireGuard server can deliver data packets destined to any device in the home network.

![routed setup](https://raw.githubusercontent.com/towalink/wgfrontend/main/doc/network-integration/setup_routed.png "Routed setup")

We also need to take care that the response packets to the WireGuard client pass via the WireGuard VPN. All devices in the home network attempt to reach the WireGuard network range 10.1.1.0/28 via the home Internet router (unless we configure a static route on each device telling it to send the packets to the WireGuard server). Due to the home Internet router's default route towards the ISP, the packets will go to the ISP. To prevents this, a static route needs to be added on the home Internet router. The static route tells that the WireGuard network range 10.1.1.0/28 can be reached via the device with address 192.168.178.9 (WireGuard server). Once a packet uses the suboptimal detour via the home Internet router, the home Internet router will - depending on configuration - send an ICMP redirect message to the sending home device to tell it the optimal route. Depending on configuration of the home Internet router and the home device (it needs to accept the message), this mitigates the suboptimal routing.

This routed setup requires that static routes can be configured on the home Internet router (configurable on many but not all of such routers). The suboptimal routing of the packets from home devices to the WireGuard clients via the home Internet router is not "clean" and - depending on configuration with respect to ICMP redirect messages - reduces throughput. Apart from these drawbacks, the routed setup is nice, clean, and scalable.

## Masqueraded Setup

In a masqueraded setup, a separate IP range is used for the WireGuard server interface and the WireGuard clients. We use 10.1.1.0/28 in the example. The WireGuard clients need to be told that the local network address range 192.168.178.0/24 can be reached via the WireGuard connection, i.e. a route is added for this network. That much is the same as in the routed setup. A masquerading rule (a special form of network address translation) is configured on the WireGuard server that masquerades this network range so that only the IP address of the eth0 interface is visible towards the home network 192.168.178.0/24. This is done using nftables or iptables.

![masqueraded setup](https://raw.githubusercontent.com/towalink/wgfrontend/main/doc/network-integration/setup_masqueraded.png "Masqueraded setup")

Data packets from a WireGuard client destined to a device in the home network are sent to the WireGuard server. The masquerading rule rewrites the source address to the address of the eth0 interface (192.168.178.9) and takes care that response packets are treated in the reverse way. For a device in the home network, the WireGuard network range 10.1.1.0/28 is not visible and packets appear to be sourced from 192.168.178.9. Thus, home devices send response packets to 192.168.178.9 (eth0 of the WireGuard server), and the WireGuard server takes care of the further steps needed.

The good thing about this setup is that no configuration on the home Internet router or the home network devices is needed and that traffic always takes a direct path. But the fact that traffic from all WireGuard clients appears to be coming from 192.168.178.9 hides the WireGuard clients so that they cannot be distinguished in the home network any more (server logs, firewall rules, etc.). Home devices also cannot initiate connections to a WireGuard client since they are not addressable. I therefore do not like this setup.

## ProxyARP Setup

In the ProxyARP setup, a subrange of the home network address range is assigned to be used as the WireGuard network. In the figure, 192.168.178.16/28 is used for the WireGuard network. This is a subrange of the home network 192.168.178.0/24. The WireGuard clients need to be told that the local network address range 192.168.178.0/24 can be reached via the WireGuard connection, i.e. a route is added for this network. 

![ProxyARP setup](https://raw.githubusercontent.com/towalink/wgfrontend/main/doc/network-integration/setup_proxyarp.png "ProxyARP setup")

The WireGuard server will attempt to reach the WireGuard clients using an address out of 192.168.178.16/28 via its WireGuard interface and the other devices in 192.168.178.0/24 via its eth0 interface. That's fine. WireGuard clients send packets destined to the home network via the WireGuard connection to the WireGuard server who knows how to deliver them. That is fine, too. A home device like 192.168.178.123 needs to know that the IP addresses of the WireGuard clients can be reached via the WireGuard servers eth0 interface. When the home devices sends an ARP request like "what is the MAC address for IP 192.168.178.18" nobody answers since there is no Ethernet device with this address in the home network. This behavior is changed once ProxyARP is enabled on the eth0 interface of the WireGuard server. Then the mentioned ARP request is answered with the MAC address of the eth0 interface of the WireGuard server so that home devices send the packets destined to 192.168.178.18 to the WireGuard server. Communication now works fine between all peers.

Like in the masqueraded setup, no configuration on the home Internet router or the home network devices is needed and traffic always takes a direct path. It needs to be ensured that the subrange assigned to the WireGuard network is not used by devices in the home network. Troubleshooting a ProxyARP setup is more difficult than the other setups. The scalabilty of this setup has limitations. Apart from these mentioned drawbacks, the ProxyARP setup is nice.
