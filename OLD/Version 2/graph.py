import os
import time
import numpy as np
import matplotlib.pyplot as plt

from os import listdir
from os.path import isfile, join


def get_last_n_lines(file_name, N):
    # Create an empty list to keep the track of last N lines
    list_of_lines = []
    # Open file for reading in binary mode
    with open(file_name, 'rb') as read_obj:
        # Move the cursor to the end of the file
        read_obj.seek(0, os.SEEK_END)
        # Create a buffer to keep the last read line
        buffer = bytearray()
        # Get the current position of pointer i.e eof
        pointer_location = read_obj.tell()
        # Loop till pointer reaches the top of the file
        while pointer_location >= 0:
            # Move the file pointer to the location pointed by pointer_location
            read_obj.seek(pointer_location)
            # Shift pointer location by -1
            pointer_location = pointer_location - 1
            # read that byte / character
            new_byte = read_obj.read(1)
            # If the read byte is new line character then it means one line is read
            if new_byte == b'\n':
                # Save the line in list of lines
                list_of_lines.append(buffer.decode()[::-1])
                # If the size of list reaches N, then return the reversed list
                if len(list_of_lines) == N:
                    return list(reversed(list_of_lines))
                # Reinitialize the byte array to save next line
                buffer = bytearray()
            else:
                # If last read character is not eol then add it in buffer
                buffer.extend(new_byte)
        # As file is read completely, if there is still data in buffer, then its first line.
        if len(buffer) > 0:
            list_of_lines.append(buffer.decode()[::-1])
    # return the reversed list
    return list(reversed(list_of_lines))


def get_data(file, lines):
    raw = get_last_n_lines(file, lines + 1)
    clean = [float(val.replace('\r', '')) for val in raw[0:-1]]
    return clean


if __name__ == "__main__":
    mypath = input("Enter folder to draw: \n")
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    colors = ['blue', 'red', 'green', 'brown', 'orange', 'yellow', 'aqua']
    prevy = []
    while True:
        if onlyfiles == []:
            onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
        try:
            x = 0
            for file in onlyfiles:
                y = get_data(mypath + '/' + file, 100000)
                plt.plot(y, color=colors[x])
                x += 1
            if prevy == y:
                break
            prevy = y
            plt.pause(0.5)
            plt.cla()
        except KeyboardInterrupt:
            print("bye!")
            plt.close()
            break
    plt.show()
