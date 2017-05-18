import os
import sys

try:
    import omnium
except ImportError:
    path = os.getenv('OMNIUM_PYTHONPATH')
    print('Adding to path: {}'.format(path))
    sys.path.insert(0, path)
    import omnium

def read_args():
    data_type = sys.argv[1]
    expt = sys.argv[2]
    return data_type, expt


def main():
    from omnium.run_control import RunControl
    from setup_logging import setup_logger

    debug = os.getenv('OMNIUM_DEBUG') == 'True'
    logger = setup_logger(debug, False)
    run_control = RunControl(*read_args())
    run_control.run()


if __name__ == '__main__':
    main()
