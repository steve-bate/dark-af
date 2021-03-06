"""
Initial experimentation with using concurrent.futures executors run
agents.
"""

import concurrent.futures
import logging
import queue

from darkaf.agents import spiderfoot
from darkaf.core import DataEvent


class AgentContext:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.log_queue = queue.Queue()

    def log(self, level: int, message: str) -> None:
        self.log_queue.put((level, message))

    def notify(self, event):
        self.event_queue.put(event)


class AgentCoordinator:
    def __init__(self):
        self.futures = []
        self.executor = concurrent.futures.ThreadPoolExecutor()

    def submit(self, agent, event, context):
        future = self.executor.submit(agent.handle_event, event, context)
        self.futures.append(future)


def _prototype():
    import sys

    log_formatter = "%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(threadName)s] "
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=log_formatter)

    coord = AgentCoordinator()
    context = AgentContext()
    sha1 = 'd2dffdbbf41026a24f020ea73914667dfae8d2c3'
    md5 = 'd2dffdbbf41026a24f020ea73914667d'
    trigger_event1 = DataEvent("ANYTHING", f"""
        {sha1}  
         some other stuff {md5}
    """)
    coord.submit(spiderfoot.create(context, 'sfp_hashes'), trigger_event1, context)
    trigger_event2 = DataEvent("ANYTHING", f"""
        {sha1.replace('d', 'f')}  
    """)
    coord.submit(spiderfoot.create(context, 'sfp_hashes'), trigger_event2, context)

    for f in concurrent.futures.as_completed(coord.futures):
        print(f'{f} completed')


if __name__ == '__main__':
    _prototype()
