#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'


from peewee import SqliteDatabase

import yaml
import logging
import os

_HERE = os.path.abspath(os.path.dirname(__file__))
_DEFAULT_CONFIG = os.path.join(_HERE, 'config.yml')

class Resource(object):
    def __init__(self, name):
        self.name = name


class ConfigException(Exception):
    pass


class ConfigResource(object):
    _required = []

    def __init__(self, options):
        self.logger = logging.getLogger('tormenta.core.config')
        self.validate(options)

    def validate(self, options):
        entries = options.keys()

        for required in self._required:
            (name, klass) = required
            if not name in entries:
                raise ConfigException('Not found required %s' 
                                ' entry in node declaration' % name)
            setattr(self, name, klass(options[name]))


class KeyHandler:
    def __init__(self, path):
        if not os.path.exists(path):
            raise ConfigException('Not found required key %s' % path)
        self.path = path

class TrackerHandler:
    def __init__(self, options):
        self.options = options

class DataBaseHandler:
    def __init__(self, options):
        if not 'uri' in options:
            raise ConfigException('Please specify a uri path for your database')
        try:
            self.conn = SqliteDatabase(options['uri'], threadlocals=True)
        except Exception as ex:
            raise ConfigException('Invalid provided database %s' % 
                                  options['uri'])

class RestHandler(ConfigResource):

    _required = [ ('port', int), 
                 ('notifications', bool),
                 ('token', bool) ]

    def __init__(self, options):
        ConfigResource.__init__(self, options)


class NodeHandler(ConfigResource):
    _required = [ ('tracker', TrackerHandler),
                  ('database', DataBaseHandler),
                  ('key', KeyHandler),
                  ('rest', RestHandler) ]

    def __init__(self, options):
        ConfigResource.__init__(self, options)


class Config(object):
    """
    Main configuration handler
    """
    DEFAULT_MEMORY_SIZE = 512.00
    DEFAULT_CPU_CORES = [ 0 ]
    DEFAULT_SWAP_SIZE = 512.00
    DEFAULT_DISK_SIZE =  1024.00
    DEFAULT_CPU_SHARES = 2048.00

    ( DEFAULT_NETWORK_IN, 
      DEFAULT_NETWORK_OUT ) = ( 1024.00, 1024.00 )

    _required = [ 'resources', 'node' ]

    def __init__(self, path=None):

        if not path:
            path = _DEFAULT_CONFIG
            
        with open(path) as configuration:
            self._config = yaml.load(configuration.read())

        for required in self._required:
            if not required in self._config:
                raise ConfigException('Invalid configuration: '
                                      '%s section not found' % required)

        self.load_resources(self._config['resources'].items())
        self.load_node(self._config['node'])

    def iterate_options(self, obj, options, skip=None):
        for option, value in options.items():
            if option not in skip:
                validator = '%s_attr_validator' % option
                if hasattr(self, validator):
                    values = getattr(self, validator)(value)
                setattr(obj, option, value)
        return obj

    def load_node(self, options):
        self.node = NodeHandler(options)
            
    def load_resources(self, resources):
        try:
            for resource in resources:
                (name, options) = resource
                getattr(self, 's_%s' % name)(options)
        except Exception as ex:
            self.logger.warn(ex.message)
            raise ConfigException('Cannot load resources' 
                                  'section from configuration')

    @property
    def memory(self):
        try:
            return self._memory
        except:
            self._memory = None
        return self._memory

    def s_memory(self, options):
        self._memory = Resource('memory')

        if not 'limit' in options:
            self._memory.limit = self.DEFAULT_MEMORY_SIZE
        else:
            self._memory.limit = float(options['limit'])

        self._memory = self.iterate_options(self._memory, options,
                                                    skip=('limit'))
        return self._memory

    @property
    def cpu(self):
        try:
            return self._cpu
        except:
            self._cpu = None
        return self._cpu

    def s_cpu(self, options):
        self._cpu = Resource('cpu')

        if not 'shares' in options:
            self._cpu.limit = self.DEFAULT_CPU_SHARES
        else:
            self._cpu.limit = float(options['shares'])

        if not 'cores' in options:
            self._cpu.cores = self.DEFAULT_CPU_CORES
        else:
            self._cpu.cores = options['cores']

        self._cpu = self.iterate_options(self._cpu, options, skip=('limit'))
        return self._cpu

    @property
    def swap(self):
        try:
            return self._swap
        except:
            self._swap = None
        return self._swap

    def s_swap(self, options):
        self._swap = Resource('swap')

        if not 'limit' in options:
            self._swap.limit = self.DEFAULT_SWAP_SIZE
        else:
            self._swap.limit = float(options['limit'])

        self._swap = self.iterate_options(self._swap, options, skip=('limit'))
        return self._swap

    @property
    def network(self):
        try:
            return self._network
        except:
            self._network = None
        return self._network

    def s_network(self, options):
        self._network = Resource('network')

        if not 'limit' in options:
            (self._network.limit_in ,
             self._network.limit_out) = (self.DEFAULT_NETWORK_IN,
                                         self.DEFAULT_NETWORK_OUT)
        else:
            if ( 'in' in options['limit'] and 'out' in options['limit'] ):
                (self._network.limit_in,
                 self._network.limit_out) = (float(options['limit']['in']),
                                             float(options['limit']['out']))
        
        self._network = self.iterate_options(self._network, options,
                                                    skip=('limit'))
        return self._network

    @property
    def disk(self):
        try:
            return self._disk
        except:
            self._disk = None
        return self._disk

    def s_disk(self, options):
        self._disk = Resource('disk')

        if not 'limit' in options:
            self._disk.limit = self.DEFAULT_SWAP_SIZE
        else:
            self._disk.limit = float(options['limit'])
        
        self._disk = self.iterate_options(self._disk, options,
                                                skip=('limit'))
        return self._disk


settings = Config()
