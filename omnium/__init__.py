import logging
# Need to make sure that this is set to log something
# before everything else starts trying to get the omni logger.
logging.basicConfig()  # nopep8

from .version import __version__

from .check_config import ConfigChecker
from .setup_logging import setup_logger

from .omni_cmd import main as omni_main
from .omnium_cmd import main as omnium_main
from .node_dag import NodeDAG
from .process_engine import ProcessEngine
from .processes import get_process_classes
from .stash import Stash
from .syncher import Syncher


def setup_ipython():
    '''Injects useful variables into the global namespace. Only use interactively.'''
    import sys
    from collections import OrderedDict
    import __main__ as main
    # Thanks: http://stackoverflow.com/a/2356420/54557
    # Guard to check being called interactively:
    if hasattr(main, '__file__'):
        raise Exception('Should only be used interactively')
    # Thanks: http://stackoverflow.com/a/14298025/54557
    builtin = sys.modules['__builtin__'].__dict__
    config = ConfigChecker.load_config()
    process_classes = get_process_classes()
    dag = NodeDAG(config, process_classes)
    globals_vars = OrderedDict()
    globals_vars['config'] = config
    globals_vars['process_classes'] = process_classes
    globals_vars['dag'] = dag
    globals_vars['proc_eng'] = ProcessEngine(False, config, process_classes, dag)
    globals_vars['stash'] = Stash()
    print('Adding to global namespace:')
    for key, value in globals_vars.items():
        print('  ' + key)
        builtin[key] = value
