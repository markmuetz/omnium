import copy
import hashlib

import simplejson


class AnalyserSetting:
    def __init__(self, settings=None):
        if settings:
            for key in settings.keys():
                assert isinstance(key, str)
            self._settings = settings
            # Check settings are all serializable.
            self.to_json()
        else:
            self._settings = None

    def __getattr__(self, item):
        return self._settings[item]

    def load(self, loc):
        self.from_json(open(loc, 'r').read())

    def save(self, loc):
        open(loc, 'w').write(self.to_json())

    def to_json(self):
        serializable_settings = copy.copy(self._settings)
        for k, v in serializable_settings.items():
            if isinstance(v, slice):
                serializable_settings[k] = 'REPR:' + repr(v)
        return simplejson.dumps(serializable_settings)

    def from_json(self, json_str):
        serializable_settings = simplejson.loads(json_str)
        for k, v in serializable_settings.items():
            if isinstance(v, str) and v[:5] == 'REPR:':
                serializable_settings[k] = eval(v[5:])
        self._settings = serializable_settings

    def get_hash(self):
        return hashlib.sha1(self.to_json().encode()).hexdigest()
