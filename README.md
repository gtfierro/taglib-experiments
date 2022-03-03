# TagLib

This repository contains experiments exploring how to align Brick and Project Haystack.

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

