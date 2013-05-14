#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'


from beanstalkc import Connection
from tormenta.core.config import settings

import logging

logger = logging.getLogger(__name__)


class BackgroundTask(Connection):

    def __init__(self, *args, **kwargs):
        Connection.__init__(self, host=settings.options.beanstalk.host,
                            port=settings.options.beanstalk.port)

    def log(self, job, message):
        logger.info('job_id:%d , message:%s' % (job, message))


class InstanceTask(BackgroundTask):

    def __init__(self, *args, **kwargs):
        BackgroundTask.__init__(self)

    def start(self, instance_id):
        try:
            job = self.put(instance_id)
        except Exception as ex:
            logger.debug(ex.message)
            raise
        self.log(job, 'new instance start request %s' % instance_id)
        return job
