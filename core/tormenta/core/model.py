#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

import logging
import datetime
import hashlib
import hmac
import uuid
import operator

from tormenta.core.driver import INSTANCE_STATES

from .config import settings

from peewee import *
from peewee import create_model_tables


logger = logging.getLogger('tormenta.core.models')


def encode(token, value):
    return hmac.new(str(token), value, hashlib.sha256).hexdigest()

def random():
    return hashlib.sha256(
        str(uuid.uuid4())).hexdigest()


class BaseModel(Model):
    class Meta:
        database = settings.options.database.connection


class Token(BaseModel):
    value = CharField(index=True, unique=True)
    created = DateTimeField(default=datetime.datetime.now)
    valid_until = DateTimeField(default=datetime.datetime.now() +
                                datetime.timedelta(days=30))

    def has_public_key_id(self, public_key_id):
        for key in self.publickey_set:
            if key.public_key_id == public_key_id:
                return key
        return False

    @classmethod
    def encode(cls):
        return random()


class PublicKey(BaseModel):
    public_key_id = CharField()
    token = ForeignKeyField(Token, related_names='keys')
    created = DateTimeField(default=datetime.datetime.now)
    raw = TextField()

    @classmethod
    def encode(cls, token, value):
        return encode(token.value, value)


class Instance(BaseModel):
    instance_id = CharField(index=True, unique=True, primary_key=True)

    created = DateTimeField(default=datetime.datetime.now)
    state = CharField(default='NOSTATE', choices=INSTANCE_STATES)

    public_key = ForeignKeyField(PublicKey, related_names='instances',
                                 cascade=True)


    @classmethod
    def create_from_args(cls, args, **kwargs):
        try:
            (public_key_id, token) = (args['public_key_id'], 
                                      kwargs.get('token', None))

            public_key = token.has_public_key_id(public_key_id)

            if not public_key:
                raise Exception('Not found public_key_id %s associated' % 
                                public_key_id)
            db.set_autocommit(False)   

            with db.transaction():
                instance = Instance.create(
                    instance_id=Instance.encode(token),
                                           public_key=public_key,
                                           state='NOSTATE', 
                                           token=token)
                instance.resources = []
                for resource, value in args.items():
                    if resource not in ('public_key_id') \
                        and value not in (None, ''):
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

    @classmethod
    def encode(cls, token):
        return encode(token.value, random())

    def hydrate(self, cb, i_fields, r_fields):
        self.resources = []
        for resource in self.instanceresource_set:
            self.resources.append(cb(resource, r_fields))
        return cb(self, i_fields)

    def has_resources(self, filters):
        filter_conditions = []

        resources = InstanceResource.select().where(
            InstanceResource.instance == self)
        
        for f in filters:
            (kind, value) = f
            filter_conditions.append(
                (InstanceResource.kind == kind) &
                (InstanceResource.value <= value))

        resources = resources.where(reduce(operator.or_, 
                                           filter_conditions))
        count = 0
        for resource in resources:
            count += 1

        return  count >= len(filters)
                

class InstanceResource(BaseModel):
    kind = CharField(choices=('disk', 'memory', 'swap', 
                              'shared', 'cores', 'bw_in', 'bw_out'))
    value = FloatField()
    instance = ForeignKeyField(Instance, related_names='resources',
                               cascade=True)


models = [PublicKey, Token, Instance, InstanceResource]

def setup_database():
    try:
        db = settings.options.database.connection
	db.connect()
        create_model_tables(models, fail_silently=True)
    except Exception as ex:
        logger.error(ex.message)
        raise
    return db


db = setup_database()
