from logging import getLogger

from mpi4py import MPI

logger = getLogger('om.mpi_ctrl')

WORKTAG = 0
DIETAG = 1


class MpiMaster(object):
    def __init__(self, run_control, comm, rank, size):
        self.run_control = run_control
        self.comm = comm
        self.rank = rank
        self.size = size
        logger.info('Initialized MPI master: {}/{}', rank, size)

    def run(self):
        task_master = self.run_control.task_master
        status = MPI.Status()
        # Launch all tasks initially.
        if self.size > len(task_master.pending_tasks):
            logger.warning('MPI size > # of pending tasks, not sure what will happen')

        waiting_dests = list(range(1, self.size)[::-1])
        # Farm out rest of work when a worker reports back that it's done.
        while True:
            try:
                task = task_master.get_next_pending()
                if not task:
                    # There are tasks with unmet dependencies.
                    waiting_dests.append(dest)
                    logger.debug('appended waiting dests: {}', waiting_dests)
            except StopIteration:
                logger.debug('All tasks sent')
                break

            need_to_block = not waiting_dests or not task
            if need_to_block:
                # Block until notified of completion.
                rdata = self.comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
                logger.info('Data received from {}', status.Get_source())
                logger.debug('data: {}', rdata)
                if rdata['command'] == 'error':
                    logger.error('Rank {} raised error', status.Get_source())
                    logger.error(rdata['msg'])
                    raise Exception('Unrecoverable error')
                received_task = rdata['task']  # reconstituted via pickle.
                task_master.update_task(received_task.index, received_task.status)

            if task:
                if waiting_dests:
                    # Clear backlog of waiting dests.
                    logger.debug('pop waiting dests: {}', waiting_dests)
                    dest = waiting_dests.pop()
                else:
                    dest = status.Get_source()

                data = {'command': 'run_task', 'task': task}
                logger.info('Sending data to {}', dest)
                logger.debug('data: {}', data)
                self.comm.send(data, dest=dest, tag=WORKTAG)

        # We are done! Listen for final data responses.
        for dest in range(1, self.size - len(waiting_dests)):
            rdata = self.comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
            if rdata['command'] == 'error':
                logger.error('Rank {} raised error', status.Get_source())
                logger.error(rdata['msg'])
                raise Exception('Unrecoverable error')
            received_task = rdata['task']  # reconstituted via pickle.
            task_master.update_task(received_task.index, received_task.status)
            logger.info('Final data received from {}', status.Get_source())
            logger.debug('data: {}', rdata)

        # Send all slaves a die command.
        for dest in range(1, self.size):
            data = {'command': 'die'}
            logger.info('Sending die to {}', dest)
            self.comm.send(data, dest=dest, tag=DIETAG)

        logger.info('Finished')


class MpiSlave(object):
    def __init__(self, run_control, comm, rank, size):
        self.run_control = run_control
        self.comm = comm
        self.rank = rank
        self.size = size
        logger.info('Initialized MPI slave: {}/{}', rank, size)

    def listen(self):
        try:
            status = MPI.Status()
            while True:
                logger.debug('Waiting for data')
                data = self.comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
                logger.debug('Received data: {}', data)
                if status.Get_tag() == DIETAG:
                    break
                else:
                    self.run_control.run_task(data['task'])
                    data['task'].status = 'done'
                    self.comm.send(data, dest=0, tag=WORKTAG)

            logger.debug('Finished')
        except Exception as e:
            logger.error(e)
            data = {'command': 'error', 'msg': e.message}
            self.comm.send(data, dest=0, tag=WORKTAG)
            return
