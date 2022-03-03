import json
import sys
from rdflib import Namespace, Literal, URIRef
import brickschema
from brickschema.namespaces import BRICK, RDF

IGNORE_TAGS = ["cur", "his"]

BLDG = Namespace("urn:bldg#")

ph = brickschema.GraphCollection()
ph.load_graph("simple_map.ttl", graph_name=URIRef("urn:tagmap#"))
ph.load_graph("Brick.ttl")

model = ph.get_context(BLDG)
filename = sys.argv[1]
phmodel = json.load(open(filename))['rows']
for ent in phmodel:
    phent = BLDG[ent['id']['val']]
    for tag, defn in ent.items():
        if tag in IGNORE_TAGS:
            continue
        if isinstance(defn, dict) and defn.get('_kind') == "marker":
            print(f"tag for {phent} is {tag}")
            model.add((phent, BRICK.hasTag, Literal(tag)))

        if tag == "equipRef" and "point" in ent.keys():
            print(f"equipRef for {phent} is {defn['val']}")
            model.add((phent, BRICK.isPointOf, BLDG[defn['val']]))

model.serialize('/tmp/out.ttl', format='turtle')
ph.expand("shacl")

res = ph.query("SELECT DISTINCT ?ent WHERE { ?ent rdf:type/rdfs:subClassOf* brick:Entity . FILTER NOT EXISTS { ?ent rdf:type/rdfs:subClassOf* brick:Measurable } }")
brickified = brickschema.Graph()
for row in res:
    if row[0] not in model.all_nodes():
        continue
    brickified += ph.cbd(row[0])

print(brickified.serialize(format="json-ld"))
brickified.serialize(f"{filename}.ttl", format="turtle")
