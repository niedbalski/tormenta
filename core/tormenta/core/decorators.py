#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from flask.ext.restful import reqparse, abort
from tormenta.core.model import Token

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'


def has_access_token(controller):
    '''
    Checks if request has access-token header
    '''
    
    header = 'X-Access-Token'

    def wrap(*args, **kwargs):

        parser = reqparse.RequestParser()
        parser.add_argument(header, 
                            type=str, 
                            location='headers', 
                            help='Access token for authentication')

        args = parser.parse_args()

        if args[header] is None:
            return abort(401)
        try:
            token = Token.get(value=args[header])
        except:
            return abort(401)

        kwargs['token'] = token
        return controller(*args, **kwargs)

    return wrap
