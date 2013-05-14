from tormenta.agent.api import app

import logging

logging.basicConfig()

app.run(host='0.0.0.0', debug=True)
