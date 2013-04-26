#!/usr/bin/env python

from tormenta.core.lxc import INSTANCE_STATES
from tormenta.core.model import db, Token, Instance, InstanceResource
from tormenta.tracker import initialize

from flask import Flask, request
from flask.ext.restful import ( Resource, Api, fields, types,
                                marshal_with, marshal, reqparse, abort )
import hashlib
import datetime
import logging
import uuid


logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

tracker = initialize()

def parse_args(request_parameter_map, all_valid=True):    
    parser = reqparse.RequestParser()
    add_arg = parser.add_argument

    for param, values in request_parameter_map.iteritems():
        add_arg(param, **values)

    args = parser.parse_args()
    return args
    
def has_access_token(func):

    HEADER_NAME = 'X-Access-Token'

    def wrapper(*args, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument(HEADER_NAME, 
                            type=str, 
                            location='headers', 
                            help='Access token for authentication')

        args = parser.parse_args()

        if args[HEADER_NAME] is None:
            return abort(401)

        token = Token.get(value=args[HEADER_NAME])        
        if not token:
            return abort(401)

        kwargs.update({'token' : token})
        return func(*args, **kwargs)

    return wrapper


token_resource_fields = {
    'value' : fields.String,
    'until' : fields.DateTime(attribute='valid_until')
}

class TokenResource(Resource):

    def _get_access_token(self):
        hashed = hashlib.sha256(str(uuid.uuid4())).hexdigest()
        return Token.create(value=hashed, 
                             tracker=tracker)
        
    @marshal_with(token_resource_fields)
    def get(self):
        return self._get_access_token()


class InstanceState(fields.Raw):

    def format(self, value):
        for k, v in INSTANCE_STATES.items():
            if v == value:
                return k

    @classmethod
    def type(cls, value):
        if not value in INSTANCE_STATES.keys():
            raise ValueError("The instance state '{}' is invalid".format(value))
        return value

class InstanceAPIResource(Resource):

    resource_fields = {
        'kind': fields.String(attribute='kind'),
        'value': fields.Float
    }

    instance_fields = {
        'instance_id': fields.String,
        'created': fields.DateTime,
        'state': InstanceState(),
        'resources': fields.Nested(resource_fields)
    }

    method_decorators = [ has_access_token ]
        
    def _resource_filter(self, value):
        try:
            (kind, value) = value.split(':')
        except:
            raise ValueError("The resource filter '{}' is invalid".format(
                    value))
        return (kind, float(value))

    def get(self, *args, **kwargs):    
        param_map = {
            'all': {
                'required': False,
                'type': bool
            },
            'state': {
                'required': False,
                'type': InstanceState.type
            },
            'resource_filter': {
                'required': False,
                'type':  self._resource_filter,
                'action': 'append'
            }
        }


        instances = Instance.select()

        args = parse_args(param_map)
        if 'resource_filter' in args:
            instances = instances.join(InstanceResource)

            filters = args['resource_filter']
            for f in filters:
                (kind, value) = f
                instances = instances.where(
                    (InstanceResource.kind == kind) & 
                                   (InstanceResource.value <= value))

        if args['state'] is not None:
            instances = instances.where(Instance.state == 
                                INSTANCE_STATES[args['state']])

        if not args['all']:
            instances = instances.where(
                Instance.token == kwargs.get('token'))

        print instances.sql

        m_instances = []
        for instance in instances:
            instance.resources = []
            for resource in instance.instanceresource_set:
                instance.resources.append(
                    marshal(resource, self.resource_fields))
            m_instances.append(marshal(instance, self.instance_fields))



        instances = {
           'count' : len(m_instances),
           'instances': m_instances
        }

        return instances
                
    def post(self, *args, **kwargs):
        """
          Receives a request for a new Instance
        """

        param_map = {
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
                #'skip_values' : [ None ],
                'location': 'json'
            }
        }

        args = parse_args(param_map)        
        token = kwargs['token']

        try:
            db.set_autocommit(False)   

            instance = Instance.create(
                instance_id=Instance.generate_instance_id(token),
                                       state=INSTANCE_STATES['REQUESTED'], 
                                       token=token)

            instance.resources = []
            for resource, value in args.items():
                if value not in (None, ''):
                    instance.resources.append(
                        InstanceResource.create(kind=resource, value=value, 
                                            instance=instance))
            
        except Exception as ex:
            logger.error('Cannot create new resources'
                         ', exception: %s' % ex.message)
            db.rollback()
            return abort(500)
        else:
            db.commit()
        finally:
            db.set_autocommit(True)

        return marshal(instance, self.instance_fields)



api.add_resource(InstanceAPIResource, '/instance')
api.add_resource(TokenResource, '/token')
