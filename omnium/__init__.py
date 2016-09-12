import logging
logging.basicConfig()
# logger = logging.getLogger('omni')
from .version import __version__

from .check_config import ConfigChecker
from .setup_logging import setup_logger

from .omni_cmd import main as omni_main
# from .omnium_cmd import main as omnium_main
from .node_dag import NodeDAG
from .process_engine import ProcessEngine
from .stash import STASH
from .syncher import Syncher
