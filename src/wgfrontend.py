#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import setupenv
import webapp


def main():
    cfg = setupenv.setup_environment()
    webapp.run_webapp(cfg)


if __name__ == '__main__':
    main()
