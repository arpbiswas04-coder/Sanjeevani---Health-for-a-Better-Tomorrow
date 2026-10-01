"""Public routing metadata only. A registry does not grant node authentication."""
import json
from pathlib import Path
import re
from optimization.common.validation import ValidationError, object_fields


def validate(value):
    value = object_fields(value, required={'nodes'}, optional=set(), path='registry')
    if not isinstance(value['nodes'], list) or not 2 <= len(value['nodes']) <= 100:
        raise ValidationError('Registry requires 2..100 nodes')
    result = {}
    for node in value['nodes']:
        node = object_fields(node, required={'node_id','region','country'}, optional=set(), path='node')
        for key in ('node_id','region'):
            if not isinstance(node[key],str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',node[key]):
                raise ValidationError('Invalid registry identifier')
        if not isinstance(node['country'],str) or not re.fullmatch('[A-Z]{2}',node['country']):
            raise ValidationError('Country must be a two-letter code')
        if node['node_id'] in result:
            raise ValidationError('Duplicate node identity')
        result[node['node_id']] = dict(node)
    return result


def load(path):
    with Path(path).open('rb') as source:
        raw = source.read(65537)
    if len(raw)>65536:
        raise ValidationError('Registry exceeds size bound')
    return validate(json.loads(raw))
