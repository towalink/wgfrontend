#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Thx to https://www.vitoshacademy.com/hashing-passwords-in-python/

import hashlib, binascii, os


def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')
 
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512', provided_password.encode('utf-8'), salt.encode('ascii'), 100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def hash_password_interactively():
    """Ask for a password and print it in hashed form"""
    pwd = input('Please enter password to hash: ')
    print('Hashed password:')
    print(hash_password(pwd))


if __name__ == '__main__':
    hash_password_interactively()
