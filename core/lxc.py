#!/usr/bin/env python
# -*- coding: utf-8 -*- 

__author__ = 'Jorge Niedbalski R. <jnr@pyrosome.org>'


from act_as_executable import act_as_executable

import logging


class LXC:
    """
      LXC wrapper
    """
    DEFAULT_RUN_TIMEOUT = 3
 
    ( RUNNING, FROZEN, 
      READY, STARTING, STARTED, STOPPING, STOPPED ) = xrange(0, 7)    

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)    

    def list_filter(self, value):
        '''
        Parse the lxc-list command output and produce a dict
        indexed by machine state
        '''
        lines = filter(lambda l: l not in (None, ''), 
                    [ x.strip(' ') for x in value.splitlines()])

        def get_state_idx(lines):
            r = []
            for idx, line in enumerate(lines):
                if hasattr(self, line):
                    r.append((idx, line))
            return r

        values = dict()
        ret = get_state_idx(lines)
        for i, n in enumerate(ret):
            try:
                values[n[1]] = lines[n[0]+1:ret[i+1][0]]
            except IndexError:
                values[n[1]] = lines[n[0]+1:]
        return values

    @act_as_executable('lxc-create --name $args_0 '
                       '--template $template -- -r $release')
    def create(self, *args, **results):
        print args, results

    @act_as_executable('lxc-freeze --name $args_0')
    def freeze(self, *args, **results):        
        print "instance_id:%s , %s" % (instance_id, kwargs)

    @act_as_executable('lxc-unfreeze --name $args_0')
    def unfreeze(self, *args, **results):
        pass

    @act_as_executable('lxc-restart --name $args_0')
    def restart(self, *args, **results):
        pass

    @act_as_executable('lxc-start --name $args_0')
    def start(self, *args, **results):
        print results, args

    @act_as_executable('lxc-stop --name $args_0')
    def stop(self, *args, **results):
        print results, args

    @act_as_executable('lxc-destroy --name $args_0')
    def destroy(self, *args, **results):
        print 'instance_id %s, %s' % (args, results)

    @act_as_executable('lxc-monitor --name $args_0')
    def monitor(self, *args, **results):
        pass

    @act_as_executable('lxc-list --name $args_0')
    def list(self, *args, **results):
        return results
