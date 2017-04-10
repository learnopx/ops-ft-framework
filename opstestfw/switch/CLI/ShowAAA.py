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


def ShowAAA(**kwargs):
    deviceObj = kwargs.get('deviceObj')
    port = kwargs.get('port', None)
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
    command = "show aaa authentication"
    LogOutput("info", "show aaa authentication command ***" + command)
    devIntRetStruct = deviceObj.DeviceInteract(command=command)
    returnCode = devIntRetStruct.get('returnCode')
    overallBuffer.append(devIntRetStruct.get('buffer'))
    if returnCode != 0:
        LogOutput('error', "Failed to get show aaa config command")
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
            localAuth = re.match("^Local\s+authentication\s+:\s+(\w+)", line)
            if localAuth:
                returnDict['local_Authentication'] = localAuth.group(1)
                continue
            RadiusAuth = re.match("^Radius\s+authentication\s+:\s+(\w+)", line)
            if RadiusAuth:
                returnDict['Radius_Authentication'] = RadiusAuth.group(1)
                continue
            Fallback = re.match(
                "^Fallback\s+to\s+local\s+authentication\s+:\s+(\w+)",
                line)
            if Fallback:
                returnDict['Fallback_Authentication'] = Fallback.group(1)
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
