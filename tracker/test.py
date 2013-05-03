import requests
import json
import pprint
import sys

headers = {
        'X-Access-Token': 'af27cb2fa64017f21f36fc55b289ceb8ec41bd2ea5b0f753726d0507932b1407',
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

#r = requests.post('http://127.0.0.1:5000/instance', data=json.dumps(data), headers=headers)
#print r.json()


#r = requests.get('http://127.0.0.1:5000/instance?all=true&state=%s&%s' % (sys.argv[1], sys.argv[2]), headers=headers)
#pprint.pprint(r.json())
#print r.status_code


r = requests.delete('http://127.0.0.1:5000/instance?all=true&instance_ids=[%s]' % sys.argv[1], headers=headers)
pprint.pprint(r.json())
print r.status_code
