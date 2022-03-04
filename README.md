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

#### Brick-to-Haystack Rules

The first kind of rule *produces*, for each Brick entity, the tags comprising the relevant Haystack proto.

This is implemented by having the Brick class be the *target* of the SHACL shape, and then adding to that shape a set of rules which add the corresponding tags to the entity.

```ttl
brick:Supply_Air_Temperature_Sensor a sh:NodeShape ;
    sh:rule [ a sh:TripleRule ;
            sh:object "air" ;
            sh:predicate brick:hasTag ;
            sh:subject sh:this ],
        [ a sh:TripleRule ;
            sh:object "point" ;
            sh:predicate brick:hasTag ;
            sh:subject sh:this ],
        [ a sh:TripleRule ;
            sh:object "sensor" ;
            sh:predicate brick:hasTag ;
            sh:subject sh:this ],
        [ a sh:TripleRule ;
            sh:object "supply" ;
            sh:predicate brick:hasTag ;
            sh:subject sh:this ],
        [ a sh:TripleRule ;
            sh:object "temp" ;
            sh:predicate brick:hasTag ;
            sh:subject sh:this ] ;
.
```

Here, we also take advantage of the fact that the Brick ontology defines the `owl:Class` portion, so we jsut have to define the `sh:NodeShape` portion.
If an `owl:Class` is also an `sh:NodeShape`, then all *instances* of that class are automatically the target of the `sh:NodeShape`.

One the rule is executed, is a straightforward transformation to produce the Haystack-compatible serialization of the resulting model.
This can be by querying the tags for each entity[^1] and assembling the resulting JSON (see `brick2haystack.py`).

[^1]: We are not yet considering how to handle `ref` tags and `value` tags but they can be incorporated into this framework.

#### Example

Taking as input the graph:

```ttl
bldg:abc a brick:Supply_Air_Temperature_Sensor .
```

the rule above produces the following graph:

```ttl
bldg:abc a brick:Supply_Air_Temperature_Sensor ;
    # these are all inferred automatically
    brick:hasTag "air", "temp", "sensor", "supply", "point" .
```

#### Haystack-to-Brick Rules

The second kind of rule  *produces* a Brick class for each entity in the graph with an appropriate set of tags.

The intuitive approach to implementation is to have a SHACL shape check each entity in a graph if it has all of the required tags to be considered an "instance" of one of the Haystack protos.
We have to be careful here: it is not enough to just have all the required tags; the entity must also have **only** the required tags and no more[^2].

We use a single rule comprising one condition for each of the required tags.
The output of the rule is a triple declaring the entity an instance of the corresponding Brick class.


```ttl
tag:Supply_Air_Temperature_Sensor-TagShape a sh:NodeShape ;
    sh:rule [ a sh:TripleRule ;
            sh:condition _:has_air_condition,
                _:has_point_condition,
                _:has_sensor_condition,
                _:has_supply_condition,
                _:has_temp_condition ;
            sh:object brick:Supply_Air_Temperature_Sensor ;
            sh:predicate rdf:type ;
            sh:subject sh:this ] ;
    sh:targetClass tag:has_exactly_5_tags_condition .
```

The target of the rule matches only entities which have exactly the number of tags as conditions in the rule.
This is more efficient and semantically equivalent to targeting *every* entity in the graph and including the tag count shape as one of the rule conditions.

Each of the tag conditions looks something like:

```ttl
_:has_temp_tag sh:path brick:hasTag ;
    sh:qualifiedMinCount 1 ;
    sh:qualifiedValueShape [ sh:hasValue "temp" ] .
```

The tag count shapes look something like

```ttl
tag:has_exactly_2_tags_rule a sh:NodeShape ;
    sh:prefixes rdf: ;
    sh:rule [ a sh:TripleRule ;
            sh:condition tag:has_exactly_2_tags_condition ;
            sh:object tag:has_exactly_2_tags_condition ;
            sh:predicate rdf:type ;
            sh:subject sh:this ] ;
    sh:targetSubjectsOf brick:hasTag .

tag:has_exactly_2_tags_condition a owl:Class,
        sh:NodeShape ;
    sh:property [ sh:maxCount 2 ;
            sh:minCount 2 ;
            sh:path brick:hasTag ] .
```

This takes advantage of a "hack" which asserts entities to be "instances" of the shapes whose conditions they fulfill.

For these rules to be executed, a Haystack model must be represented as an RDF graph.
Luckily this is looks to be very straightforward: to start, all marker tags become the objects of `brick:hasTag` relationships and all ref tags are translated to their Brick equivalents.

[^2]: See Chapter 4 (specifically section 4.3 and 4.4) of  [my thesis](https://home.gtf.fyi/papers/fierro-dissertation.pdf) for an explanation as to "why". Essentially, due to tags like "min" and "max", the "subclass" hierarchy for protos is not equivalent to the lattice defined by a strict subset relationship between tagsets.

#### Example

Taking as input the graph:

```ttl
bldg:abc brick:hasTag "air", "temp", "sensor", "supply", "point" .
```

the rule above produces the following graph:

```ttl
bldg:abc brick:hasTag "air", "temp", "sensor", "supply", "point" ;
   # this is inferred automatically
   a brick:Supply_Air_Temperature_Sensor .
```

Once in an RDF representation, our rules can perform the actual translation work on the model.

### Complex Mappings

For cases where there is not a 1-1 relationship between a Haystack proto and a Brick class, it is necessary to figure out how the concept in one is represented in the other[^3].
The complex representation can be specified as a SHACL shape, which is a set of constraints defining what information/properties/types should be associated with an entity.a

[^3]: From initial experience, it seems that some Haystack protos will map to multiple Brick entities and not the other way around.
