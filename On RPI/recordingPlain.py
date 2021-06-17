import os
import pickle
import codecs
from daqhats import mcc118, OptionFlags, HatIDs, HatError
import daqhats
import numpy
import time
import datetime
import pause
import socket

HEADERSIZE = 10
sampChan = 1000
channelList = [0, 1, 2, 3, 4, 5, 6, 7]


def send(msg_type, message, sock):
    request = {"type": msg_type, "content": message}
    msg = pickle.dumps(request)
    msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8') + msg
    sock.send(msg)


def chan_list_to_mask(chan_list):
    # type: (list[int]) -> int
    """
    Function taken from mcc118 example github. https://github.com/mccdaq/daqhats/tree/master/examples/python/mcc118


    This function returns an integer representing a channel mask to be used
    with the MCC daqhats library with all bit positions defined in the
    provided list of channels to a logic 1 and all other bit positions set
    to a logic 0.
    Args:
        chan_list (int): A list of channel numbers.
    Returns:
        int: A channel mask of all channels defined in chan_list.
    """
    chan_mask = 0

    for chan in chan_list:
        chan_mask |= 0x01 << chan

    return chan_mask


def initHat(channels):
    """
    Initializes the hat by creating channel mask and returning all important information.
    :param channels: A list containing channels to be polled.
    :return: mcc daqhat object, a channel mask created with chan_list_to_mask,option flags, number of channels being used.
    """
    mcc = mcc118(0)
    options = OptionFlags.CONTINUOUS
    channel_mask = chan_list_to_mask(channels)
    numberOfChannels = len(channels)
    return mcc, channel_mask, options, numberOfChannels


def initData(data, channels):
    """
    Populates the data array with empty arrays which are to be filled during recording.
    :param data: Data variable used for recording.
    :param channels: Array of channels
    :return: populated data array.
    """
    for channel in channels:
        data.append([])
    return data


def collectData(mcc, samplesPerChannel):
    """
    Reads the mcc cache and stores the data into an list which is returned at the end of the recording.
    :param mcc: Initialized MCC object.
    :param samplesPerChannel: Samples to record per channel
    :return: Populated data list with recording.
    """
    current = mcc.a_in_scan_read(samplesPerChannel, 5)
    if current.hardware_overrun:
        print('\n\nHardware overrun\n')

    elif current.buffer_overrun:
        print('\n\nBuffer overrun\n')

    return current.data


def main(cmd):
    """
    Combines all subprograms.
    :return:
    """
    # Initializes mcc hat and respective channels.
    channel_list = cmd['channel_list']
    mcc, channel_mask, options, c = initHat(channel_list)

    # Initialize the MCC Hat
    scanRate = (10 ** 6) / (cmd['sample_period'])
    print(f"Frequency : {scanRate}")
    sampPerChan = int(scanRate)

    pause.until(cmd['start_time'])

    # Start recording.
    start = time.time()
    mcc.a_in_scan_start(channel_mask, sampPerChan, scanRate, options)
    after_call = time.time()

    for i in range(cmd['iters']):
        yield collectData(mcc, sampPerChan)

    mcc.a_in_scan_stop()
    time.sleep(1)

    # Store stop recording time.
    end = datetime.datetime.now()
    print(f"Time of stopping: {end}")
