import logging
# Need to make sure that this is set to log something
# before everything else starts trying to get the logger.
logging.basicConfig()  # nopep8

from .version import __version__

from .omnium_cmd import main as omnium_main
from .stash import Stash


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
    builtin = sys.modules['__builtin__'].__dict__

    config, process_classes, dag, proc_eng, stash = init()
    globals_vars = OrderedDict()
    globals_vars['stash'] = stash
    print('Adding to global namespace:')
    for key, value in globals_vars.items():
        print('  ' + key)
        builtin[key] = value
