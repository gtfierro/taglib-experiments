from brickschema.namespaces import BRICK
from rdflib import Namespace

PROTO = Namespace("https://brickschema.org/schema/ph4protos#")

simple_mapping = {
    ('supply', 'air', 'temp', 'sensor', 'point'): BRICK.Supply_Air_Temperature_Sensor,
    ('discharge', 'air', 'temp', 'sensor', 'point'): BRICK.Discharge_Air_Temperature_Sensor,
    ('mixed', 'air', 'temp', 'sensor', 'point'): BRICK.Mixed_Air_Temperature_Sensor,
    ('zone', 'air', 'temp', 'sensor', 'point'): BRICK.Zone_Air_Temperature_Sensor,
    ('return', 'air', 'temp', 'sensor', 'point'): BRICK.Return_Air_Temperature_Sensor,
    ('supply', 'air', 'flow', 'sensor', 'point'): BRICK.Supply_Air_Flow_Sensor,
    ('co2', 'sensor', 'point'): BRICK.CO2_Sensor,
    ('dmp', 'pos', 'cmd', 'point'): BRICK.Damper_Position_Command,
    ('valve', 'cmd', 'point'): BRICK.Valve_Command,
    ('vav', 'equip'): BRICK.VAV,
    ('dmp', 'equip'): BRICK.Damper,
    ('hot', 'water', 'heat', 'valve', 'cmd', 'point'): PROTO.HotWaterHeatValveCmd,
    ('heating', 'valve', 'equip'): BRICK.Heating_Valve,

    ('ahu', 'chilledWaterCooling', 'elec', 'equip', 'hotWaterHeating', 'hvac', 'singleDuct', 'vavZone'): BRICK.AHU,
    ('equip', 'hotWaterHeating', 'hvac', 'singleDuct', 'thermostat', 'vav'): BRICK.RVAV,
}
