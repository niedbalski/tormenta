from tormenta.agent.api import app
from tormenta.core.config import settings

import logging

logging.basicConfig(level=logging.INFO)

app.run(host=settings.agent.listen.hostname,
             port=settings.agent.listen.port,
             debug=True)
