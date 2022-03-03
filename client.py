import brickschema
from brickschema.namespaces import BRICK
import readline
from collections import defaultdict

# use any haystack tag library that is necessary (and translate between them!)
# use existing haystack software on top of semantic web stuff!
# haystack doesn't have to worry about RDF-izing
# TODO: add missing concepts to Brick
# TODO: how to handle subgraphs (haystack entity "split" into equip + point)
# TODO: document how to create your own mapping
# implement haystack v3 API? (just one endpoint?)
# do the SHACL shapes in Brick / 223P
# a large controls company says this will help them support haystack

g = brickschema.Graph()
g.load_file("../../Brick.ttl")
#g.load_file("haystack_proto_map.ttl")
#g.load_file("oap_map.ttl")
#g.load_file("brick_tag_map.ttl")
g.load_file("simple_map.ttl")
g.load_file("../../examples/g36/g36-vav-a2.ttl")
g.expand("shacl")
g.serialize('/tmp/test.ttl', format='turtle')

def find_entities(tags):
    clauses = [
        f'?ent brick:hasTag "{tag}" .' for tag in tags
    ]
    query = f"""
        SELECT DISTINCT ?ent
        WHERE {{
            {' '.join(clauses)}
        }}"""
    res = defaultdict(list)
    for row in g.query(query):
        cbd = g.cbd(row[0])
        cbd.remove((None, BRICK.hasTag, None))
        # remove tags to reduce volume of output
        print(f"{row[0]}")
        print(cbd.serialize(format='json-ld'))
        print("-"* 80)


if __name__ == "__main__":
    while True:
        tags = input("Enter tags: ").split()
        find_entities(tags)
