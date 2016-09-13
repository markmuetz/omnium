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
from .stash import Stash
from .syncher import Syncher
