import pickle
from brickschema.namespaces import BRICK, TAG, SH, A, OWL, RDF, RDFS
import brickschema
import rdflib
from rdflib import XSD

brick = brickschema.Graph().load_file("../../Brick.ttl")
brick.load_file("supplementary-shapes.ttl")

def is_shape(node):
    return SH["NodeShape"] in brick.objects(subject=node, predicate=RDF.type)


has_exactly_n_tags_shapes = {}


def get_id(node):
    return node.split('#')[-1]


def generate_inst_tags(brick_class, tagset):
    tagset = tuple(tagset)
    triples = []
    triples.append((brick_class, A, SH.NodeShape))
    for tag in tagset:
        rule = rdflib.BNode(f"add_{tag}_to_{get_id(brick_class)}")
        triples.append((brick_class, SH.rule, rule))
        triples.append((rule, A, SH.TripleRule))
        triples.append((rule, SH.subject, SH.this))
        triples.append((rule, SH.predicate, BRICK.hasTag))
        triples.append((rule, SH.object, rdflib.Literal(tag)))
    return triples


def generate_class_from_tags(brick_class, tagset, shacl_tag_property_shapes):
    triples = []
    shape = TAG[f"{get_id(brick_class)}-TagShape"]
    rule = rdflib.BNode(f"{get_id(brick_class)}-Tag2ClassInferenceRule")
    triples.append((shape, A, SH.NodeShape))
    triples.append((shape, SH.rule, rule))
    triples.append((rule, A, SH.TripleRule))
    triples.append((rule, SH.subject, SH.this))
    triples.append((rule, SH.predicate, A))
    triples.append((rule, SH.object, brick_class))
    for tag in tagset:
        triples.append((rule, SH.condition, shacl_tag_property_shapes[tag]))
    triples.append((shape, SH.targetClass, has_exactly_n_tags_shapes[len(tagset)]))
    return triples


# A "mapping" is a Python dictionary whos keys are either:
# - strings (point protos): '-'-delimited sets of tags
# - tuples (tag sets): an unordered set of tags
#
# The values are one of:
# - a Brick class (URIRef)
# - a list of Brick classes (URIRefs): any of these classe can be used
def generate_shapes(mapping):
    shacl_tag_property_shapes = {}
    triples = []

    decl = rdflib.BNode("decl")
    triples.append((rdflib.URIRef(TAG), SH.declare, decl))
    triples.append((decl, SH.prefix, rdflib.Literal("rdf")))
    triples.append((decl, SH.namespace, rdflib.URIRef(RDF)))

    for tagset_or_proto, brick_classes in mapping.items():
        if isinstance(tagset_or_proto, str):
            tagset = set(tagset_or_proto.split(' '))
        else:
            tagset = set(tagset_or_proto)

        if isinstance(brick_classes, rdflib.URIRef):
            brick_classes = [brick_classes]

        # define a shape for having this many tags
        if len(tagset) not in has_exactly_n_tags_shapes:
            # tag count condition
            cond = TAG[f"has_exactly_{len(tagset)}_tags_condition"]
            prop = rdflib.BNode(f"has_exactly_{len(tagset)}_tags")
            triples.append((cond, A, OWL.Class))
            triples.append((cond, A, SH.NodeShape))
            triples.append((cond, SH.property, prop))
            triples.append((prop, SH.path, BRICK.hasTag))
            triples.append((prop, SH.minCount, rdflib.Literal(len(tagset))))
            triples.append((prop, SH.maxCount, rdflib.Literal(len(tagset))))
            has_exactly_n_tags_shapes[len(tagset)] = cond

            # generate inference rule
            rule = TAG[f"has_exactly_{len(tagset)}_tags_rule"]
            body = rdflib.BNode(f"has_{len(tagset)}_tags_body")
            triples.append((rule, A, SH.NodeShape))
            triples.append((rule, SH.targetSubjectsOf, BRICK.hasTag))
            triples.append((rule, SH.rule, body))
            triples.append((rule, SH.prefixes, rdflib.URIRef(RDF)))
            triples.append((body, A, SH.TripleRule))
            triples.append((body, SH.subject, SH.this))
            triples.append((body, SH.predicate, A))
            triples.append((body, SH.object, cond))
            triples.append((body, SH.condition, cond))

        # define shapes for having each tag
        for tag in tagset:
            if tag not in shacl_tag_property_shapes:
                cond = rdflib.BNode(f"has_{tag}_condition")
                prop = rdflib.BNode(f"has_{tag}_tag")
                tagshape = rdflib.BNode(f"tagshape_{tag}")
                triples.append((cond, SH.property, prop))
                triples.append((prop, SH.path, BRICK.hasTag))
                triples.append((prop, SH.qualifiedValueShape, tagshape))
                triples.append((tagshape, SH.hasValue, rdflib.Literal(tag)))
                triples.append(
                    (prop, SH.qualifiedMinCount, rdflib.Literal(1, datatype=XSD.integer))
                )
                shacl_tag_property_shapes[tag] = cond

        # associate the tags with each Brick class
        for brick_class in brick_classes:
            for tag in tagset:
                triples.append((brick_class, BRICK.hasAssociatedTag, rdflib.Literal(tag)))
            triples.extend(generate_inst_tags(brick_class, tagset))
            triples.extend(generate_class_from_tags(brick_class, tagset, shacl_tag_property_shapes))

    return triples


# def generate_haystack_proto_map():
#     haystack_proto_map = pickle.load(open('haystack_proto_map.pkl', 'rb'))
#     G = brickschema.Graph()
#     brickschema.namespaces.bind_prefixes(G)
#     for triple in generate_shapes(haystack_proto_map):
#         G.add(triple)
#     valid, _, report = G.validate()
#     assert valid, report
#     G.serialize('haystack_proto_map.ttl', format='turtle')
# 
# 
# def generate_brick_tag_map():
#     BG = brickschema.Graph().load_file("../../Brick.ttl")
#     brick_tag_map = {}
#     for brick_class in BG.subjects(RDF.type, OWL.Class):
#         tags = set()
#         for tag in BG.objects(brick_class, BRICK.hasAssociatedTag):
#             for t in BG.objects(tag, RDFS.label):
#                 tags.add(str(t))
#         if len(tags) > 0:
#             brick_tag_map[tuple(tags)] = brick_class
#     G = brickschema.Graph()
#     brickschema.namespaces.bind_prefixes(G)
#     for triple in generate_shapes(brick_tag_map):
#         G.add(triple)
#     valid, _, report = G.validate()
#     assert valid, report
#     G.serialize('brick_tag_map.ttl', format='turtle')
# 
# def generate_oap_map():
#     from generate_oap_map import mapping as oap_mapping
#     G = brickschema.Graph()
#     brickschema.namespaces.bind_prefixes(G)
#     for triple in generate_shapes(oap_mapping):
#         G.add(triple)
#     valid, _, report = G.validate()
#     assert valid, report
#     G.serialize('oap_map.ttl', format='turtle')

def generate_simple_map():
    from simple_map import simple_mapping
    G = brickschema.Graph()
    brickschema.namespaces.bind_prefixes(G)
    for triple in generate_shapes(simple_mapping):
        G.add(triple)
    valid, _, report = G.validate()
    assert valid, report
    G.serialize('simple_map.ttl', format='turtle')

# generate_haystack_proto_map()
# generate_brick_tag_map()
# generate_oap_map()
generate_simple_map()
