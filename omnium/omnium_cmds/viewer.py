import sys

ARGS = [(['filenames'], {'nargs': '+'}),
        (['--state'], {'nargs': '?', 'default': None}),
        (['--ignore-prev-settings'], {'action': 'store_true', 'default': False})]

def main(args):
    # I can't figure out how to embed a python shell with pylab/matplotlib enabled.
    # as in 
    # In [1]: %matplotlib
    # See:
    # http://stackoverflow.com/questions/33127785/embed-ipython-with-pylab-enabled
    # http://stackoverflow.com/questions/27911570/can-you-specify-a-command-to-run-after-you-embed-into-ipython
    # for some ideas.
    import IPython
    import traitlets.config
    from omnium.v2 import CubeListViewer

    filenames = args.filenames
    use_prev_settings = not args.ignore_prev_settings
    viewer = CubeListViewer()
    viewer.load(filenames)
    config = traitlets.config.Config()
    config.InteractiveShellApp.exec_lines = [
            'get_ipython().magic(u"gui qt")',
            ]
    # N.B. keep access to e.g. viewer
    #IPython.start_ipython(config=config)
    # This is better because it allows you to access viewer
    # N.B. not running exec_lines :(.
    IPython.embed(banner1='*'*80 + '\nviewer.help()\n%gui qt', config=config)

