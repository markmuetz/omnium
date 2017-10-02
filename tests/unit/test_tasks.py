from unittest import TestCase
from mock import Mock, patch, mock_open

from omnium.task import Task, TaskMaster


class TestTask(TestCase):
    def test_task_chain(self):
        t0 = Task(0, 'S0', 'cycle', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
        t1 = Task(1, 'S0', 'cycle', 'analysis', 'cloud_analysis',
                  ['atmos.pp1.nc'], ['atmos.cloud_analysis.nc'])
