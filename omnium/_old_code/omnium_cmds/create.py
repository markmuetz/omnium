"""Creates new omni"""
import os
import shutil
from glob import glob
import datetime as dt
import socket
from logging import getLogger

from jinja2 import Environment, FileSystemLoader

logger = getLogger('omni')

OMNI_INFO_FILENAME = 'omni.info.tpl'
OMNI_CONF_FILENAME = 'omni_conf.py.tpl'
OMNI_COMP_FILENAME = 'computer.txt.tpl'

ARGS = [(['omniname'], {'nargs': 1,
                        'help': 'Filename of omni to create'}),
        (['--title'], {'help': 'Longer name'}),
        (['--description'], {'help': 'Useful description'})]


def main(args):
    cwd = os.getcwd()
    args.cwd = cwd

    omniname = args.omniname[0]
    user_dir = os.path.expandvars('$HOME')
    omni_dir = os.path.join(cwd, omniname)

    if os.path.exists(omni_dir):
        msg = 'Omni dir {} already exists, please choose a different name'.format(omni_dir)
        logger.info(msg)
        return

    omni_home = os.path.dirname(os.path.realpath(__file__))
    tpl_env = Environment(
                autoescape=False,
                loader=FileSystemLoader(os.path.join(omni_home, '..', 'data', 'templates')),
                trim_blocks=False)

    info_context = {
        'title': args.title,
        'description': args.description,
        'created': dt.datetime.now().strftime('%Y%m%d_%H%M'),
        }

    conf_context = {
        'computer_name': socket.gethostname(),
        }

    comp_context = {
        'computer_name': socket.gethostname(),
        }

    os.makedirs(omni_dir)

    files_contexts = [
        (OMNI_INFO_FILENAME, info_context),
        (OMNI_CONF_FILENAME, conf_context),
        (OMNI_COMP_FILENAME, comp_context)]

    for tpl_filename, context in files_contexts:
        # PyLint gets confused by jinja2 template rendering.
        # pylint: disable=no-member
        tpl_render = tpl_env.get_template(tpl_filename).render(context)
        filename = os.path.splitext(tpl_filename)[0]  # Nip off final .tpl

        with open(os.path.join(omni_dir, filename), 'w') as outfile:
            outfile.write(tpl_render)
