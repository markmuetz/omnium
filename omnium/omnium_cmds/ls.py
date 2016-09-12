"""Lists all omnis"""
import os
from glob import glob

ARGS = [(['--full-path'], {'help': 'show full path of files',
                           'action': 'store_true',
                           'default': False}),
        (['-l', '--long'], {'help': 'show more info',
                            'action': 'store_true',
                            'default': False})]


def main(args):
    user_dir = os.path.expandvars('$HOME')
    omnis_dir = os.path.join(user_dir, 'omnis')

    header = ['name', 'title', 'description']
    print_grid = [header]
    for dirname in sorted(glob(os.path.join(omnis_dir, '*'))):
        row = []
        if args.full_path:
            row.append(dirname)
        else:
            row.append(os.path.basename(dirname))

        try:
            config = ConfigObj(os.path.join(dirname, 'omni.info'))
            info = config['info']
            row.append(info['title'])
            row.append(info['description'])
        except:
            row.append('No Info')
            row.append('')
        print_grid.append(row)

    col_widths = [0] * len(header)
    for row in print_grid:
        assert(len(row) == len(header))
        for j in range(len(row)):
            col_widths[j] = max(col_widths[j], len(row[j]))

    fmts = []
    if args.long:
        col_slice = slice(None)
    else:
        col_slice = slice(0, 1)
    for i, col_width in enumerate(col_widths[col_slice]):
        fmts.append('{{{0}:{1}}}'.format(i, col_width))
    fmt = ' '.join(fmts)

    for row in print_grid:
        print(fmt.format(*row))
