#!/usr/bin/env python3

import threading

class threadWorker(object):
    def __init__(self, worker, daemon):
        self._worker = worker
        self._threadWork = threading.Thread(target=self._worker)
        self._daemon = daemon
    
    def get_daemon(self):
        return self._daemon

    def set_daemon(self, value):
        self._daemon = value

    def start(self):
        self._threadWork.daemon = self._daemon
        self._threadWork.start()

    def stop(self):
        self._threadWork.join()

class threadHandler:
    def __init__(self, workers = []):
        self._workers = workers

    def start(self):
        for worker in self._workers:
            worker.start()

    def stop(self):
        for worker in self._workers:
            worker.stop()
