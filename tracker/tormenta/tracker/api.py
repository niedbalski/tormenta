#!/usr/bin/env python

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from tormenta.core.lxc import INSTANCE_STATES
from tormenta.core.decorators import has_access_token
from tormenta.core.model import ( db, Token, Instance, 
                                  InstanceResource as InstanceResourceModel)
from tormenta.tracker import (initialize, params)

from flask import Flask, request
from flask.ext.restful import ( Resource, Api, 
                                marshal_with, marshal, abort )

import logging


logger = logging.getLogger('tormenta.tracker.api')


app = Flask(__name__)
api = Api(app)

tracker = initialize()

class TokenResource(Resource):

    params = params.Token()

    def _get_access_token(self):
        return Token.create(value=Token.random(), 
                             tracker=tracker)

    def get(self):
        return marshal(self._get_access_token(), self.params.fields)

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
            instances = instances.where(Instance.state == 
                                INSTANCE_STATES[args['state']])
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
        instances = {
           'count' : len(m_instances),
           'instances': m_instances
        }

        return instances

    def delete(self, *args, **kwargs):
        """
        Receives a request for destroy a running/requested instance
        """
        (args, token) = (self.params.delete, kwargs.get('token'))        

        instances = Instance.update(state=INSTANCE_STATES['DELETED']).where(
            Instance.token == kwargs.get('token'))

        if args['state']:
            instances = instances.where(Instance.state == 
                                INSTANCE_STATES[args['state']])
        
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
        (args, token) = (self.params.post, kwargs.get('token'))

        try:
            db.set_autocommit(False)   

            with db.transaction():
                instance = Instance.create(
                    instance_id=Instance.generate_instance_id(token),
                                           state=INSTANCE_STATES['REQUESTED'], 
                                           token=token)

                instance.resources = []
                for resource, value in args.items():
                    if value not in (None, ''):
                        instance.resources.append(
                            InstanceResourceModel.create(
                                kind=resource, value=value, 
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

        return marshal(instance, self.params.fields)


api.add_resource(InstanceResource, '/instance')
api.add_resource(TokenResource, '/token')
