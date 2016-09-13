import os
import re

from omnium.processes import Process


class CopyFileProcess(Process):
    name = 'copy_file'
    out_ext = 'txt'

    @staticmethod
    def convert_filename(filename):
        # e.g. atmos.000.pp3 => atmos.000.3.nc
        filename = os.path.basename(filename)
        if not re.match('txt', filename[-3:]):
            raise Exception('Unrecognized filename {}'.format(filename))

        pre, ext = os.path.splitext(filename)

        return pre + '.copy.' + CopyFileProcess.out_ext

    def load_upstream(self):
        super(CopyFileProcess, self).load_upstream()
        from_node = self.node.from_nodes[0]
        self.data = open(from_node.filename(self.config), 'r').read()

        return self.data

    def run(self):
        self.processed_data = self.data

    def save(self):
        super(CopyFileProcess, self).save()
        filename = self.node.filename(self.config)
        open(filename, 'w').write(self.data)
        self.saved = True
        return filename


class TextReplaceProcess(Process):
    name = 'text_replace'
    out_ext = 'txt'

    def load_upstream(self):
        super(TextReplaceProcess, self).load_upstream()
        from_node = self.node.from_nodes[0]
        lines = open(from_node.filename(self.config), 'r').readlines()
        self.data = lines
        return self.data

    def run(self):
        super(TextReplaceProcess, self).run()
        outlines = []
        for line in self.data:
            outlines.append(line.replace('r', 'a'))
        self.processed_data = ''.join(outlines)

    def save(self):
        super(TextReplaceProcess, self).save()
        filename = self.node.filename(self.config)
        open(filename, 'w').write(self.processed_data)
        self.saved = True
        return filename


class TextCombineProcess(Process):
    name = 'text_combine'
    out_ext = 'txt'

    def load_upstream(self):
        super(TextCombineProcess, self).load_upstream()
        from_node = self.node.from_nodes[0]
        self.data = []
        for from_node in self.node.from_nodes:
            self.data.extend(open(from_node.filename(self.config), 'r').readlines())
        return self.data

    def run(self):
        self.processed_data = self.data

    def save(self):
        super(TextCombineProcess, self).save()
        filename = self.node.filename(self.config)
        open(filename, 'w').write(''.join(self.data))
        self.saved = True
        return filename
