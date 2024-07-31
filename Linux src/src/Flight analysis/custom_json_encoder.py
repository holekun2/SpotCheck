# custom_json_encoder.py
import json
from flight_models import *

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, OrbitType):
            return obj.value
        return super().default(obj)