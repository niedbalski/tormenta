#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from flask.ext.restful import reqparse, abort, request
from tormenta.core.model import PublicKey

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'


parser = reqparse.RequestParser()


def has_public_key(controller):

    header = 'Public-Key-Id'

    def wrapper(self, *args, **kwargs):
        parser.add_argument(header,
                            type=str,
                            location='headers',
                            help='Specify %s on headers' % header)

        args = parser.parse_args()

        if not (header in args and args[header] is not None):
            return abort(401)
        try:
            public_key = PublicKey.select().where(
                PublicKey.public_key_id == args[header]).get()
        except:
            return abort(401)

        return controller(self, public_key)

    return wrapper
