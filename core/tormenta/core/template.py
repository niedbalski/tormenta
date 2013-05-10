#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from jinja2 import Environment, PackageLoader

loader  = Environment(loader=PackageLoader('tormenta.core', 'templates'))

def load(name):
    return loader.get_template(name)
