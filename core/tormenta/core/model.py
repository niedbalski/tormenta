#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'

import logging
import datetime
import hashlib

from .lxc import INSTANCE_STATES
from .config import settings

from peewee import *
from peewee import create_model_tables


logger = logging.getLogger('tormenta.core.models')


class BaseModel(Model):

    class Meta:
        database = settings.node.database.conn


class Agent(BaseModel):
    public_key = TextField() 
    
class Tracker(BaseModel):
    public_key = CharField(primary_key=True)

    @classmethod
    def get_or_create(cls, path):

        with open(path) as public_key:
            readed = public_key.read()
        hashed = hashlib.sha256(readed).hexdigest()
        try:
            tracker = cls.get(Tracker.public_key == hashed)
        except:
            tracker = cls.create(public_key=hashed)
        return tracker

class TrackerAgent(BaseModel):
    agent = ForeignKeyField(Agent)
    tracker = ForeignKeyField(Tracker)


class Token(BaseModel):
    value = CharField(index=True, unique=True)
    created = DateTimeField(default=datetime.datetime.now)
    valid_until = DateTimeField(default=datetime.datetime.now() + 
                                datetime.timedelta(days=30))
    tracker = ForeignKeyField(Tracker, related_names='tokens',
                            cascade=True)

class Instance(BaseModel):

    id = CharField(index=True, unique=True)
    created = DateTimeField(default=datetime.datetime.now)
    state = IntegerField(choices=(INSTANCE_STATES.values()))

    token = ForeignKeyField(Token, related_names='instances',
                            cascade=True)


class Usage(BaseModel):
    unit  = CharField(choices=('MB', 'KB', 'Bytes'))
    value = FloatField()
    instance = ForeignKeyField(Instance, related_name='usages', 
                               cascade=True)


class Resource(BaseModel):
    kind = CharField(choices=('disk', 'memory', 'swap', 'shared', 'cores'))
    identifier = TextField()
    
    instance = ForeignKeyField(Instance, related_names='resources', 
                               cascade=True)


def setup_database():
    try:
        settings.node.database.conn.connect()

        #create tables on the database
        create_model_tables([Usage, 
                         Resource, 
                         Instance, 
                         Token, 
                         Agent, 
                         Tracker, 
                         TrackerAgent], fail_silently=True)
    except Exception as ex:
        logger.error(ex.message)
        raise


setup_database()
