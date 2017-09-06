import mpi4py
from logging import getLogger

logger = getLogger('om.mpi_ctrl')


class MpiMaster(object):
    def __init__(self, run_control):
        self.run_control = run_control
        self.comm = mpi4py.MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.my_data = []

    def run(self):
        logger.debug('running all analysis')
        for (analysis, data_type, analyser_config,
             filename_glob, enabled) in self.run_run_control.analysis_workflow.values():
            if enabled:
                logger.debug('analysis {} enabled'.format(analysis))
                self.setup_run_analyser(analysis, data_type, analyser_config, filename_glob)

    def setup_run_analyser(self, analysis, data_type, analyser_config, filename_glob):
        my_datas = []
        for expts, filenames in self.run_control.get_filenames(analysis, data_type, filename_glob):
            min_num_files_per_inst = int(len(filenames) / self.size)
            num_extra_files = len(filenames) % self.size

            start_index = min_num_files_per_inst + 1
            for i in range(1, self.size):
                if i <= num_extra_files:
                    num_files = min_num_files_per_inst + 1
                else:
                    num_files = min_num_files_per_inst
                data = {'command': 'data',
                        'analysis': analysis,
                        'expts': expts,
                        'analyser_config': analyser_config,
                        'filenames': filenames[start_index:start_index + num_files]}
                logger.debug('Sending to rank {}: {}'.format(i, data))
                self.comm.send(data, dest=i, tag=11)
                start_index += num_files

            if num_extra_files:
                data = {'command': 'data',
                        'expts': expts,
                        'analyser_config': analyser_config,
                        'filenames': filenames[0: min_num_files_per_inst + 1]}
            else:
                data = {'command': 'data',
                        'expts': expts,
                        'analyser_config': analyser_config,
                        'filenames': filenames[0: min_num_files_per_inst]}
            self.run_control._setup_run_analyser(**data)

        for i in range(1, self.size):
            data = {'command': 'start'}
            self.comm.send(data, dest=i, tag=11)

        for data in self.my_data:
            logger.debug('Running data: '.format(data))
            self.run_control._setup_run_analyser(**data)
        logger.debug('Finished')


class MpiSlave(object):
    def __init__(self, run_control):
        self.run_control = run_control
        self.comm = mpi4py.MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.my_data = []

    def listen(self):
        data = self.comm.recv(source=0, tag=11)
        if data['command'] == 'data':
            logger.debug('Received data: '.format(data))
            self.my_data.append(data)
        elif data['command'] == 'start':
            for data in self.my_data:
                logger.debug('Running data: '.format(data))
                self.run_control._setup_run_analyser(**data)
        logger.debug('Finished')
