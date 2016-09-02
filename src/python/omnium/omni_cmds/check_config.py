"""Perform consistency checks on config"""
from omnium.check_config import ConfigChecker

ARGS = [(['--warnings-as-errors'], {'help': 'Treat all warnings as errors',
                                    'action': 'store_true',
                                    'default': False}),
         ]

def main(args, config):
    checker = ConfigChecker(args, config, False, args.warnings_as_errors)
    warnings, errors = checker.run_checks()
    if warnings:
        print('Config Warnings:')
        for warning in warnings:
            print(warning)

    if errors:
        print('CONFIG ERRORS FOUND:')
        for error in errors:
            print(error.message)
            if error.hint:
                print(error.hint)
    else:
        print('Config OK')
