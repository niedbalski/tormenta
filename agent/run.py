from tormenta.agent.api import app
from tormenta.core.config import settings

app.run(host=settings.agent.listen.hostname,
             port=settings.agent.listen.port,
             debug=True)
