# TagLib

This repository contains experiments exploring how to align Brick and Project Haystack.

## Feature Overview

### Generate Tag Shims

Tag shims are RDF graphs of SHACL shapes which provide bi-directional translation between Brick classes/shapes and Haystack tag sets/protos.
`simple_map.py` contains a *representative* (but painfully incomplete) mapping between Haystack 4 protos and Brick classes.
Running `make generate-tag-shims` will compile this mapping into a tag shim RDF graph, stored as `simple_map.ttl`.

The `oap`, `protos`, `automapping-stuff` and `utah` folders all contain partial work on establishing mappings between Brick classes and other Haystack tag interpretations.

### Translating Brick <--> Haystack

The file `haystack2brick.py` turns a Haystack model into a Brick model (not all the way yet):

```
$ python haystack2brick.py alpha.json
```

The contents of the produced `alpha.json.ttl` file look something like this:

```ttl
@prefix brick: <https://brickschema.org/schema/Brick#> .
@prefix tag: <https://brickschema.org/schema/BrickTag#> .

<urn:bldg#a-0005> a brick:Mixed_Air_Temperature_Sensor,
        tag:has_exactly_5_tags_condition ;
    brick:hasTag "air",
        "mixed",
        "point",
        "sensor",
        "temp" ;
    brick:isPointOf <urn:bldg#a-0001> .
<urn:bldg#a-0001> a brick:AHU,
        tag:has_exactly_8_tags_condition ;
    brick:hasTag "ahu",
        "chilledWaterCooling",
        "elec",
        "equip",
        "hotWaterHeating",
        "hvac",
        "singleDuct",
        "vavZone" .
```

---

The file `brick2haystack.py` turns a Brick model into a Haystack model (not all the way yet):

```
$ python  brick2haystack.py g36-ahu-a9.ttl
```

The contents of the produced `g36-ahu-a9.ttl.json` looks something like this:

```json
{
  "rows": [
    {
      "id": {
        "_kind": "ref",
        "val": "urn:bldg#hwvlv_ahu",
        "dis": "urn:bldg#hwvlv_ahu"
      },
      "heating": {
        "_kind": "marker"
      },
      "equip": {
        "_kind": "marker"
      },
      "valve": {
        "_kind": "marker"
      }
    },
    {
      "id": {
        "_kind": "ref",
        "val": "urn:bldg#saf1_status",
        "dis": "urn:bldg#saf1_status"
      },
      "equipRef": {
        "_kind": "ref",
        "val": "urn:bldg#saf1",
        "dis": "urn:bldg#saf1"
      }
    },
  ]
}
```

### Serve Haystack from Brick Model

We can also query Haystack from a Brick model without needing to do the full translation.
This is obviously not the full Haystack query lang, but it is a start.
Run the `client.py` script and then type in Haystack tags to get back JSON-LD snippets of the Brick model.

```
$ python client.py
> air temp
urn:bldg#mats1
[
  {
    "@id": "urn:bldg#mats1",
    "@type": [
      "https://brickschema.org/schema/Brick#Mixed_Air_Temperature_Sensor",
      "https://brickschema.org/schema/Brick#Point"
    ],
    "https://brickschema.org/schema/Brick#isPointOf": [
      {
        "@id": "urn:bldg#ahu1"
      }
    ]
  }
]
--------------------------------------------------------------------------------
urn:bldg#sats_ahu1
[
  {
    "@id": "urn:bldg#sats_ahu1",
    "@type": [
      "https://brickschema.org/schema/Brick#Supply_Air_Temperature_Sensor",
      "https://brickschema.org/schema/Brick#Discharge_Air_Temperature_Sensor",
      "https://brickschema.org/schema/Brick#Point"
    ],
    "https://brickschema.org/schema/Brick#isPointOf": [
      {
        "@id": "urn:bldg#ahu1"
      }
    ]
  }
]
```

## Implementation Notes

The goal of the technical implementation is to establish a *shared vocabulary* that can serve as the point of interoperability between Brick and Haystack.
Each term in the vocabulary is implemented as a class or shape in Brick, and as a proto in Haystack.


A Haystack proto is related to a Brick class when there is a 1-1 relationship between the two concepts.
For example, the `supply air temp sensor point` proto in Haystack is equivalent to the `brick:Supply_Air_Temperature_Sensor` class in Brick.
The `discharge hot water heat valve cmd point` proto in Haystack must be represented as multiple entities in Brick, so this would not be suitable to relate to a Brick class and must be handled as a shape.
We cover both of these cases below, starting with simple 1-1 mappings.

### Simple Mappings

To implement the 1-1 mapping between Brick classes and Haystack protos, we take as input a mapping table such as the one in `simple_map.py` and output an RDF graph (the so-called "tag shim") containing two kinds of rules for each proto-to-class mapping.

The first kind of rule (Brick to Haystack) *produces*, for each Brick entity, the tags comprising the relevant Haystack proto.

```ttl
bldg:abc a brick:Supply_Air_Temperature_Sensor ;
    # these are all inferred automatically
    brick:hasTag "air", "temp", "sensor", "supply", "point" .
```
It is a straightforward transformation to produce the Haystack-compatible serialization of the model by querying the tags for each entity\footnote{We are not yet considering how to handle `ref` tags and `value` tags but they can be incorporated into this framework.}.

The second kind of rule (Haystack to Brick) *produces* a Brick class for each entity in the graph with an appropriate set of tags:

```ttl
bldg:abc brick:hasTag "air", "temp", "sensor", "supply", "point" ;
   # this is inferred automatically
   a brick:Supply_Air_Temperature_Sensor .
```

For these rules to be executed, a Haystack model must be represented as an RDF graph.
Luckily this is looks to be very straightforward: to start, all marker tags become the objects of `brick:hasTag` relationships and all ref tags are translated to their Brick equivalents.
Once in an RDF representation, our rules can perform the actual translation work on the model.

### Complex Mappings

For cases where there is not a 1-1 relationship between a Haystack proto and a Brick class, it is necessary to figure out how the concept in one is represented in the other[^1].
The complex representation can be specified as a SHACL shape, which is a set of constraints defining what information/properties/types should be associated with an entity.a

[^1]: From initial experience, it seems that some Haystack protos will map to multiple Brick entities and not the other way around.
