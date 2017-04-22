VERSION = (0, 7, 0, 0, 'alpha')


def get_version(form='short'):
    if form == 'short':
        return '.'.join([str(v) for v in VERSION[:3]])
    elif form == 'long':
        return '.'.join([str(v) for v in VERSION][:4]) + '-' + VERSION[4]
    else:
        raise ValueError('unrecognised form specifier: {0}'.format(form))


__version__ = get_version()

if __name__ == '__main__':
    print(get_version())
