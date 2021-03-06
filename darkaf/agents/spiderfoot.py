# Experimental agent wrapper for SpiderFoot "modules"

import re
import sys
import logging
import importlib
from types import ModuleType
from typing import Optional

from darkaf.core import DataEvent, AgentContext
from spiderfoot import sflib
from spiderfoot.sflib import SpiderFootEvent

SFLOG = logging.getLogger('spiderfoot')

HASH_PATTERNS = {
    "MD5": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{32})(?:[^a-fA-F\d]|\b)"),
    "SHA1": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{40})(?:[^a-fA-F\d]|\b)"),
    "SHA256": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{64})(?:[^a-fA-F\d]|\b)"),
    "SHA512": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{128})(?:[^a-fA-F\d]|\b)")
}


def parseHashes(data):
    """Extract all hashes within the supplied content."""
    return [(name, match) for name, pattern in HASH_PATTERNS.items()
            for match in re.findall(pattern, data)]


class SpiderFootDatabaseAdapter:
    @staticmethod
    def scanInstanceGet(scan_id: str) -> tuple:
        return None, None, None, None, None, None


class SpiderFootAdapter:
    def __init__(self, context: AgentContext):
        self.context = context
        self._priority = 0

    def debug(self, message):
        self.context.log(logging.DEBUG, message)

    def info(self, message):
        self.context.log(logging.INFO, message)

    def error(self, message: str, progagateException: bool = False):
        self.context.log(logging.ERROR, message)

    HASH_PATTERNS = {
        "MD5": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{32})(?:[^a-fA-F\d]|\b)"),
        "SHA1": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{40})(?:[^a-fA-F\d]|\b)"),
        "SHA256": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{64})(?:[^a-fA-F\d]|\b)"),
        "SHA512": re.compile(r"(?:[^a-fA-F\d]|\b)([a-fA-F\d]{128})(?:[^a-fA-F\d]|\b)")
    }

    # noinspection PyMethodMayBeStatic
    def parseHashes(self, data):
        return parseHashes(data)

    @staticmethod
    def watchedEvents() -> [str]:
        return ["*"]

    def handleEvent(self, sf_event: SpiderFootEvent) -> None:
        self.debug(f'Published {sf_event}')
        self.context.notify(DataEvent(sf_event.eventType, sf_event.data))

    def dictnames(self) -> dict:
        return {}

    def dictwords(self) -> dict:
        return {}

    def cacheGet(self, key: str, timeout: int) -> Optional[str]:
        return None

    def fetchUrl(self, url: str, **kwargs) -> Optional[dict]:
        return {'content': None}


class SpiderFootAgent:
    ROOT_EVENT = SpiderFootEvent("ROOT", "", "ROOT", None)

    def __init__(self, context: AgentContext, sf_module: ModuleType, opts: Optional[dict] = None):
        opts = opts if opts is not None else {}
        # SpiderFoot event handlers are objects that have the same
        # name as the module.
        self.handler_name = sf_module.__name__.replace('spiderfoot.modules.', '')
        handler_type = getattr(sf_module, self.handler_name)
        self.handler = handler_type()
        self.handler.__sfdb__ = SpiderFootDatabaseAdapter()
        self.spiderfoot = SpiderFootAdapter(context)
        self.handler._listenerModules = [self.spiderfoot]
        self.handler.setup(self.spiderfoot, opts)

    def handle_event(self, event: DataEvent) -> None:
        # Convert to SpiderFootEvent
        # Some modules expect a "Target"
        sf_event = SpiderFootEvent(
            self._translate_event_type(event.event_type),
            event.event_data, "DARK", self.ROOT_EVENT)
        self.handler.handleEvent(sf_event)

    @staticmethod
    def _translate_event_type(event_type):
        return event_type

    def __str__(self):
        return f"<SpiderFootAgent:{self.handler_name}>"


def create(context: AgentContext, name: str, opts: Optional[dict] = None) -> SpiderFootAgent:
    if 'sflib' not in sys.modules:
        # Top-level SF modules not in namespace
        sys.modules['sflib'] = sflib
    sf_module = importlib.import_module(f'spiderfoot.modules.{name}')
    return SpiderFootAgent(context, sf_module, opts)
