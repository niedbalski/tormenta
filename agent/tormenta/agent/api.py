#!/usr/bin/env python

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

from tormenta.core.config import settings
from tormenta.core.tasks import InstanceTask

from tormenta.core.decorators import has_public_key
from tormenta.core.model import (db, PublicKey,
                                 Instance,
                                 InstanceResource as InstanceResourceModel)

from tormenta.agent import (initialize, params)

from flask import Flask, request
from flask.ext.restful import (Resource, Api, marshal_with, marshal, abort)

import beanstalkc
import logging

logger = logging.getLogger('tormenta.agent.api')

app = Flask(__name__)
api = Api(app, prefix='/api/v%d' % settings.options.api_version)


def marshal_and_count(n, r, f=None, **other):
    if not isinstance(r, list):
        r = [r]
    if f:
        r = map(lambda q: marshal(q, f), r)

    d = dict({'count': len(r), '%s' % n: r})
    for k, v in other.items():
        d.update({k: v})
    return d


class PublicKeyResource(Resource):

    params = params.PublicKey()

    @has_public_key
    def get(self, public_key):
        return marshal_and_count('keys', public_key, f=self.params.fields)

    def post(self, *args, **kwargs):
        public_key_id = PublicKey.encode(self.params.post['public_key'])

        try:
            key = PublicKey.get(public_key_id)
        except:
            key = PublicKey.create(public_key_id=public_key_id,
                                   raw=self.params.post['public_key'])

        return marshal_and_count('keys', key, f=self.params.fields)


class InstanceResource(Resource):

    params = params.Instance()

    @has_public_key
    def get(self, public_key):
        """
           List all instances
        """
        instances = Instance.select().where(
            Instance.public_key == public_key)

        if self.params.get['state'] is not None:
            instances = instances.where(
            Instance.state == self.params.get['state'])

        m_instances = []
        for instance in instances:
            resource_filters = self.params.get.get('resource_filter', None)
            if resource_filters:
                if instance.has_resources(resource_filters):
                    m_instances.append(instance)
            else:
                m_instances.append(instance)

        m_instances = map(lambda i: i.hydrate(marshal,
                          self.params.fields,
                          self.params.resource.fields),
                          m_instances)

        return marshal_and_count('instances', m_instances)

    @has_public_key
    def delete(self, public_key):
        """
            Receives a request for destroy a running/requested instance
        """
        if self.params.get['state']:
            instances = instances.where(Instance.state == args['state'])

        instance_ids = args.get('instance_ids', None)
        if instance_ids:
            instance_filters = []
            for instance_id in instance_ids:
                instance_filters.append(Instance.instance_id == instance_id)

            instances = instances.where(reduce(operator.or_,
                                               instance_filters))
        affected = instances.execute()
        return affected

    @has_public_key
    def post(self, public_key):
        """
          Receives a request for a new Instance
        """
        try:
            instance = Instance.create_from_args(self.params.post, public_key)
            job_id = InstanceTask().start(instance.instance_id)
        except Exception as ex:
            logger.error(ex.message)
            return abort(500)

        return marshal_and_count('instances',
                                 instance,
                                 f=self.params.fields,
                                 job_id=job_id)


api.add_resource(PublicKeyResource, '/public_key')
api.add_resource(InstanceResource, '/instance')
