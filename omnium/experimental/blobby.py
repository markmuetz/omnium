from collections import namedtuple

import numpy as np
import pylab as plt
import pygraphviz as pgv

import omnium as om

Blob = namedtuple('Blob', ['time_index', 'blob_index', 'from_blobs', 'to_blobs'])


def blob_str(self):
    return 'Blob(time_index={}, blob_index{}, from_blobs={}, to_blobs={})'\
           .format(self.time_index,
                   self.blob_index,
                   len(self.from_blobs),
                   len(self.to_blobs))

Blob.__repr__ = blob_str
Blob.__str__ = blob_str


def render_graph(timeseries, filename):
    G = pgv.AGraph(directed=True, rank='same', rankdir='LR')

    for blobs in timeseries:
        new_next_blobs = {}
        for b in blobs.values():
            G.add_node('{}:{}'.format(b.time_index, b.blob_index))

            if not b.time_index == 0 and not b.from_blobs:
                dummy_fmt = 'd{}:{}'
                dummy_name = dummy_fmt.format(b.blob_index, 0)
                G.add_node(dummy_name, style='invis', shape='none', width=0, height=0)

                ti = 0
                for ti in range(1, b.time_index):
                    G.add_node(dummy_fmt.format(b.blob_index, ti),
                               style='invis', shape='none', width=0, height=0)
                    G.add_edge(dummy_fmt.format(b.blob_index, ti - 1),
                               dummy_fmt.format(b.blob_index, ti),
                               style='invis')
                G.add_edge(dummy_fmt.format(b.blob_index, ti),
                           '{}:{}'.format(b.time_index, b.blob_index),
                           style='invis')

            for nb in b.to_blobs:
                if nb.blob_index not in new_next_blobs:
                    new_next_blobs[nb.blob_index] = nb
                G.add_edge('{}:{}'.format(b.time_index, b.blob_index),
                           '{}:{}'.format(nb.time_index, nb.blob_index))
    G.layout('dot')
    G.draw(filename)


def create_blob_timeseries(Mqrain, thresh):
    timeseries = []
    max_blob_index, blob_array = count_blobs(Mqrain[0], 1, True)
    init_blobs = {}
    for blob_index in range(1, max_blob_index + 1):
        blob = Blob(0, blob_index, [], [])
        init_blobs[blob_index] = blob

    prev_blob_array = blob_array
    prev_blobs = init_blobs
    timeseries.append(init_blobs)
    for t_index in range(1, Mqrain.shape[0]):
        max_blob_index, blob_array = count_blobs(Mqrain[t_index], thresh, True)
        new_blobs = {}
        for prev_blob in prev_blobs.values():
            new_blob_indices = set(blob_array[prev_blob_array == prev_blob.blob_index])
            new_blob_indices -= set([0])
            for new_blob_index in new_blob_indices:
                if new_blob_index in new_blobs:
                    blob = new_blobs[new_blob_index]
                    blob.from_blobs.append(prev_blob)
                else:
                    blob = Blob(t_index, new_blob_index, [prev_blob], [])
                    new_blobs[new_blob_index] = blob

                prev_blob.to_blobs.append(blob)

        for new_blob_index in range(1, blob_array.max() + 1):
            if new_blob_index not in new_blobs:
                blob = Blob(t_index, new_blob_index, [], [])
                new_blobs[new_blob_index] = blob

        prev_blobs = new_blobs
        prev_blob_array = blob_array
        timeseries.append(new_blobs)
    return timeseries


def plot(Mqrains, thresh):
    t_index = -1
    prev_cmd = 'f'
    cmd = 'f'
    try:
        while cmd != 'q':
            if cmd in ['f', 'c']:
                t_index += 1
            elif cmd in ['b', 'cb']:
                t_index -= 1
            elif cmd[0] == 'g':
                t_index = int(cmd.split()[1])
            if t_index < 0 or t_index >= Mqrains[0].shape[0]:
                break

            for i, Mqrain in enumerate(Mqrains):
                plt.figure(i)
                plt.clf()
                plt.title('{}'.format(t_index))
                s = Mqrain[t_index]
                plt.imshow(count_blobs(s, thresh, True)[1], origin='upper', interpolation='nearest')
                plt.pause(0.01)

            if cmd[0] != 'c':
                prev_cmd = cmd
                cmd = raw_input('fbqc [{}]: '.format(prev_cmd))
            if cmd == '':
                cmd = prev_cmd
    except KeyboardInterrupt:
        pass
    plt.pause(0.01)
    raw_input('Done')


def test_indices(i, j, diagonal=False):
    indices = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
    if diagonal:
        indices += [(i-1, j-1), (i-1, j+1), (i+1, j-1), (i+1, j+1)]
    return indices


def count_blobs(twod_slice, thresh, diagonal=False, wrap=True):
    mask = twod_slice.data > thresh
    blobs = np.zeros_like(mask, dtype=np.int32)  # pylint: disable=no-member
    blob_index = 0
    for j in range(mask.shape[1]):
        for i in range(mask.shape[0]):
            if blobs[i, j]:
                continue

            if mask[i, j]:
                blob_index += 1
                blobs[i, j] = blob_index
                outers = [(i, j)]
                while outers:
                    new_outers = []
                    for ii, jj in outers:
                        for it, jt in test_indices(ii, jj, diagonal):
                            if not wrap:
                                if it < 0 or it >= mask.shape[0] or\
                                   jt < 0 or jt >= mask.shape[1]:
                                    continue
                            else:
                                it %= mask.shape[0]
                                jt %= mask.shape[1]

                            if not blobs[it, jt] and mask[it, jt]:
                                new_outers.append((it, jt))
                                blobs[it, jt] = blob_index
                    outers = new_outers

    return blob_index, blobs
