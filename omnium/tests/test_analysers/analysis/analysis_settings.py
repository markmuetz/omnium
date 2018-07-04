import sys
from omnium import AnalyserSetting


__version__ = (0, 0, 0, 1)
settings = AnalyserSetting(sys.modules[__name__], {})
