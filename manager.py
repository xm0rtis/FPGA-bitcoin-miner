#!/usr/bin/python3

from queue import Queue
import os, subprocess, csv
import threading
import time
import traceback


"""
# How to use:

import Mgr


def process(x):
    # Do the required work
    print(x)

mgr = Mgr(process)
mgr.run(50)    # number of threads = 50

for x in range(1000000):
    # pass the argument to be passed to process function
    mgr.add(x)

mgr.finish()

"""


class Mgr:
    def __init__(self, process):
        self.cv = threading.Condition()
        self.working = False
        self.clue_bank = 0
        self.workers = []
        self.process = process
        self.q = Queue(0)

    def run(self, wnum):
        self.working = True

        for i in range(wnum):
            self.workers.append(Worker(i, self))

    def get_a_clue(self):
        with self.cv:
            if self.clue_bank > 0:
                self.clue_bank -= 1
                return self.clue_bank + 1
            else:
                self.cv.wait()
                return False

    def add(self, item):
        self.q.put(item)
        self.clue_bank += 1
        try:
            with self.cv:
                self.cv.notifyAll()
        except RuntimeError as e:
            print(e)

    def stop(self):
        self.working = False
        with self.cv:
            self.cv.notifyAll()

    def finish(self):
        with self.cv:
            self.cv.notifyAll()
        while self.clue_bank > 0:
            time.sleep(1)

        self.stop()
        for w in self.workers:
            w.join()


class Worker:
    def __init__(self, tid, mgr):
        self.tid = tid
        self.mgr = mgr
        self.thread = threading.Thread(target=self)
        self.thread.start()

    def join(self):
        self.thread.join()

    def __call__(self):
        while self.mgr.working:
            clue = self.mgr.get_a_clue()

            if clue:
                l = self.mgr.q.get()
                self.mgr.process(l)