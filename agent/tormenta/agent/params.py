#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from tormenta.core.driver import INSTANCE_STATES
from tormenta.core.model import PublicKey

from flask.ext.restful import fields, types, reqparse

import re


def parse_args(request_parameter_map, all_valid=True):
    parser = reqparse.RequestParser()
    add_arg = parser.add_argument

    for param, values in request_parameter_map.iteritems():
        add_arg(param, **values)

    args = parser.parse_args()
    return args


def parse_list(value):
    regex = re.compile('[^,;\s]+')
    matched = regex.findall(re.sub('[\[|\]]', '', value))
    if len(matched):
        return matched
    return None


class PublicKey:

    fields = {
        'public_key': fields.String(attribute='raw'),
        'public_key_id': fields.String,
        'created': fields.String
    }

    _post = {
        'public_key': {
            'required': True,
            'type': str,
            'location': 'json'
        }
    }

    @property
    def post(self):
        return parse_args(self._post)


class Resource:
    #resource fields
    fields = {
        'kind': fields.String(attribute='kind'),
        'value': fields.Float
    }

    @classmethod
    def filter(cls, value):
        try:
            (kind, value) = value.split(':')
        except:
            raise ValueError("The resource filter '{}' is invalid".format(
                    value))
        return (kind, float(value))


class Instance:

    class State(fields.Raw):
        def format(self, value):
            if value in INSTANCE_STATES:
                return value

    #Instance fields
    fields = {
        'instance_id': fields.String,
        'created': fields.DateTime,
        'state': State,
    }

    filter_fields = ( 'public_key_id' )

    _delete = {
        'all': {
            'required': False,
            'type': bool,
            'default': False
        },

        'state': {
            'required': False
        },

        'instance_ids': {
            'required': False,
            'help': 'Please specify a valid instance_id'
        }
    }

    _get = {
        'all': {
            'required': False,
            'type': bool
            },
        'state': {
            'required': False
        },
        'resource_filter': {
            'required': False,
            'action': 'append'
        }
    }

    _post = {
        'cores': {
            'type': float,
            'help': 'Please specify required amount of CPU cores',
            'required': True,
            'location': 'json'
        },
        'memory': {
            'type': float,
            'help': 'Please specify required amount of RAM on MiB',
            'required': True,
            'location': 'json'

            },
        'disk': {
            'type': float,
            'help': 'Please specify required amount of disk size on MiB',
            'required': True,
            'location': 'json'

            },
        'bw_out': {
            'type': float,
            'help': 'Please specify required amount of outgoing'
            'bandwidth on MiB',
            'required': True,
            'location': 'json'

            },
        'bw_in': {
            'type': float,
            'help': 'Please specify required amount of incoming' 
            'bandwidth on MiB',
            'required': True,
            'location': 'json'

            },
        'callback': {
            'type': types.url,
            'help': 'URL callback for post notification on state change',
            'location': 'json'
            }
    }
    
    def __init__(self):
        self.resource = Resource()
        self.fields.update(
            { 'resources': fields.Nested(self.resource.fields) }
        )

    def type_handler(self, method, entry, callback):
        getattr(self, '_' + method)[entry]['type'] = callback
        
    @property
    def post(self):
        return parse_args(self._post)

    @property
    def get(self):
        self.type_handler('get', 'state', self.type)
        self.type_handler('get', 'resource_filter', self.resource.filter)
        return parse_args(self._get)

    @property
    def delete(self):
        self.type_handler('delete', 'state', self.type)
        self.type_handler('delete', 'instance_ids', self.instances)
        return parse_args(self._delete)

    def instances(self, value):
        parsed = parse_list(value)
        if parsed is None:
            raise ValueError('The provided instance_ids are invalid')
        return filter(lambda i: i is not None, parsed)

    def type(self, value):
        if not value in INSTANCE_STATES:
            raise ValueError("The instance state '{}' is invalid".format(value))
        return value
    

class Token:
    fields = {
        'value' : fields.String,
        'until' : fields.DateTime(attribute='valid_until')
    }
