# wgfrontend

A simple web frontend for configuring peers within a WireGuard configuration file to thus administer road warrior clients.

There are already a lot of user interfaces for administering WireGuard configuration files available. However, many of them have a bunch of dependencies, require root privileges to operate, or are a hassle to set up. "wgfrontend" provides a user interface that can be easily installed by just installing a package from Python's package repository PyPi (i.e. using pip).

IMPORTANT NOTE: This tool is still in development stage. Bug reports are appreciated.

This little tool is independent of the Towalink site connectivity solution (see https://towalink.readthedocs.io).

---

## Features

- Web frontend for adding, modifying, and deleting WireGuard peers
- Config files for WireGuard peers can be downloaded
- Config files for WireGuard peers are shown as QR Code
- Assistant for initial set-up
- Web frontend has responsive design
- Web frontend does not run with root privileges
- Simple installation

---

## Installation

Install using PyPi:

```shell
pip3 install wgfrontend
```

---

## Quickstart

After installing "wgfrontend" as shown above, just execute the tool with root permissions to get started:

```shell
wgfrontend
```

An interactive set-up assistant queries for the needed configuration data and sets up the environment.
Once everything is configured, "wgfrontend" drops root privileges and runs a small web server on port 8080 to serve the web frontend.

Note that the changes done by wgfrontend in the WireGuard configuration file do not take affect automatically. The new configuration needs to be taken over to the WireGuard interface manually. Automating this is on the roadmap.

---

## Details


### The wgfrontend configuration file

The interactive set-up assistant creates a configuration file with the desired information. It is located at "/etc/wgfrontend/wgfrontend.conf".

Here is an example:

```
### Config file of the Towalink WireGuard Frontend ###
[general]
# The WireGuard config file to read and write
wg_configfile = /etc/wireguard/wg_rw.conf

# The system user to be used for the frontend
user = wgfrontend

[users]
admin = dc524e423d9762830649d4d9e18f4b47a56c92f96646104dd06c71b26b54f732e8318d5b60a6b2b01b4f269407771496e879c9bf65ca9ef4f55a243ff358fc8dfea0bd9d30d766320857093eb95022822f71b098215f26f6d2644033d956bfdd
```

### Add an additional frontend user

Create a password hash using the following command:

```shell
wgfrontend-password
```

Using this, you can add another user to the [users] section in the wgfrontend configuration file.

### A note on security

Don't expose the web frontend to the Internet without another layer of protection.

The wgfrontend web server does not run with root permissions. That's a start and better than many other WireGuard frontends. But the web server user has the permission to write to a WireGuard configuration file. This file may reference scripts that are run with root permissions when wg-quick is run. In case of a vulnerability in wgfrontend, this can be abused for privilege escalation. Thus add an additional safeguard layer of protection.

---

## Reporting bugs

In case you encounter any bugs, please report the expected behavior and the actual behavior so that the issue can be reproduced and fixed.

---
## Developers

### Clone repository

Clone this repo to your local machine using `https://github.com/towalink/wgfrontend.git`

Install the module temporarily to make it available in your Python installation:
```shell
pip3 install -e <path to root of "src" directory>
```

---

## License

[![License](http://img.shields.io/:license-agpl3-blue.svg?style=flat-square)](https://opensource.org/licenses/AGPL-3.0)

- **[AGPL3 license](https://opensource.org/licenses/AGPL-3.0)**
- Copyright 2020 © <a href="https://github.com/towalink/wgfrontend" target="_blank">Dirk Henrici</a>.
- [WireGuard](https://www.wireguard.com/) is a registered trademark of Jason A. Donenfeld.
