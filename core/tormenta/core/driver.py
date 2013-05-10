#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

import logging
import importlib

logger = logging.getLogger('tormenta.core.driver')

INSTANCE_STATES = (
    'NOSTATE',
    'REMOVED',
    'RUNNING',
    'BLOCKED',
    'PAUSED',
    'SHUTDOWN',
    'SHUTOFF',
    'CRASHED',
    'SUSPENDED'
)
