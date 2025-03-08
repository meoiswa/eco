import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os


class RestartHandler(FileSystemEventHandler):
    def __init__(self, process):
        self.process = process

    def on_any_event(self, event):
        if event.event_type in ('modified', 'created', 'deleted') and event.src_path.endswith('.py'):
            print(f"Change detected in {event.src_path}. Restarting bot...")
            self.process.kill()
            self.process = subprocess.Popen(["python3", "edcolbot.py"])


def main():
    # Start your bot script
    process = subprocess.Popen(["python3", "edcolbot.py"])
    
    event_handler = RestartHandler(process)
    observer = Observer()
    observer.schedule(event_handler, path=os.getcwd(), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.join()
        process.kill()


if __name__ == "__main__":
    main()
