import uvicorn
import yaml
from hostthedocs import getconfig, app

if __name__ == '__main__':
    with open('logging.yaml','r') as logconffile:
        log_conf = yaml.safe_load(logconffile)
    uvicorn.run(app.app, host=getconfig.host, port=getconfig.port, log_config=log_conf)
