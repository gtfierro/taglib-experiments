import re
from collections import deque
import networkx as nx
from networkx.algorithms import isomorphism
import matplotlib.pyplot as plt
import pandas as pd
import brickschema
from brickschema.namespaces import BRICK, RDFS
from fuzzywuzzy import process, fuzz

class Hierarchy:
    def advance(self):
        raise NotImplementedError
    def expand(self):
        new_frontier = []
        for node in self.frontier:
            for child in self.children(node):
                new_frontier.append(child)
        self.frontier = new_frontier


class BrickHierarchy(Hierarchy):
    _q = """SELECT ?class ?label ?base WHERE {
        ?class rdfs:label ?label .
        {
          ?class rdfs:subClassOf* brick:Point .
          BIND ("point" as ?base)
        }
        UNION
        {
          ?class rdfs:subClassOf* brick:Equipment .
            BIND ("equip" as ?base)
        }
    }"""

    def __init__(self, filename):
        self.brick_file = filename
        self.g = brickschema.Graph().load_file(filename)
        self.brick = {}
        for row in self.g.query(self._q):
            self.brick[row[0]] = {
                # rdfs label of the class
                'label': str(row[1]).lower(),
                # split the label into words
                'tags': tuple(sorted(str(row[1]).lower().split(' '))),
                # the Brick class itself
                'class': row[0],
                # the useful Brick root class
                'base': str(row[2]),
            }
        self.frontier = [BRICK.Temperature_Sensor]

    def children(self, node):
        return self.g.subjects(predicate=RDFS.subClassOf, object=node)

    def all_nodes(self):
        q = deque(self.frontier)
        while q:
            node = q.popleft()
            yield node
            q.extend(self.children(node))

    def to_hierarchy(self):
        g = nx.DiGraph()
        for node in self.all_nodes():
            g.add_node(node)
        for node in self.all_nodes():
            for child in self.children(node):
                g.add_edge(node, child)
        return g

    @property
    def frontier_labels(self):
        return [self.brick[node]['label'] for node in self.frontier]


class HaystackHierarchy(Hierarchy):
    def __init__(self, filename):
        self.haystack_file = filename
        df = pd.read_csv(filename)
        self.haystack = {}
        replacements = {
            'equip': 'equipment',
            'sp': 'setpoint',
            'cmd': 'command',
            'elec': 'electrical',
            'freq': 'frequency',
            'occ': 'occupied',
            'temp': 'temperature',
        }
        for _, row in df.iterrows():
            proto = row.pop('proto')
            original = proto
            tags = set(row.dropna().keys())
            for key, value in replacements.items():
                proto = re.sub(f"{key}", f"{value}", proto)
                if key in tags:
                    tags.remove(key)
                    tags.add(value)
            tags = tuple(sorted(tags))
            self.haystack[tags] = ({
                # the essential 'type' of the tag set
                'base': 'point' if 'point' in tags else 'equip' if 'equipment' in tags else '',
                # a clean  text label
                'label': proto,
                # the original proto string
                'proto': original,
                # tags associated with the proto
                'tags': tags,
            })
        self.frontier = [("point", "sensor", "temperature")]

    def tagset(self, node):
        return self.haystack[node]['tags']

    def children(self, node):
        return [k for k, v in self.haystack.items()
                if set(v['tags']).issuperset(self.tagset(node))
                and len(v['tags']) == len(self.tagset(node)) + 1]

    def to_hierarchy(self):
        g = nx.DiGraph()
        for node in self.haystack.keys():
            g.add_node(node)
        for node in self.haystack.keys():
            for child in self.children(node):
                g.add_edge(node, child)
        return g

    @property
    def frontier_labels(self):
        return self.labels_for(self.frontier)

    def labels_for(self, queue):
        return [self.haystack[node]['label'] for node in queue]

    @property
    def frontier_tags(self):
        return self.tags_for(self.frontier)

    def tags_for(self, queue):
        return [self.haystack[node]['tags'] for node in queue]


brick = BrickHierarchy("../../Brick.ttl")
ph = HaystackHierarchy("protos.csv")


class MyGraphMapper(isomorphism.DiGraphMatcher):
    def __init__(self, brick, haystack):
        self.brick = brick
        self.brick_hierarchy = brick.to_hierarchy()
        nx.draw(self.brick_hierarchy)
        plt.savefig('brick.png')
        self.ph = haystack
        self.ph_hierarchy = haystack.to_hierarchy()
        nx.draw(self.ph_hierarchy)
        plt.savefig('ph.png')
        super().__init__(self.brick_hierarchy, self.ph_hierarchy, self.node_match)

    def node_match(self, brick_node, ph_node):
        print(brick_node, ph_node)
        return True

    def semantic_feasibility(self, brick_node, ph_node):
        print(brick_node, ph_node)
        return True

matcher = MyGraphMapper(brick, ph)
print(matcher.is_isomorphic())
print(matcher.mapping)

# for brick_node in brick.all_nodes():
#     brick_tags = brick.brick[brick_node]['tags']
#     print(f"{brick_node} {brick_tags}")
#     phstack = deque(ph.frontier)
#     while phstack:
#         node = phstack.popleft()
#         print(fuzz.token_sort_ratio(brick_tags, node), node)
#         phstack.extend(ph.children(node))

# mapping = {}
# haystackstack = deque(ph.frontier)
# brick_nodes = brick.all_nodes()
# node = next(brick_nodes)
# node_match = ' '.join(brick.brick[node]['tags'])
# print(f"Compare node {node}")
# while len(haystackstack) > 0:
#     match_map = {' '.join(ts): ts for ts in haystackstack}
#     res = process.extractOne(node_match, match_map.keys())
#     assert res is not None
#     choice, score = res
#     choice = match_map[choice]
#     print(f"{brick.brick[node]['label']} -> {ph.haystack[choice]['label']} with score {score}")
#     if score < 90:
#         new_node = haystackstack.popleft()
#         haystackstack.extend(ph.children(new_node))
#         continue
#     mapping[node] = choice
#     haystackstack.extend(ph.children(choice))
#     haystackstack.remove(choice)
#     try:
#         node = next(brick_nodes)
#     except StopIteration:
#         break

from pprint import pprint
# pprint(mapping)

# print(f"Brick frontier: {brick.frontier_labels}")
# print(f"Haystack frontier: {ph.frontier_labels}")
# for node in brick.frontier:
#     print(node)
#     res = process.extract(brick.brick[node]['label'], ph.frontier_labels)
#     print(res)
