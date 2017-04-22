"""Lists all omnium processes"""
import os
from glob import glob

ARGS = []


def main(args):
    user_dir = os.path.expandvars('$HOME')
    omnium_dir = os.path.join(user_dir, 'omnium')

    header = ['process_name']
    print_grid = [header, ['============']]
    for fn in sorted(glob(os.path.join(omnium_dir, '*'))):
        row = []
        row.append(os.path.basename(fn))

        print_grid.append(row)

    col_widths = [0] * len(header)
    for row in print_grid:
        assert(len(row) == len(header))
        for j in range(len(row)):
            col_widths[j] = max(col_widths[j], len(row[j]))

    fmts = []
    col_slice = slice(None)
    for i, col_width in enumerate(col_widths[col_slice]):
        fmts.append('{{{0}:{1}}}'.format(i, col_width))
    fmt = ' '.join(fmts)

    for row in print_grid:
        print(fmt.format(*row))
