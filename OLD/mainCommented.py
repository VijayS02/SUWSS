import ftplib
import os
import configparser
import codecs
from daqhats import mcc118, OptionFlags, HatIDs, HatError
import daqhats
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy
import threading
import time
import datetime
import pause
import queue
from dateutil.relativedelta import relativedelta

FTP_HOST = "143.89.22.92"
FTP_USER = "admin"
FTP_PASS = "gs221188"
localPath = 'Store/'
configName = 'Raspi.ini'
publicPath = '/Public/cRIO/'
sampChan = 1000
channelList = [0, 1, 2, 3, 4, 5, 6, 7]

config = configparser.ConfigParser()


def connectToFTP(host, usern, passw,verb):
    """
    Creates an FTP Connection with the given details using FTPLib.

    :param host: Hostname (e.g. IP address) of the connection
    :param usern: Username to login with
    :param passw: password
    :param verb: print errors or not.
    :return: FTP Connection object. Success:1, Failure:0
    """
    try:
        ftp = ftplib.FTP(host, usern, passw)
        ftp.encoding = "utf-8"
        ftp.set_pasv(False)
    except Exception as e:
        if verb:
            print(e)
            print("\nERROR while creating FTP Connection \n")
        return None,0
    return ftp,1


def downloadFile(ftp, remoteaddr, localaddr, filename):
    """
    Downloads a remote file via an ftp connection to the given local address.

    :param ftp: An ftp connection object.
    :param remoteaddr: Path of the remote file (Excluding the file itself)
    :param localaddr: Local path where file is to be stored. (Excluding the file itself)
    :param filename: File name including extension.
    """
    remoteFile = remoteaddr + filename
    storeFile = open(localPath + filename, 'wb')
    try:
        ftp.retrbinary(f"RETR {remoteFile}", storeFile.write)
    except Exception as e:
        print(e)
        print("\nERROR while trying to retrieve remote file.")
        return
    storeFile.close()


def updateConfig(location, filename):
    """
    Simply updates the config object.

    :param location: Local path where config file is. (Excluding the file itself)
    :param filename: Config filename and extension.
    """
    try:
        config.read(location + filename)
    except:
        print(e)
        print("\nERROR while trying to load config data.")



def configUpdateThreaed(remoteaddr, localaddr, filename, kill):
    """
    A separate thread designed solely for constantly downloading and updating the config file.
    :param remoteaddr: Path of the remote config file (Excluding the file itself)
    :param localaddr: Local path where config file is to be downloaded to. (Excluding the file itself)
    :param filename: Config File name including extension.
    :param kill: A queue which is constantly checked to see if the program is to be terminated.
    """
    print("Updating thread has been Initialized.")
    errorCount = 0
    while kill.empty():  # Constantly checks if the queue is empty.
            ftp, success = connectToFTP(FTP_HOST, FTP_USER, FTP_PASS,0)
            if success:
                downloadFile(ftp, remoteaddr, localaddr, filename)
                # Give FTP server time before checking again.
                time.sleep(0.1)
                ftp.quit()
            else:
                errorCount+=1
            if errorCount>5:
                print("There is an error while connecting to the server.")
                connectToFTP(FTP_HOST, FTP_USER, FTP_PASS, 1)
                break
    print("Updating thread has been Killed.")


def initPath(path):
    """
    Initializes a folder. (I.e. creates if it does not exist).
    :param path: Path of folder to be intialized.
    """
    if not (os.path.exists(localPath)):
        print(f"Path '{path}' does not exist. Creating path...\n")
        os.mkdir(localPath)
        print(f"Path '{path}' created.")


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


def uploadFile(ftp, remoteaddr, localaddr, filename):
    """
    Uploads a local file via an ftp connection to the given remote address.


    :param ftp: An ftp connection object.
    :param remoteaddr: Path of the remote file to be stored (Excluding the file itself)
    :param localaddr: Local path where file is (Excluding the file itself)
    :param filename: File name including extension.
    """
    remoteFile = remoteaddr + filename
    file = open(localaddr + filename, 'rb')  # file to send
    ftp.storbinary(f'STOR {remoteFile}', file)
    file.close()


def writeFile(data, startTim, numChan, file, lo):
    """
    Writes out the data into a .csv file.
    :param data: Array of data to be written out.
    :param startTim: The start time of the recording
    :param numChan: Number of channels used in the recording
    :param file: filename and extension
    :param lo: local address of file (excluding filename)
    :return: Success:1, Fail:0 (Exception occurred)
    """
    writeString = ''
    for counter in range(0, numChan):
        writeString += f"Channel {counter},"
    writeString += startTim
    writeString += "\n"
    for point in range(0, len(data[0])):
        tempWr = ''
        for counter in range(0, numChan):
            tempWr += str(data[counter][point]) + ','
        tempWr = tempWr[0:len(tempWr) - 1]
        writeString += tempWr + '\n'
    writeString = writeString[0:len(writeString) - 2]

    try:

        wrFl = open(lo + file, 'w+')
        wrFl.write(writeString)
        wrFl.close()
        return 1
    except Exception as e:
        print(e)
        print("ERROR while trying to write out file.")
        return 0



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


def collectData(mcc, samplesPerChannel, data, channels):
    """
    Reads the mcc cache and stores the data into an list which is returned at the end of the recording.
    :param mcc: Initialized MCC object.
    :param samplesPerChannel: Samples to record per channel
    :param data: Data List
    :param channels: List of channels
    :return: Populated data list with recording.
    """
    current = mcc.a_in_scan_read(samplesPerChannel, 5)
    if current.hardware_overrun:
        print('\n\nHardware overrun\n')

    elif current.buffer_overrun:
        print('\n\nBuffer overrun\n')

    current = current.data
    for i in range(0, samplesPerChannel):
        for channel in channels:
            if not (len(current) == len(channels) * samplesPerChannel):
                print("ERROR Length does not match the given samples per channel.")
            try:
                data[channel].append(current[channel])
            except Exception as e:
                print(e)
                print("\nERROR While trying to store data.")
    return data


def main():
    """
    Combines all subprograms.
    :return:
    """

    # Tests ftp connection.
    ftp,success = connectToFTP(FTP_HOST, FTP_USER, FTP_PASS,1)
    if not success:
        return

    # Creates a queue that will end all other threads when necessary.
    killThread = queue.Queue()

    # Initializes the local path
    initPath(localPath)

    # Starts the updating thread that will constantly poll the config file on the server
    checker = threading.Thread(target=configUpdateThreaed, args=(publicPath, localPath, configName, killThread,))
    checker.daemon = True
    checker.start()

    # Creates the list which is going to be used to store recording data
    dat = []
    initData(dat, channelList)

    # Initializes mcc hat and respective channels.
    mcc, channel_mask, options, c = initHat(channelList)

    # This time.sleep allows the updating thread to download a config file in case there is not one already.
    time.sleep(1)

    # Updates the config object from file.
    updateConfig(localPath, configName)
    print("\n\nWaiting...")

    start = False
    errors =0
    while not start:
        updateConfig(localPath, configName)
        try:
            if config['RAS']['Start'] == 'TRUE':
                start = True
        except:
            pass

    print("Config file received!")

    # Sets the start recording time and adjusts according to labview formatting.
    timeM = datetime.datetime.fromtimestamp(float(config['RAS']['Start Time']) / (10 ** 9))
    year1 = relativedelta(years=10, days=4, months=0)
    final = timeM + year1
    print(f"\nWaiting until: {final}")
    # Waits until it is time to record
    pause.until(final)

    start = datetime.datetime.now()
    print("STARTING RECORDING NOW")
    print(f"Time of Starting: {start}")

    # Initialize scan rate and start recording.
    scanRate = (10 ** 6) / (int(config['RAS']['Sample Period']))
    print(f"Frequency : {scanRate}")
    sampPerChan = int(scanRate / 10)
    mcc.a_in_scan_start(channel_mask, sampPerChan, scanRate, options)

    # Wait until stop recording command is sent.
    while config['RAS']['Start'] == 'TRUE':
        updateConfig(localPath, configName)
        dat = collectData(mcc, sampPerChan, dat, channelList)

    mcc.a_in_scan_stop()

    # Store stop recording time.
    end = datetime.datetime.now()
    print(f"Time of stopping: {end}")
    print(f"Diff: {end - start}")

    # Write out data to file.
    success = writeFile(dat, str(start), len(channelList), 'Data0.csv', localPath)
    if not success:
        return

    # Print number of samples
    print(f"Number of samples: {len(dat[0])}")

    # Send kill command
    killThread.put("end")
    checker.join()
    try:
        ftp, success = connectToFTP(FTP_HOST, FTP_USER, FTP_PASS,1)
        if success:
            uploadFile(ftp, publicPath, localPath, 'Data0.csv')
            ftp.close()
    except Exception as error:
        print("ERROR while uploading")
        print(error)
        print("\n\n")


while True:
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n\nKeyboard interrupt detected. Ending program.")
        break
    except Exception as e:
        print(e)
