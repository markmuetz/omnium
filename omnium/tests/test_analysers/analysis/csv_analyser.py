import csv

from omnium.analysis import Analyser


class CsvAnalyser(Analyser):
    analysis_name = 'csv_analysis'
    single_file = True
    input_dir = 'share/data/history/{expt}'
    input_filename = '{input_dir}/atmos.000.pp1.csv'
    output_dir = 'share/data/history/{expt}'
    output_filenames = ['{output_dir}/atmos.000.pp1.csv.out']

    def load(self):
        with open(self.task.filenames[0], 'r') as f:
            reader = csv.reader(f)
            lines = [l for l in reader]
        self.header = lines[0]
        self.data = lines[1:]

    def run(self):
        self.new_data = []
        for data_line in self.data:
            print(data_line)
            new_data_line = [5 * v for v in map(float, data_line)]
            self.new_data.append(new_data_line)

    def save(self, state, suite):
        with open(self.task.output_filenames[0], 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(self.header)
            for data_line in self.new_data:
                writer.writerow(data_line)
