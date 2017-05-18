import os
import sys

try:
    import omnium
except ImportError:
    path = os.getenv('OMNIUM_PYTHONPATH')
    print('Adding to path: {}'.format(path))
    sys.path.insert(0, path)
    import omnium


def main():
    from omnium.run_control import RunControl
    run_control = RunControl()
    run_control.run()


if __name__ == '__main__':
    main()
