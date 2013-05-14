#!/usr/bin/env python
#-*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

import logging
import datetime
import hashlib
import hmac
import uuid
import operator

from tormenta.core.config import settings
from tormenta.core.driver import INSTANCE_STATES

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


class PublicKey(BaseModel):
    public_key_id = CharField()
    created = DateTimeField(default=datetime.datetime.now)
    raw = TextField()

    @classmethod
    def encode(cls, value):
        return encode(random(), value)


class Instance(BaseModel):
    instance_id = CharField(index=True, unique=True, primary_key=True)
    created = DateTimeField(default=datetime.datetime.now)
    state = CharField(default='NOSTATE', choices=INSTANCE_STATES)
    public_key = ForeignKeyField(PublicKey, related_names='instances',
                                 cascade=True)

    @classmethod
    def create_from_args(cls, args, public_key):
        try:
            db.set_autocommit(False)

            with db.transaction():
                instance = Instance.create(
                    instance_id=Instance.encode(public_key),
                    public_key=public_key,
                    state='NOSTATE')

                instance.resources = []
                for resource, value in args.items():
                    if resource not in ('public_key_id'):
                        if value not in (None, ''):
                            instance.resources.append(
                                InstanceResource.create(kind=resource,
                                                        value=value,
                                                        instance=instance))
        except Exception as ex:
            logger.error('Cannot create new resources'
                         ', exception: %s' % ex.message)
            db.rollback()
            raise
        else:
            db.commit()
        finally:
            db.set_autocommit(True)

        return instance

    @classmethod
    def encode(cls, public_key):
        return encode(public_key.public_key_id, random())

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

        resources = resources.where(
            reduce(operator.or_, filter_conditions))

        count = 0
        for resource in resources:
            count += 1

        return count >= len(filters)


class InstanceResource(BaseModel):
    kind = CharField(choices=('disk', 'memory', 'swap',
                              'shared', 'cores', 'bw_in',
                              'bw_out'))
    value = FloatField()
    instance = ForeignKeyField(Instance, related_names='resources',
                               cascade=True)


models = [PublicKey, Instance, InstanceResource]


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
