#!/usr/bin/env python

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from tormenta.core.config import settings
from tormenta.core.decorators import has_access_token
from tormenta.core.model import ( db, Token, PublicKey, 
                                  Instance,  
                                  InstanceResource as InstanceResourceModel)

from tormenta.agent import (initialize, params)

from flask import Flask, request
from flask.ext.restful import ( Resource, Api, 
                                marshal_with, marshal, abort )
import logging


logger = logging.getLogger('tormenta.agent.api')


app = Flask(__name__)
api = Api(app, prefix='/api/v%d' % settings.options.api_version)

#agent = initialize()

def marshal_and_count(n, r, f):
    if not isinstance(r, list):
        r = [r]
    r = map(lambda q: marshal(q, f), r)
    return dict({'count': len(r), '%s' % n: r})


class TokenResource(Resource):

    params = params.Token()

    def _get_access_token(self):
        return Token.create(value=Token.encode())

    def get(self):
        return marshal(self._get_access_token(), self.params.fields)


class PublicKeyResource(Resource):

    method_decorators = [ has_access_token ]
    params = params.PublicKey()

    def get(self, *args, **kwargs):
        (args, token) = (self.params.get, kwargs.get('token'))

        keys = PublicKey.select().where(PublicKey.token == token)

        if args['public_key_id']:
            keys = keys.where(PublicKey.public_key_id == args['public_key_id'])

        return marshal_and_count('keys', key, self.params.fields)

    def post(self, *args, **kwargs):
        (args, token) = (self.params.post, kwargs.get('token'))
        
        pkey_param = args['public_key']
        pkey_id = PublicKey.encode(token, pkey_param)

        try:
            key = PublicKey.select().where(PublicKey.token == token).where(
                PublicKey.public_key_id == pkey_id).get()
        except:
            key = PublicKey.create(public_key_id=pkey_id, 
                                   raw=pkey_param, 
                                   token=token)

        return marshal_and_count('keys', key, self.params.fields)


class InstanceResource(Resource):
    method_decorators = [ has_access_token ]
    params = params.Instance()

    def get(self, *args, **kwargs):    
        """
           List all instances
        """
        (args, token) = (self.params.get, kwargs.get('token'))

        instances = Instance.select()

        if args['state']:
            instances = instances.where(Instance.state == args['state'])

        if not args['all']:
            instances = instances.where(
                Instance.token == kwargs.get('token'))

        m_instances = []
        for instance in instances:
            resource_filters = args.get('resource_filter', None)
            if resource_filters:
                if instance.has_resources(resource_filters) == True:
                    m_instances.append(instance)
            else:
                m_instances.append(instance)

        m_instances = map(lambda i: i.hydrate(marshal, 
                                              self.params.fields, 
                                              self.params.resource.fields), 
                                              m_instances)

        return count('instances', m_instances)


    def delete(self, *args, **kwargs):
        """
            Receives a request for destroy a running/requested instance
        """
        (args, token) = (self.params.delete, kwargs.get('token'))        

        instances = Instance.update(state='REMOVED').where(
            Instance.token == kwargs.get('token'))

        if args['state']:
            instances = instances.where(Instance.state == args['state'])
        
        instance_ids = args.get('instance_ids', None)
        if instance_ids:
            instance_filters = []
            for instance_id in instance_ids:
                instance_filters.append(Instance.instance_id == instance_id)

            import operator
            instances = instances.where(reduce(operator.or_, 
                                               instance_filters))
        affected = instances.execute()
        return affected


    def post(self, *args, **kwargs):
        """
          Receives a request for a new Instance
        """
        try:
            instance = Instance.create_from_args(self.params.post, kwargs)
        except Except as ex:
            logger.error(ex.message)
            return abort(500)

        return marshal_and_count('instances', instance, self.params.fields)


api.add_resource(TokenResource, '/token')
api.add_resource(PublicKeyResource, '/public_key')
api.add_resource(InstanceResource, '/instance')
