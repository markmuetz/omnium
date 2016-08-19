import os
from glob import glob

import iris


def main(args, config):
    convert_settings = config.convert
    print(convert_settings)

    if not convert_settings.convert_all:
        return

    if convert_settings.get_confirm:
	if convert_settings.delete_after_convert:
	    msg_tpl = 'Convert {} to {} and delete original? y/[n]: '
	else:
	    msg_tpl = 'Convert {} to {}? y/[n]: '
	msg = msg_tpl.format(convert_settings.convert_from, 
                             convert_settings.convert_to)
	print(msg)
	cmd = raw_input(msg)
	print(cmd)
	if cmd != 'y':
	    return

    for glob_name in config.convert_streams.options():
        stream_name = glob_name[5:]
        stream_glob = getattr(config.convert_streams, glob_name)

        full_glob = os.path.join(config.settings.work_dir, stream_glob)
        filenames = sorted(glob(full_glob))

        if not len(filenames):
            print('No files to convert for stream {}'.format(stream_name))
            print('Have you converted them already?')
            continue

        print('Convert files for {}'.format(stream_name))
        for filename in filenames:
            pre, ext = os.path.splitext(filename)
            assert(ext[:3] == convert_settings.convert_from)
            output_filename = pre + '.' + ext[-1] + convert_settings.convert_to 

	    if os.path.exists(output_filename):
		print('Exists: {}'.format(output_filename))
		continue
            print('Convert: ' + filename)
            print('to     : ' + output_filename)

            cubes = iris.load(filename)
            if len(cubes):
                iris.save(cubes, output_filename)
                if convert_settings.delete_after_convert:
                    os.remove(filename)
            else:
                print('Filename {} contains no cubes'.format(filename))


if __name__ == '__main__':
    convert_all()
