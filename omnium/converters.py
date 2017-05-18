import os
import re
import abc

import iris


class Converter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, overwrite=False, delete=False, allow_non_ppX=False):
        self.overwrite = overwrite
        self.delete = delete
        self.allow_non_ppX = allow_non_ppX

    @abc.abstractmethod
    def converted_filename(self):
        return

    @abc.abstractmethod
    def convert(self):
        return


class FF2NC(Converter):
    name = 'ff2nc'

    def converted_filename(self, old_filename):
        # e.g. atmos.000.pp3 => atmos.000.pp3.nc
        # Who knows why they give a fields file the extension pp??
        dirname = os.path.dirname(old_filename)
        filename = os.path.basename(old_filename)
        if not self.allow_non_ppX and not re.match('pp\d', filename[-3:]):
            raise Exception('Unrecognized filename {}'.format(filename))

        newname = filename + '.nc'
        return os.path.join(dirname, newname)

    def convert(self, filename):
        self.messages = ['archer_analysis convert ' + self.name]
        converted_filename = self.converted_filename(filename)
        print('Convert: {} -> {}'.format(filename, converted_filename))

        if os.path.exists(converted_filename):
            if self.overwrite:
                self.messages.append('Deleting: {}'.format(converted_filename))
                os.remove(converted_filename)
            else:
                print('Already converted')
                return converted_filename

        self.messages.append('Using iris to convert')
        self.messages.append('Original filename: {}'.format(filename))
        self.messages.append('New filename: {}'.format(converted_filename))

        cubes = iris.load(filename)
        iris.save(cubes, converted_filename)

        if self.delete:
            print('Delete: {}'.format(filename))
            os.remove(filename)
            self.messages.append('Deleted original')

        with open(converted_filename + '.done', 'w') as f:
            f.write('\n'.join(self.messages))
            f.write('\n')

        return converted_filename


CONVERTERS = {
    FF2NC.name: FF2NC,
}
