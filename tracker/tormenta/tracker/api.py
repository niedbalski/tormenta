#!/usr/bin/env python

from tormenta.core.lxc import INSTANCE_STATES
from tormenta.core.model import Token, Instance
from tormenta.tracker import initialize

from flask import Flask, request
from flask.ext.restful import ( Resource, Api, fields, 
                                marshal_with, marshal, reqparse, abort )
import hashlib
import datetime
import logging
import uuid


logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)

tracker = initialize()


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

            
class InstanceResource(Resource):

    class InstanceState(fields.Raw):
        def format(self, value):
            for k, v in INSTANCE_STATES.items():
                if v == value:
                    return k

    resource_fields = {
        'id': fields.String,
        'created': fields.DateTime,
        'state': InstanceState(),
    }

    method_decorators = [ has_access_token ]

    def get(self, *args, **kwargs):
        instances = Instance.select().where(
                Instance.token == kwargs.get('token'))

        instances = map(lambda i: marshal(i, self.resource_fields), instances)
        instances = {
           'count' : len(instances),
           'instances': instances
        }

        return instances
                
    def post(self, *args, **kwargs):
        """
        Receives a request for a new Instance
        """
        parser = reqparse.RequestParser()
        parser.add_argument('cpus', type=float, required=True,
                            help='Specify required amount of CPU cores')
        parser.add_argument('memory', type=float, required=True,
                            help='Specify required amount RAM memory (MiB)')
        parser.add_argument('disk', type=float, required=True,
                            help='Specify required amount of disk (GiB)')
        parser.add_argument('bw', type=tuple, required=True,
                     help='Specify required amount of bandwidth (MiB)')        

        args = parser.parse_args()


api.add_resource(InstanceResource, '/instance')
api.add_resource(TokenResource, '/token')
