from mpi4py import MPI
from logging import getLogger

logger = getLogger('om.mpi_ctrl')

WORKTAG = 0
DIETAG = 1


class MpiMaster(object):
    def __init__(self, run_control, comm, rank, size):
        self.run_control = run_control
        self.comm = comm
        self.rank = rank
        self.size = size

    def run(self):
        all_tasks_iter = iter(self.run_control.task_master.get_all_tasks())
        status = MPI.Status()
        # Launch all tasks initially.
        for dest in range(1, self.size):
            task  = all_tasks_iter.next()
            data = {'command': 'run_task', 'task': task}
            logger.debug('Sending to dest {}: {}'.format(dest, data))
            self.comm.send(data, dest=dest, tag=WORKTAG)

        # Farm out rest of work when a worker reports back that it's done.
        while True:
            try:
                task  = all_tasks_iter.next()
            except StopIteration:
                logger.debug('All tasks sent')
                break
            data = self.comm.recv(source=MPI.ANY_SOURCE,
                                  tag=MPI.ANY_TAG, status=status)
            logger.debug('Data received from {}: {}'.format(status.Get_source(), data))
            data = {'command': 'run_task', 'task': task}
            logger.debug('Sending more data to {}: {}'.format(status.Get_source(), data))
            self.comm.send(data, dest=status.Get_source(), tag=WORKTAG)

        # We are done! Listen for final data responses.
        for dest in range(1, self.size):
            data = self.comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG)
            logger.debug('Final data received from {}: {}'.format(status.Get_source(), data))

        # Send all slaves a die command.
        for dest in range(1, self.size):
            data = {'command': 'die'}
            self.comm.send(data, dest=dest, tag=DIETAG)

        logger.debug('Finished')


class MpiSlave(object):
    def __init__(self, run_control, comm, rank, size):
        self.run_control = run_control
        self.comm = comm
        self.rank = rank
        self.size = size

    def listen(self):
        status = MPI.Status()
        while True:
            data = self.comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
            logger.debug('Received data: '.format(data))
            if status.Get_tag() == DIETAG:
                break
            else:
                self.run_control.run_task(data['task'])
                data['task'].status = 'done'
                self.comm.send(data, dest=0, tag=WORKTAG)

        logger.debug('Finished')
