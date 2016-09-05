from __future__ import print_function


def pprint(d, indent=0, level=0, indentation=2):
    indent_str = ' '*indentation
    for key, value in d.iteritems():
        if isinstance(value, dict):
            print(indent_str * indent + str(key) + ': {')
            pprint(value, indent+1, level+1)
            print(indent_str * indent + '}')
        else:
            kv = '{}: {},'.format(key, value)
            print(indent_str * (indent) + kv)
