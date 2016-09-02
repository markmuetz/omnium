"""Creates new omni"""
import os
import shutil
from glob import glob
import datetime as dt
import socket

from jinja2 import Environment, FileSystemLoader

OMNI_INFO_FILENAME = 'omni.info'
OMNI_CONF_FILENAME = 'omni_conf.py'
OMNI_COMP_FILENAME = 'computer.txt'

ARGS = [
        (['omniname'], {'nargs': 1,
                      'help': 'Filename of omni to create'}),
        (['--title'], {'help': 'Longer name'}),
        (['--description'], {'help': 'Useful description'}),
           ]

def main(args):
    cwd = os.getcwd()
    args.cwd = cwd

    omniname = args.omniname[0]
    user_dir = os.path.expandvars('$HOME')
    omni_dir = os.path.join(cwd, omniname)

    if os.path.exists(omni_dir):
        msg = 'Omni dir {} already exists, please choose a different name'.format(omni_dir)
        print(msg)
        return

    omni_home = os.path.expandvars('$OMNI_HOME')
    tpl_env = Environment(
                autoescape=False,
                loader=FileSystemLoader(os.path.join(omni_home, 'templates')),
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

    info_tpl_render = tpl_env.get_template(OMNI_INFO_FILENAME).render(info_context)
    conf_tpl_render = tpl_env.get_template(OMNI_CONF_FILENAME).render(conf_context)
    comp_tpl_render = tpl_env.get_template(OMNI_COMP_FILENAME).render(comp_context)

    os.makedirs(omni_dir)
    with open(os.path.join(omni_dir, OMNI_INFO_FILENAME), 'w') as f:
        f.write(info_tpl_render)

    with open(os.path.join(omni_dir, OMNI_CONF_FILENAME), 'w') as f:
        f.write(conf_tpl_render)

    with open(os.path.join(omni_dir, OMNI_COMP_FILENAME), 'w') as f:
        f.write(comp_tpl_render)
