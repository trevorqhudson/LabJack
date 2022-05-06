"""
Demonstrates usage of the periodic stream-out functions.

Streams out arbitrary values. These arbitrary values act on DAC0 to cyclically
increase the voltage from 0 to 2.5.

Relevant Documentation:

LJM Library:
    LJM Library Installer:
        https://labjack.com/support/software/installers/ljm
    LJM Users Guide:
        https://labjack.com/support/software/api/ljm
    Opening and Closing:
        https://labjack.com/support/software/api/ljm/function-reference/opening-and-closing
    LJM Single Value Functions (like eReadName, eReadAddress):
        https://labjack.com/support/software/api/ljm/function-reference/single-value-functions
    Stream Functions (eStreamRead, eStreamStart, etc.):
        https://labjack.com/support/software/api/ljm/function-reference/stream-functions

T-Series and I/O:
    Modbus Map:
        https://labjack.com/support/software/api/modbus/modbus-map
    Stream Mode:
        https://labjack.com/support/datasheets/t-series/communication/stream-mode
    Stream-Out:
        https://labjack.com/support/datasheets/t-series/communication/stream-mode/stream-out
    Digital I/O:
        https://labjack.com/support/datasheets/t-series/digital-io
    DAC:
        https://labjack.com/support/datasheets/t-series/dac

"""
import sys
import os
import math
import csv
import pandas as pd
import numpy as np
from datetime import datetime
from time import sleep

from labjack import ljm
from labjack import ljm_stream_util


def main():
    scanRate = 10000  
    scansPerRead = int(scanRate / 2)   #scans per packet
    runTime = 3  # Number of seconds to stream out waveforms
    

    
    # output set up
    outChannels = ["STREAM_OUT0"]  # Up to 4 out-streams can be ran at once
    scanList = ljm.namesToAddresses(len(outChannels), outChannels)[0]
    targetAddr = 1000 # Only stream out to DAC0
    streamOutIndex = 0  # Stream out index can only be a number between 0-3
    
    samplesToWrite = 500  #controls output waveform resolution/frequency along with scanRate
    # outputfreq = scanRate/samplesToWrite
    
    # sine wave out
    writeData = []
    
    amp = 1
    offset = 2.5
    
    for i in range(samplesToWrite):
        sample = amp*math.sin(i*2*math.pi/samplesToWrite) + offset
        writeData.append(sample)
        
    # input set up
    inChannels = ["AIN0", "AIN3", "AIN2", "AIN1"]
    numInChannels = len(inChannels)
    outScanList = ljm.namesToAddresses(numInChannels, inChannels)[0]
    
    scanList = outScanList + scanList
    
    #timing
    appStartTime = datetime.now()
    # startTimeStr = appStartTime.isoformat(timespec='milliseconds')
    startTimeStr = appStartTime.strftime("%Y/%m/%d %I:%M:%S%p")
    timeStr = appStartTime.strftime("%Y_%m_%d-%I_%M_%S%p")
    
    #LabJack timing
    
    
    #file i/o
    cwd = 'C:\\Users\\Health Lab\\Documents\\Trevor\\LJ Data\\Python Data'
    
    fileName = timeStr + "-%s-Example.csv"%(inChannels)
    filePath = os.path.join(cwd, fileName)

    # Open the file & write a header-line
    # f = open(filePath, 'w', newline='')
    # f.write("Time Stamp, Duration/Jitter (ms), %s" %(inChannels))
    

    print("Beginning...\n")
    handle = openLJMDevice(ljm.constants.dtANY, ljm.constants.ctANY, "ANY")
    printDeviceInfo(handle)

    try :
        print("\nInitializing stream out... \n")
        ljm.periodicStreamOut(handle, streamOutIndex, targetAddr, scanRate, len(writeData), writeData)
        actualScanRate = ljm.eStreamStart(handle, scansPerRead, len(scanList), scanList, scanRate)
        print("Stream started with commanded scan rate of %f Hz (actual %f Hz)\n Running for %d seconds\n" % (scanRate, actualScanRate, runTime))
        
        data = []
        myTime = []
        
        start_time = ljm.getHostTick()
        time_delta = ljm.getHostTick() - start_time
        while time_delta < (runTime*10**6):
            print(time_delta)
            ret = ljm.eStreamRead(handle)
            time_delta = ljm.getHostTick() - start_time
            myTime.append(time_delta)
            data.extend(ret[0][0:(scansPerRead * numInChannels)])
        
        itercount = 0
        
        #preallocate un-interleaved data array
        numRows = int(len(data)/numInChannels) + 1
        numColumns = numInChannels
        output = np.zeros((numRows, numColumns))
        
        print(len(data))
        print(np.shape(output))
        
        for i in range(len(data)):
            for chan in range(numInChannels):
                if i%numInChannels == chan:
                    output[itercount][chan] = data[i]
                if i%numInChannels == 0:
                    itercount += 1
                    break
            
        
        df = pd.DataFrame(output)
        
        
        with open(filePath, 'w') as f:
            f.write('Test comment')
        df.to_csv(filePath, mode='a')
        
        
    except ljm.LJMError:
        ljm_stream_util.prepareForExit(handle)
        raise
    except Exception:
        ljm_stream_util.prepareForExit(handle)
        raise
    except KeyboardInterrupt:
        raise

    ljm_stream_util.prepareForExit(handle)
    
    
def openLJMDevice(deviceType, connectionType, identifier):
    try:
        handle = ljm.open(deviceType, connectionType, identifier)
    except ljm.LJMError:
        print(
            "Error calling ljm.open(" +
            "deviceType=" + str(deviceType) + ", " +
            "connectionType=" + str(connectionType) + ", " +
            "identifier=" + identifier + ")"
        )
        raise

    return handle


def printDeviceInfo(handle):
    info = ljm.getHandleInfo(handle)
    print(
        "Opened a LabJack with Device type: %i, Connection type: %i,\n"
        "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i\n" %
        (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5])
    )


if __name__ == "__main__":
    main()