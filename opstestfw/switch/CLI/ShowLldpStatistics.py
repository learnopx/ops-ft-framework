# (C) Copyright 2015 Hewlett Packard Enterprise Development LP
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from opstestfw import *
import re


def ShowLldpStatistics(**kwargs):
    deviceObj = kwargs.get('deviceObj')
    returnDict = dict()
    overallBuffer = []
    returnStructure = deviceObj.VtyshShell()
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    # Pass LLDP commands here
    command = "show lldp statistics"

    devIntRetStruct = deviceObj.DeviceInteract(command=command)
    returnCode = devIntRetStruct.get('returnCode')
    overallBuffer.append(devIntRetStruct.get('buffer'))
    if returnCode != 0:
        LogOutput('error', "Failed to get show lldp statistics command")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls
    else:
        rawBuffer = devIntRetStruct.get('buffer')
        bufferSplit = rawBuffer.split("\r\n")
        globalStatsDict = dict()
        for line in bufferSplit:
            TotalPacketsTransmitted = \
                re.match("^Total\sPackets\stransmitted\s*:\s*(\d+)\s*$", line)
            if TotalPacketsTransmitted:
                globalStatsDict['Total_Packets_Transmitted'] = \
                    TotalPacketsTransmitted.group(1)
                continue
            TotalPacketsReceived = \
                re.match("^Total\sPackets\sreceived\s*:\s*(\d+)\s*$", line)
            if TotalPacketsReceived:
                globalStatsDict['Total_Packets_Received'] = \
                    TotalPacketsReceived.group(1)
                continue
            TotalPacketsReceivedAndDiscarded = re.match("^Total\sPacket\
                \sreceived\sand\sdiscarded\s*:\s*(\d+)\s*$", line)
            if TotalPacketsReceivedAndDiscarded:
                globalStatsDict['Total_Packets_Received_And_Discarded'] = \
                    TotalPacketsReceivedAndDiscarded.group(1)
                continue
            TotalTLVsUnrecognized = \
                re.match("^Total\sTLVs\sunrecognized\s*:\s*(\d+)\s*$", line)
            if TotalTLVsUnrecognized:
                globalStatsDict['Total_TLVs_Unrecognized'] = \
                    TotalTLVsUnrecognized.group(1)
            # Need to add LLDP Port Statistics

            returnDict['globalStats'] = globalStatsDict
    returnStructure = deviceObj.VtyshShell(configOption="unconfig")
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh prompt")
        returnCls = returnStruct(returnCode=returnCode,)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(
        returnCode=0,
        buffer=bufferString,
        data=returnDict)
    return returnCls
