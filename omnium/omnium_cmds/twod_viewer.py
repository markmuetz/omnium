import sys

ARGS = [(['filenames'], {'nargs': '+'})]

def main(args):
    import IPython
    from omnium.experimental.twod_cube_viewer import TwodCubeViewer

    filename = args.filenames[0]
    tcv = TwodCubeViewer()
    tcv.load(filename)
    # IPython.start_ipython(argv=[])
    # This is better because it allows you to access tcv
    print('Remember to %matplotlib!!!')
    IPython.embed()
