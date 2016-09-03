import os
import logging

# Thanks: http://stackoverflow.com/a/287944/54557
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Custom colour formatter
# Thanks go to: # http://stackoverflow.com/a/8349076/54557
class ColourConsoleFormatter(logging.Formatter):
    dbg_fmt = bcolors.OKBLUE + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    info_fmt = bcolors.OKGREEN + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    warn_fmt = bcolors.WARNING + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    err_fmt = bcolors.FAIL + '%(levelname)-8s' + bcolors.ENDC\
              + bcolors.BOLD +  ': %(message)s' + bcolors.ENDC

    def __init__(self, fmt="%(levelno)s: %(msg)s"):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = ColourConsoleFormatter.dbg_fmt
        elif record.levelno == logging.INFO:
            self._fmt = ColourConsoleFormatter.info_fmt
        elif record.levelno == logging.WARNING:
            self._fmt = ColourConsoleFormatter.warn_fmt
        elif record.levelno == logging.ERROR:
            self._fmt = ColourConsoleFormatter.err_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result

def setup_logger(config):
    '''Gets a logger specified by name. Sets up root logger ('omni') if nec.'''
    cwd = os.getcwd()
    root_logger = logging.getLogger('omni')
    root_logger.propagate = False

    if getattr(root_logger, 'is_setup', False):
        # Stops log being setup for a 2nd time during ipython reload(...)
	root_logger.debug('Root logger already setup')
    else:
        logging_dir = os.path.join(cwd, 'logs')
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)

        settings = config['settings']
        console_level = settings.get('console_log_level', 'info').upper()
        file_level = settings.get('file_log_level', 'debug').upper()

        formatter = logging.Formatter('%(asctime)s:%(name)-12s:%(levelname)-8s: %(message)s')
        fmt = '%(levelname)-8s: %(message)s'
        if not settings.get('disable_colour_log_output', False):
            print_formatter = ColourConsoleFormatter(fmt)
        else:
            print_formatter = logging.Formatter(fmt)

        logging_filename = os.path.join(logging_dir, 'omni.log')
        fileHandler = logging.FileHandler(logging_filename, mode='a')
        fileHandler.setFormatter(formatter)
        fileHandler.setLevel(file_level)

        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(print_formatter)
        streamHandler.setLevel(console_level)

        root_logger.setLevel(min(console_level, file_level))

        root_logger.addHandler(fileHandler)
        root_logger.addHandler(streamHandler)

        root_logger.debug('Created root logger: {0}'.format('omni.log'))

        root_logger.is_setup = True

    return root_logger
