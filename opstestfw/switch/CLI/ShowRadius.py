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
import opstestfw.switch
from opstestfw import *
import re
import time


def ShowRadius(**kwargs):
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

    # Pass Radius commands here
    command = "show radius-server"
    LogOutput("info", "show radius command ***" + command)
    devIntRetStruct = deviceObj.DeviceInteract(command=command)
    returnCode = devIntRetStruct.get('returnCode')
    overallBuffer.append(devIntRetStruct.get('buffer'))
    if returnCode != 0:
        LogOutput('error', "Failed to get show radius config command")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls
    else:
        rawBuffer = devIntRetStruct.get('buffer')
        bufferSplit = rawBuffer.split("\r\n")
        print rawBuffer
        for line in bufferSplit:
            HostIP = re.match("^Host\s+IP\s+address\s+:\s+(.*)", line)
            if HostIP:
                returnDict['Host_IP_address'] = HostIP.group(1)
                continue
            AuthPort = re.match("^Auth\s+port\s+:\s+(\d+)", line)
            if AuthPort:
                returnDict['Auth_port'] = AuthPort.group(1)
                continue
            SharedSecret = re.match(
                "^Shared\s+secret\s+:\s+(\w+)",
                line)
            if SharedSecret:
                returnDict['Radius_Secret'] = SharedSecret.group(1)
                continue
            Retries = re.match(
                "^Retries\s+:\s+(\d+)",
                line)
            if Retries:
                returnDict['Radius_Retries'] = Retries.group(1)
                continue
            Timeout = re.match(
                "^Timeouts+:\s+(\d+)",
                line)
            if Timeout:
                returnDict['Radius_Timeout'] = Timeout.group(1)
                continue

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
