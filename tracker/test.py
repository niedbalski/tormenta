from tormenta.core.config import settings

import requests
import json
import pprint
import sys

headers = {
        'X-Access-Token': '5c02b8228f8fb8fbf614104eb62bf4a8a2a00955dab54ae5de7321aa2f917eb7',
        'Content-Type': 'application/json'
}

#r = requests.get('http://127.0.0.1:5000/instance', headers=headers)
#print r.json()


data = {
  'disk': 5.0,
  'caca': 5.5,
  'bw_in' : 1024.0, 
  'cores': 2.0,
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
data.update({'public_key_id': pkey})

r = requests.post('%s/api/v1/instance' % settings.agent.listen.uri, 
		   data=json.dumps(data), headers=headers)
print r.json()

#r = requests.get('http://127.0.0.1:5000/instance?all=true&state=%s&%s' % (sys.argv[1], sys.argv[2]), headers=headers)
#pprint.pprint(r.json())
#print r.status_code


#r = requests.delete('http://127.0.0.1:5000/instance?all=true&instance_ids=[%s]' % sys.argv[1], headers=headers)
#pprint.pprint(r.json())
#print r.status_code


#r = requests.get('http://127.0.0.1:5000/agent', headers=headers)
#pprint.pprint(r.json())
