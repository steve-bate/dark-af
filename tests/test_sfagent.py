# Tests for SpiderFootAgent adapter

import pytest

import darkaf.agents.spiderfoot
from darkaf.core import DataEvent


class AgentContextStub:
    def __init__(self):
        self.events = []

    def notify(self, event):
        self.events.append(event)

    def log(self, level, message):
        print(level, message)


def test_sfp_hashes():
    context = AgentContextStub()
    agent = darkaf.agents.spiderfoot.create(context, 'sfp_hashes')
    sha1 = 'd2dffdbbf41026a24f020ea73914667dfae8d2c3'
    md5 = 'd2dffdbbf41026a24f020ea73914667d'
    trigger_event = DataEvent("ANYTHING", f"""
        {sha1}  
         some other stuff {md5}
    """)
    agent.handle_event(trigger_event)
    # TODO convert output events
    # TODO Use structured data instead of formatted strings
    assert len(context.events) == 2
    output_event = context.events.pop(0)
    assert output_event.eventType == 'HASH'
    assert output_event.data == f'[MD5] {md5}'
    output_event = context.events.pop(0)
    assert output_event.eventType == 'HASH'
    assert output_event.data == f'[SHA1] {sha1}'


@pytest.mark.parametrize("filename, expected_event_count", [
    ("boring.txt", 0),
    ("interesting.pdf", 1)
])
def test_sfp_intfiles(filename, expected_event_count):
    context = AgentContextStub()
    agent = darkaf.agents.spiderfoot.create(context, 'sfp_intfiles')
    trigger_event = DataEvent("ANYTHING", filename)
    agent.handle_event(trigger_event)
    # TODO convert output events
    queue_size = len(context.events)
    assert queue_size == expected_event_count
    if queue_size > 0:
        assert context.events[0].data == filename
