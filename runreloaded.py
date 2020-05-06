from watchgod import run_process, DefaultDirWatcher

class MyWatcher(DefaultDirWatcher):
    def should_watch_file(self, entry):
        return entry.name.endswith(('.py', '.yaml'))

def run():
    subprocess
def main():
    run_process('.',target=run,watcher_cls=MyWatcher)

if __name__ == '__main__':
    main()
