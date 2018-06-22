import copy
import hashlib
from typing import Any, Dict
from types import ModuleType

import simplejson


class AnalyserSetting:
    def __init__(self, package: ModuleType, settings: Dict[str, Any]=None):
        self.package = package
        if settings:
            for key in settings.keys():
                assert isinstance(key, str)
            self._settings = settings
            # Check settings are all serializable.
            self.to_json()
        else:
            self._settings = None

    def __getattr__(self, item: str):
        return self._settings[item]

    def load(self, loc: str) -> None:
        self.from_json(open(loc, 'r').read())

    def save(self, loc) -> None:
        open(loc, 'w').write(self.to_json())

    def to_json(self):
        serializable_settings = copy.copy(self._settings)
        for k, v in serializable_settings.items():
            if isinstance(v, slice):
                # repr comes in handy!
                serializable_settings[k] = 'REPR:' + repr(v)
        return simplejson.dumps(serializable_settings)

    def from_json(self, json_str: str) -> None:
        serializable_settings = simplejson.loads(json_str)
        for k, v in serializable_settings.items():
            if isinstance(v, str) and v[:5] == 'REPR:':
                serializable_settings[k] = eval(v[5:])
        self._settings = serializable_settings

    def get_hash(self) -> str:
        return hashlib.sha1(self.to_json().encode()).hexdigest()
