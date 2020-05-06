import uvicorn
from ruamel.yaml import YAML
from hostthedocs import getconfig
from watchgod import run_process, DefaultDirWatcher

class MyWatcher(DefaultDirWatcher):
    def should_watch_file(self, entry):
        return entry.name.endswith(('.py', '.yaml'))

def main():
    run_process('.',target=run,watcher_cls=MyWatcher)

def run():
    yaml = YAML()
    with open('logging.yaml','r') as logconffile:
        log_conf = yaml.load(logconffile)
    uvicorn.run('hostthedocs.app:app', host=getconfig.host, port=getconfig.port, log_config=log_conf)

if __name__ == '__main__':
    main()
