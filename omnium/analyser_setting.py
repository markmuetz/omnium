import hashlib
from typing import Any, Dict

import simplejson


class AnalyserSetting:
    def __init__(self, settings: Dict[str, Any]=None):
        if settings:
            for key in settings.keys():
                assert isinstance(key, str)
            self._settings = settings
            # Check settings are all serializable.
            self.to_json()
        else:
            self._settings = {}

    def __getattr__(self, item: str) -> Any:
        if len(item) >= 2 and item[:2] == '__':
            return None
        return self._settings[item]

    def __eq__(self, other: 'AnalyserSetting') -> bool:
        return self.get_hash() == other.get_hash()

    def __ne__(self, other: 'AnalyserSetting') -> bool:
        return not self == other

    def has_item(self, item: str) -> bool:
        return item in self._settings

    def load(self, loc: str) -> None:
        self.from_json(open(loc, 'r').read())

    def save(self, loc) -> None:
        open(loc, 'w').write(self.to_json())

    def to_json(self) -> str:
        serializable_settings = {}
        for k, v in sorted(self._settings.items(), key=lambda x: x[0]):
            if isinstance(v, slice):
                # repr comes in handy!
                serializable_settings[k] = 'REPR:' + repr(v)
            else:
                serializable_settings[k] = v

        return simplejson.dumps(serializable_settings)

    def from_json(self, json_str: str) -> None:
        serializable_settings = simplejson.loads(json_str)
        for k, v in serializable_settings.items():
            if isinstance(v, str) and v[:5] == 'REPR:':
                serializable_settings[k] = eval(v[5:])
        self._settings = serializable_settings

    def get_hash(self) -> str:
        return hashlib.sha1(self.to_json().encode()).hexdigest()
