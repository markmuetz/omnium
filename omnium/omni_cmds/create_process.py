"""Creates new processes in src/python"""
import os
from logging import getLogger
import importlib

from jinja2 import Environment, FileSystemLoader

logger = getLogger('omni')

OMNI_PROC_FILENAME = 'omni_proc.py.tpl'

ARGS = [(['process_name'], {'nargs': 1, 'help': 'Process name to create'}),
        (['--baseclass', '-b'], {'help': 'Baseclass to use',
                                 'default': 'Process'}),
        (['--out-ext'], {'help': 'Extension of process filename',
                         'nargs': '?'}),
        (['--module-names'], {'help': 'Modules for process',
                              'nargs': '*'})]


def main(args, config, process_classes):
    process_name = args.process_name[0]

    src_dir = 'src/python'
    filename = os.path.join(src_dir, process_name + '.py')

    if os.path.exists(filename):
        raise Exception('{} already exists'.format(filename))

    out_ext = args.out_ext
    if args.module_names:
        module_names = args.module_names
    else:
        module_names = []

    if args.baseclass:
        processes = importlib.import_module('omnium.processes')
        if not hasattr(processes, args.baseclass):
            logger.warn('Cannot find baseclass {}'.format(args.baseclass))

        if args.baseclass == 'IrisProcess' and not args.out_ext:
            out_ext = 'nc'
        elif args.baseclass == 'PylabProcess' and not args.out_ext:
            out_ext = 'png'

        if args.baseclass == 'IrisProcess' and not args.module_names:
            module_names = ['iris']
        elif args.baseclass == 'PylabProcess' and not args.module_names:
            module_names = ['pylab']

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            logger.warn('Cannot load module {}'.format(module_name))

    omni_home = os.path.dirname(os.path.realpath(__file__))
    tpl_env = Environment(
                autoescape=False,
                loader=FileSystemLoader(os.path.join(omni_home, '..', 'data', 'templates')),
                trim_blocks=False)

    logger.debug(args)
    process_name_capitalized = ''.join(map(str.title,
                                           process_name.split('_')))
    proc_context = {
        'process_name': process_name,
        'process_name_capitalized': process_name_capitalized,
        'baseclass': args.baseclass,
        'out_ext': out_ext,
        'module_names': module_names,
        }

    # PyLint gets confused by jinja2 template rendering.
    # pylint: disable=no-member
    proc_tpl_render = tpl_env.get_template(OMNI_PROC_FILENAME).render(proc_context)

    if not os.path.exists(src_dir):
        os.makedirs(src_dir)
    with open(filename, 'w') as outfile:
        outfile.write(proc_tpl_render)
