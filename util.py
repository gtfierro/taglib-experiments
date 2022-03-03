import pandas as pd
import re


def get_haystack():
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
    return haystack
