from fuzzywuzzy import process
import pandas as pd
import brickschema

q = """SELECT ?class ?label WHERE {
    ?class rdfs:label ?label .
    { ?class rdfs:subClassOf* brick:Point }
    UNION
    { ?class rdfs:subClassOf* brick:Equipment }
}"""

g = brickschema.Graph().load_file("../../Brick.ttl")
brick = {}
for row in g.query(q):
    brick[str(row[1])] = ({'label': str(row[1]).lower(), 'class': row[0]})

mapping = {}
df = pd.read_csv('oap-points.csv')
for _, row in df.iterrows():
    original = row['name']
    name_tags = set([x.lower() for x in row['name'].split(' ')])
    tags = set(row['typeTags'].split('|')).union(name_tags)
    guesses = process.extract(' '.join(tags), brick.keys(), limit=2)
    print(original)
    print(tags)
    print(guesses)
    print()
    mapping[tuple(tags)] = brick[guesses[0][0]]['class']
