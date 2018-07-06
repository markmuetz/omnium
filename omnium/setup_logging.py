import logging
import sys


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


class BraceMessage:
    def __init__(self, msg, *args, **kwargs):
        self.msg = str(msg)
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.msg.format(*self.args, **self.kwargs)


class BraceFormatter(logging.Formatter):
    """Allow deferred formatting of msg using {msg} syntax"""
    def format(self, record):
        # record.msg is whatever was passed into e.g. logger.debug(...).
        # record.args is:
        #     extra args, or:
        # kwargs dict:.
        record_args_orig = record.args
        record_msg_orig = record.msg
        # replace record.msg with a BraceMessage and set record.args to ()
        if isinstance(record.args, dict):
            args = []
            kwargs = record.args
        else:
            args = record.args
            kwargs = {}
        record.args = ()
        # N.B. msg has not been formatted yet. It will get formatted when
        # str(...) gets called on the BraceMessage.
        record.msg = BraceMessage(record.msg, *args, **kwargs)
        result = logging.Formatter.format(self, record)

        # Leave everything as we found it.
        record.args = record_args_orig
        record.msg = record_msg_orig

        return result


# Thanks: # http://stackoverflow.com/a/8349076/54557
class ColourConsoleFormatter(logging.Formatter):
    '''Format messages in colour based on their level'''
    dbg_fmt = bcolors.OKBLUE + '{levelname:8s}' + bcolors.ENDC + ': {message}'
    info_fmt = bcolors.OKGREEN + '{levelname:8s}' + bcolors.ENDC + ': {message}'
    file_fmt = bcolors.HEADER + '{levelname:8s}' + bcolors.ENDC + ': {message}'
    warn_fmt = bcolors.WARNING + '{levelname:8s}' + bcolors.ENDC + ': {message}'
    err_fmt = (bcolors.FAIL + '{levelname:8s}' + bcolors.ENDC + bcolors.BOLD +
               ': {message}' + bcolors.ENDC)

    def __init__(self, fmt="{levelno}: {msg}", style='{'):
        logging.Formatter.__init__(self, fmt, style=style)

    def format(self, record):

        # record.msg is whatever was passed into e.g. logger.debug(...).
        # record.args is:
        #     extra args, or:
        # kwargs dict:.

        # replace record.msg with a BraceMessage and set record.args to ()
        # import ipdb; ipdb.set_trace()
        if isinstance(record.args, dict):
            args = []
            kwargs = record.args
        else:
            args = record.args
            kwargs = {}
        record.args = ()
        record.msg = BraceMessage(record.msg, *args, **kwargs)
        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt
        # Fix colour formatting for new versions of logging.
        if hasattr(self, '_style'):
            style_format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._fmt = ColourConsoleFormatter.dbg_fmt
        elif record.levelno == logging.INFO:
            self._fmt = ColourConsoleFormatter.info_fmt
        elif record.levelno == logging.WARNING:
            self._fmt = ColourConsoleFormatter.warn_fmt
        elif record.levelno == logging.ERROR:
            self._fmt = ColourConsoleFormatter.err_fmt
        if hasattr(self, '_style'):
            self._style._fmt = self._fmt

        # Call the original formatter class to do the grunt work
        result = BraceFormatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig
        if hasattr(self, '_style'):
            self._style._fmt = style_format_orig

        return result


def add_file_logging(logging_filename, root=True):
    root_logger = logging.getLogger()

    if root and getattr(root_logger, 'has_file_logging', False):
        # Stops log being setup for a 2nd time during ipython reload(...)
        root_logger.debug('Root logger already has file logging')
    else:
        root_logger.debug('Adding file handler {}', logging_filename)
        file_formatter = BraceFormatter('{asctime}:{name:12s}:{levelname:8s}: {message}',
                                        style='{')
        fileHandler = logging.FileHandler(logging_filename, mode='a')
        fileHandler.setFormatter(file_formatter)
        fileHandler.setLevel(logging.DEBUG)

        root_logger.addHandler(fileHandler)
        if root:
            root_logger.has_file_logging = True


def remove_file_logging(logging_filename):
    root_logger = logging.getLogger()
    handlers = [h for h in root_logger.handlers
                if isinstance(h, logging.FileHandler) and h.baseFilename == logging_filename]
    assert len(handlers) == 1
    handler = handlers[0]
    root_logger.handlers.remove(handler)
    root_logger.debug('Removed file handler {}', logging_filename)


def setup_logger(debug=False, colour=True, warn_stderr=False):
    '''Gets a logger. Sets up root logger ('omnium') if nec.'''
    root_logger = logging.getLogger()
    om_logger = logging.getLogger('om')
    root_logger.propagate = False

    root_handlers = []
    while root_logger.handlers:
        # By default, the root logger has a stream handler attached.
        # Remove it. N.B any code that uses omnium should know this!
        root_handlers.append(root_logger.handlers.pop())

    if getattr(om_logger, 'is_setup', False):
        # Stops log being setup for a 2nd time during ipython reload(...)
        om_logger.debug('Root logger already setup')
    else:
        # fmt = '%(levelname)-8s: %(message)s'
        fmt = '{levelname:8s}: {message}'
        if colour:
            console_formatter = ColourConsoleFormatter(fmt, style='{')
        else:
            console_formatter = BraceFormatter(fmt, style='{')

        if debug:
            level = logging.DEBUG
        else:
            level = logging.INFO

        stdoutStreamHandler = logging.StreamHandler(sys.stdout)
        stdoutStreamHandler.setFormatter(console_formatter)
        stdoutStreamHandler.setLevel(level)

        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(stdoutStreamHandler)

        if warn_stderr:
            stderrStreamHandler = logging.StreamHandler(sys.stderr)
            stderrStreamHandler.setFormatter(BraceFormatter(fmt, style='{'))
            stderrStreamHandler.setLevel(logging.WARNING)
            root_logger.addHandler(stderrStreamHandler)

        root_logger.is_setup = True

    for hdlr in root_handlers:
        om_logger.debug('Removed root handler: {}', hdlr)

    return om_logger
