from tormenta.core.config import settings

import requests
import json
import pprint
import sys

headers = {
    'Content-Type': 'application/json'
}

data = {
  'disk': 5.0,
  'bw_in' : 1024.0,
  'cores': 1.0,
  'bw_out' : 1024.0,
  'memory': 128.0
}

with open('/home/aktive/src/tormenta/test.pub') as key:
    readed = key.read()

public_key = {
  'public_key': readed
}

r = requests.post('%s/api/v1/public_key' % settings.agent.listen.uri,
            data=json.dumps(public_key), headers=headers)

r = r.json()

pkey = r['keys'][0]['public_key_id']

headers.update({'public_key_id': pkey})

print headers

r = requests.post('%s/api/v1/instance' % settings.agent.listen.uri, 
            data=json.dumps(data), headers=headers)

instance = r.json()

#print instance
instance_id = instance['instances'][0]['instance_id']

print 'Requesting for ... %s' % instance_id

r = requests.get('%s/api/v1/instance?instance_ids=[%s]' % 
            (settings.agent.listen.uri, instance_id), headers=headers)

#print r.json()


print 'Requesting for .. %s with memory:%s' % (instance_id, sys.argv[1])

r = requests.get('%s/api/v1/instance?instance_ids=[%s]&resource_filter=memory:%s' % 
            (settings.agent.listen.uri, instance_id, sys.argv[1]), headers=headers)
#print r.json()


#r = requests.get('http://127.0.0.1:5000/instance?all=true&state=%s&%s' % (sys.argv[1], sys.argv[2]), headers=headers)
#pprint.pprint(r.json())
#print r.status_code


#r = requests.delete('http://127.0.0.1:5000/instance?all=true&instance_ids=[%s]' % sys.argv[1], headers=headers)
#pprint.pprint(r.json())
#print r.status_code


#r = requests.get('http://127.0.0.1:5000/agent', headers=headers)
#pprint.pprint(r.json())
