#!/usr/bin/env python

from tormenta.core.model import Token

from flask import Flask, request
from flask.ext.restful import Resource, Api

import datetime
import logging
import uuid


logger = logging.getLogger(__name__)

app = Flask(__name__)
api = Api(app)


class TokenResource(Resource):

    def _get_access_token(self):
        try:
            token = Token()
            token.value = uuid.uuid4().__str__()
            token.save()
        except Exception as ex:
            logger.error(ex.message)
            raise
        return token
        
    def get(self):
        return {
            'access-token': self._get_access_token() 
        }


api.add_resource(TokenResource, '/token')
