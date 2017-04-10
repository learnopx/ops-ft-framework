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


def SwitchCpuLoad(**kwargs):
    """
    Library function to simulate switch CPU load

    :param deviceObj	        : Device object
    :param gotolinuxmode	: Goto switch linux mode & start/stop CPU load
    :type gotolinuxmode	: boolean
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    gotolinuxmode = kwargs.get('gotolinuxmode', True)
    config = kwargs.get('config', True)

    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error', "Need to pass switch device object deviceObj")
        returnCls = returnStruct(returnCode=1)
        return returnCls
    overallBuffer = []

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls
    print deviceObj.deviceContext

    if config is True:
        if gotolinuxmode is True:
            command = "start-shell\r"
            returnDevInt = deviceObj.DeviceInteract(command=command)
            retCode = returnDevInt['returnCode']
            overallBuffer.append(returnDevInt['buffer'])
            deviceObj.deviceContext = "linux"
            if retCode != 0:
                LogOutput('error', "Failed get switch Linux mode")
                returnCls = returnStruct(
                    returnCode=retCode,
                    buffer=overallBuffer)
                return returnCls

        # Pass below command to start switch CPU load simulation
            command = "for i in 1 2 3 4 ; do while : ; do : ; done & done"
            command += "\r"
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])
    else:
        # Pass below command to stop switch CPU load simulation
        if gotolinuxmode is True:
            command = "exit\r"
            returnDevInt = deviceObj.DeviceInteract(command=command)
            retCode = returnDevInt['returnCode']
            overallBuffer.append(returnDevInt['buffer'])
            deviceObj.deviceContext = "linux"
            if retCode != 0:
                LogOutput('error', "Failed get switch Linux mode")
                returnCls = returnStruct(
                    returnCode=retCode,
                    buffer=overallBuffer)
                return returnCls

            command = "for i in 1 2 3 4 ; do kill %$i; done"
            command += "\r"
            returnStructure = deviceObj.DeviceInteract(command=command)
            retCode = returnStructure['returnCode']
            overallBuffer.append(returnStructure['buffer'])

    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
