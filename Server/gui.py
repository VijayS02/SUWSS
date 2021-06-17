"""
GUI code and Main module for the server program

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import tkinter as tk
from tkinter import messagebox as mb
import tkinter.scrolledtext as st

from graph import create_graph
from threading_gui import ThreadWorker
import sys

INPUTS = ["# Clients", "Sample Period (μs)", "Iterations", "Starting Offset (s)"]
LIMITS = [(1, 10), (10, 10 ** 6), (1, 100), (2, 10)]
WORKER = ThreadWorker()
ANI = None


def get_value_validated(item) -> int:
    item = input_data[item]
    try:
        val = int(item[0].get())
        if item[1] <= val <= item[2]:
            return val
        else:
            mb.showerror("ValueError", f"Inputted Value must be between {item[1]} and {item[2]}.")
    except ValueError:
        mb.showerror("ValueError", f"{item[0].get()} is not an integer")
        raise ValueError


def conenct_to_clients():
    task = {'func': "Connect", "desired_clients": get_value_validated('# Clients'),
            'max_conns': 20}
    WORKER.add_task(task)


def record():
    global ANI
    if WORKER.get_clients() is not None:
        try:
            samps = get_value_validated('Sample Period (μs)')
            task = {'func': "Record",
                    "sampls": samps,
                    "iters": get_value_validated('Iterations'),
                    "start_offset": get_value_validated('Starting Offset (s)')}
            WORKER.add_task(task)
            ANI = create_graph(WORKER.get_clients(), samps)
        except ValueError as err:
            print(err)
    else:
        mb.showerror("Client Error", "Connect first please.")


def exit_prog():
    print("Goodbye")
    WORKER.stop()
    sys.exit()


if __name__ == "__main__":
    master = tk.Tk()
    input_data = {}
    count = 0

    for i in range(len(INPUTS)):
        tk.Label(master, text=INPUTS[i]).grid(row=i)
        input_box = tk.Entry(master)
        input_box.grid(row=i, column=1)
        input_data[INPUTS[i]] = (input_box, LIMITS[count][0], LIMITS[count][1])
        count = i

    tk.Button(master, text='Quit', command=exit_prog).grid(row=count + 2,
                                                           column=0,
                                                           sticky=tk.W,
                                                           pady=4)

    tk.Button(master, text='Connect', command=conenct_to_clients).grid(row=count + 2,
                                                                       column=1,
                                                                       sticky=tk.W,
                                                                       pady=4)

    tk.Button(master, text='Record', command=record).grid(row=count + 2,
                                                          column=2,
                                                          sticky=tk.W,
                                                          pady=4)

    text_area = st.ScrolledText(master,
                                width=30,
                                height=8,
                                font=("Times New Roman",
                                      15))

    text_area.grid(rowspan=count + 2, row=0, column=3, pady=5, padx=10)

    text_area.insert(tk.INSERT, """asdkjljaksjdhasdjkh\naskldjsalkjd""")

    text_area.configure(state='disabled')

    master.mainloop()

    tk.mainloop()
