VERSION = (0, 5, 10, 0, 'gamma-ray')


def get_version(form='short'):
    if form == 'short':
        return '.'.join([str(v) for v in VERSION[:3]])
    elif form == 'long':
        return '.'.join([str(v) for v in VERSION][:4]) + '-' + VERSION[4]
    else:
        raise ValueError('unrecognised form specifier: {0}'.format(form))


__version__ = get_version()
