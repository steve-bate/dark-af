import io
import json
import os
import re
import urllib

import urllib.parse
from flask import Flask
from flask_graphql import GraphQLView
import graphene
from graphene import List

from darkaf.agents import spiderfoot
from darkaf.coordinator import AgentContext
from darkaf.core import DataEvent

app = Flask(__name__)
app.debug = True

class AgentResult(graphene.ObjectType):
    type = graphene.String()
    data = graphene.String()

class Agent(graphene.ObjectType):
    uri = graphene.String()
    name = graphene.String()
    description = graphene.String()
    group = graphene.String()
    categories = graphene.List(graphene.String)
    labels = graphene.List(graphene.String)
    provides = graphene.List(graphene.String)
    consumes = graphene.List(graphene.String)
    needsApiKey = graphene.Boolean()

    run = graphene.List(
        AgentResult,
        eventType=graphene.String(),
        eventData=graphene.String())

    @classmethod
    def resolve_run(cls, root, info, eventType, eventData):
        uri = urllib.parse.urlparse(root.uri)
        if uri.scheme == "agent":
            if uri.hostname == "spiderfoot":
                agent_name = uri.path[1:]
                agent_context = AgentContext()
                agent = spiderfoot.create(agent_context, agent_name)
                data_event = DataEvent(eventType, eventData)
                agent.handle_event(data_event)
                results = []
                while agent_context.event_queue.qsize() > 0:
                    e = agent_context.event_queue.get()
                    r = AgentResult(type=e.event_type, data=e.event_data)
                    results.append(r)
                return results

def load_agent_metadata():
    with io.open(os.path.join("spiderfoot_agents.json")) as fp:
        return json.loads(fp.read())

agents = []

for agent in load_agent_metadata():
    agents.append(Agent(
        uri=agent['uri'],
        name=agent['name'],
        description=agent['descr'],
        group=agent['group'],
        categories=agent['cats'],
        labels=agent['labels'] if agent['labels'] != [""] else [],
        provides=agent['provides'],
        consumes=agent['consumes'],
        needsApiKey=agent['needs_api_key'],
    ))

class Query(graphene.ObjectType):
    queryAgents = graphene.Field(
        List(Agent),
        uri=graphene.String(),
        consumes=graphene.String(),
        provides=graphene.String(),
        needsApiKey=graphene.Boolean(),
        label=graphene.String(),
        category=graphene.String(),
        categories=graphene.List(graphene.String)
    )

    @staticmethod
    def _regex_filter(selector, items, accessor):
        m = re.match('/(.*)/', selector)
        if m:
            return filter(
                lambda i: any(re.match(m.group(1), value) is not None
                              for value in accessor(i)),
                items)
        else:
            return filter(lambda i: selector in accessor(i), items)

    @classmethod
    def resolve_queryAgents(
            cls, _, info,
            uri=None,
            consumes=None,
            provides=None,
            needsApiKey=None,
            label=None,
            category=None,
            categories=None
            ):
        resolved_agents = agents
        if uri is not None:
            resolved_agents = filter(lambda a: a.uri == uri, resolved_agents)
        if consumes is not None:
            resolved_agents = cls._regex_filter(consumes, resolved_agents, lambda a: a.consumes)
        if provides is not None:
            resolved_agents = cls._regex_filter(provides, resolved_agents, lambda a: a.provides)
        if needsApiKey is not None:
            resolved_agents = filter(lambda a: a.needsApiKey == needsApiKey, resolved_agents)
        if label is not None:
            resolved_agents = filter(lambda a: label in a.labels, resolved_agents)
        if category is not None:
            resolved_agents = filter(lambda a: category in a.categories, resolved_agents)
        if categories is not None:
            resolved_agents = filter(lambda a: all(c in a.categories for c in categories), resolved_agents)
        return resolved_agents

    getAgent = graphene.Field(
        Agent,
        uri=graphene.String()
    )

    @classmethod
    def resolve_getAgent(
            cls, _, info,
            uri=None
            ):
        for agent in agents:
            if agent.uri == uri:
                return agent


schema = graphene.Schema(query=Query)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

#TODO Add batch query support (used in Apollo-Client)
#app.add_url_rule('/graphql/batch', view_func=GraphQLView.as_view('graphql', schema=schema, batch=True))

if __name__ == '__main__':
    app.run()
