import os
import datetime as dt
import shutil
import logging

FILE_LEVEL_NUM = 21


# Thanks: http://stackoverflow.com/a/13638084/54557
def log_file(self, filename, message=None, *args, **kwargs):
    '''Takes a timestamped copy of filename (rel to config loc or abs)'''
    if self.isEnabledFor(FILE_LEVEL_NUM):
        self._log(FILE_LEVEL_NUM, 'logging file {}'.format(filename), [], **{})

        if not os.path.exists(filename):
            self.error('file {} does not exist'.format(filename))
        fmt = '%Y%m%dT%H%M%S'
        timestamp = dt.datetime.now().strftime(fmt)

        new_filename = os.path.join(self.logging_dir, '{1}_{0}{2}'
                                    .format(timestamp, *os.path.splitext(filename)))

        self._log(FILE_LEVEL_NUM, 'Copy file from {} to {}'
                  .format(filename, new_filename), [], **{})
        shutil.copyfile(filename, new_filename)
        self._log(FILE_LEVEL_NUM, 'Message: {}'.format(message), [], **{})


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


# Thanks: # http://stackoverflow.com/a/8349076/54557
class ColourConsoleFormatter(logging.Formatter):
    '''Format messages in colour based on their level'''
    dbg_fmt = bcolors.OKBLUE + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    info_fmt = bcolors.OKGREEN + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    file_fmt = bcolors.HEADER + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    warn_fmt = bcolors.WARNING + '%(levelname)-8s' + bcolors.ENDC + ': %(message)s'
    err_fmt = (bcolors.FAIL + '%(levelname)-8s' + bcolors.ENDC + bcolors.BOLD +
               ': %(message)s' + bcolors.ENDC)

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
        elif record.levelno == FILE_LEVEL_NUM:
            self._fmt = ColourConsoleFormatter.file_fmt
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
    '''Gets a logger. Sets up root logger ('omni') if nec.'''
    cwd = os.getcwd()
    root_logger = logging.getLogger('omni')
    root_logger.propagate = False

    if getattr(root_logger, 'is_setup', False):
        # Stops log being setup for a 2nd time during ipython reload(...)
        root_logger.debug('Root logger already setup')
    else:
        logging_dir = os.path.join(cwd, 'logs', config['computer_name'])
        root_logger.logging_dir = logging_dir
        if not os.path.exists(logging_dir):
            os.makedirs(logging_dir)

        settings = config['settings']
        console_level = settings.get('console_log_level', 'info').upper()
        file_level = settings.get('file_log_level', 'debug').upper()

        file_formatter = logging.Formatter('%(asctime)s:%(name)-12s:%(levelname)-8s: %(message)s')
        fmt = '%(levelname)-8s: %(message)s'
        if not settings.get('disable_colour_log_output', False):
            console_formatter = ColourConsoleFormatter(fmt)
        else:
            console_formatter = logging.Formatter(fmt)

        logging_filename = os.path.join(logging_dir, 'omni.log')
        fileHandler = logging.FileHandler(logging_filename, mode='a')
        fileHandler.setFormatter(file_formatter)
        fileHandler.setLevel(file_level)

        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(console_formatter)
        streamHandler.setLevel(console_level)

        root_logger.setLevel(min(console_level, file_level))

        root_logger.addHandler(fileHandler)
        root_logger.addHandler(streamHandler)

        root_logger.debug('Created root logger: {0}'.format('omni.log'))

        # Add a method to (all) loggers that lets it log a file.
        logging.addLevelName(FILE_LEVEL_NUM, "FILE")
        logging.Logger.log_file = log_file
        logging.FILE = FILE_LEVEL_NUM

        root_logger.is_setup = True

    return root_logger
