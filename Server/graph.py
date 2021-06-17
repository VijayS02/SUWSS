import time

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from custom_deque import Graph_Deque


LENGTH = 5
ITEMS_PER_UPDATE = 50000
PLUS_MINUS = 5000


def update(i, clients, storage, lines):
    for client, store, line in zip(clients, storage, lines):
        if not client.graph_queue.empty():
            print("Update", client)
            store.add(client.graph_queue.get())
            line.set_ydata(store.convert_to_list())
    return lines


def create_graph(clients, sample_period):
    ipu = int(10 ** 6 / sample_period)
    fig = plt.figure()
    axes = fig.add_subplot(1, 1, 1)
    lines = []
    storage = []
    for client in clients:
        tmp = Graph_Deque(ipu, LENGTH)
        storage.append(tmp)
        lines.append(axes.plot(tmp.convert_to_list(), label=client)[0])
    axes.set(ylim=(-0.5, 3))
    ani = animation.FuncAnimation(fig, update, fargs=(clients, storage, lines),
                                  interval=0, blit=True)

    plt.legend()
    plt.show()

    return ani


if __name__ == "__main__":
    create_graph([[1]], 10)
