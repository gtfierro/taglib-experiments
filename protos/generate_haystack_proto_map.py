import re
import pickle
import dedupe
import pandas as pd
import brickschema

q = """SELECT ?class ?label ?base WHERE {
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

g = brickschema.Graph().load_file("../../Brick.ttl")

brick = {}
for row in g.query(q):
    brick[str(row[0])] = {'label': str(row[1]).lower(), 'class': row[0], 'base': str(row[2])}

df = pd.read_csv('protos.csv')
haystack = {}
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
    for key, value in replacements.items():
        proto = re.sub(f"{key}", f"{value}", proto)
        # proto = proto.replace(key, value)
    tags = set(row.dropna().keys())
    haystack[proto] = ({
        'base': 'point' if 'point' in tags else 'equip' if 'equip' in tags else '',
        'label': proto, 'proto': original, 'tags': tags
    })

for bk, bv in brick.items():
    for hk, hv in haystack.items():
        if bv['base'] == hv['base']:
            print(f"{bv['label']}|{hv['label']}")
    print('---' * 20)

fields = [
    {'field': 'label', 'type': 'String'},
    {'field': 'base', 'type': 'String'},
]
linker = dedupe.RecordLink(fields)
linker.prepare_training(brick, haystack)
dedupe.console_label(linker)
linker.train()
print('clustering...')
linked_records = linker.join(brick, haystack, 0.0)

mapping = {}
print('# duplicate sets', len(linked_records))
for cluster_id, (cluster, score) in enumerate(linked_records):
    print('cluster id', cluster_id)
    print('cluster score', score)
    brick_record, haystack_record = cluster
    mapping[haystack[haystack_record]['proto']] = brick[brick_record]['class']
with open('haystack_proto_map.pkl', 'wb') as f:
    pickle.dump(mapping, f)
