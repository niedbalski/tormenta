#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from tormenta.core.config import settings
from tormenta.core.model import Tracker

def initialize():
    return Tracker.get_or_create(settings.node.key.path)
