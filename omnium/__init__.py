import logging
# Need to make sure that this is set to log something
# before everything else starts trying to get the logger.
logging.basicConfig()  # nopep8

from .version import VERSION
from .stash import Stash
from .analysis import Analysers, Analyser, AnalyserSetting, FF2NC_Converter
from .run_control import RunControl, TaskMaster, Task
from .suite import Suite, ExptList, Expt
from .omnium_errors import OmniumError
from .state import State
from .syncher import Syncher
from .omnium_cmd import main as omnium_main
import omnium.analysis
import omnium.run_control
import omnium.suite

__version__ = VERSION

__all__ = [
    Stash,
    Analysers,
    Analyser,
    AnalyserSetting,
    FF2NC_Converter,
    RunControl,
    TaskMaster,
    Task,
    Suite,
    ExptList,
    Expt,
    OmniumError,
    State,
    Syncher,
    omnium_main
]


def init():
    """Useful for setting up variables in a script."""
    stash = Stash()
    return stash


def setup_ipython():
    """Injects useful variables into the global namespace. Only use interactively."""
    import sys
    from collections import OrderedDict
    import __main__ as main
    # Thanks: http://stackoverflow.com/a/2356420/54557
    # Guard to check being called interactively:
    if hasattr(main, '__file__'):
        raise Exception('Should only be used interactively')
    # Thanks: http://stackoverflow.com/a/14298025/54557
    builtins = sys.modules['builtins'].__dict__

    stash = init()
    globals_vars = OrderedDict()
    globals_vars['stash'] = stash
    print('Adding to global namespace:')
    for key, value in globals_vars.items():
        print('  ' + key)
        builtins[key] = value
