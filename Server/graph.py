"""
Graphing module for the realtime data collection

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import logging
import matplotlib

from Client import Client
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.lines

from custom_deque import GraphDeque

logger = logging.getLogger(__name__)

LENGTH = 5
ITEMS_PER_UPDATE = 50000
PLUS_MINUS = 5000


def update(i: int, clients: list[Client], storage: list[GraphDeque],
           lines: list[matplotlib.lines.Line2D]):
    """
    Animation function for the graph. BLIT has to be true to truly make use of only updating the
    content of the graph.
    Args:
        i: iteration, auto passed in from the funcAnimation
        clients: clients to read data from
        storage: history data to allow a moving plot
        lines: lines to change data of
    """
    for client, store, line in zip(clients, storage, lines):
        if not client.graph_queue.empty():
            logger.debug(f"Updating graph, i: {i}, client: {client}")
            print("Update", client)
            store.add(client.graph_queue.get())
            line.set_ydata(store.convert_to_list())
    return lines


def create_graph(clients: list[Client], sample_period: int):
    """
    Create a graph with animation that updates from client objects.
    Args:
        clients: Client objects to update from (Using graph_queue)
        sample_period: the sample period of the current recording.
    """
    logger.debug(f"Graph being created... clients: {clients}, sample_period: {sample_period}")
    ipu = int(10 ** 6 / sample_period)
    fig = plt.figure()
    axes = fig.add_subplot(1, 1, 1)
    lines = []
    storage = []
    for client in clients:
        tmp = GraphDeque(ipu, LENGTH)
        storage.append(tmp)
        lines.append(axes.plot(tmp.convert_to_list(), label=client)[0])
    axes.set(ylim=(-0.5, 3))
    ani = animation.FuncAnimation(fig, update, fargs=(clients, storage, lines),
                                  interval=0, blit=True)

    plt.legend()
    plt.show()
    return ani
