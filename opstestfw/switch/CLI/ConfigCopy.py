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


def ConfigCopy(**kwargs):
    """
    Library function to copy files between two different place

    :param deviceObj            : Device object
    :param sourceplace    	: instucts the source place (Eg:running)
    :type sourceplace           : string
    :param destinationplace	: instructs the destination place (Eg:start-up)
    :type destinationplace      : string
    :return                     : returnStruct Object
    :returnType                 : object
    """

    deviceObj = kwargs.get('deviceObj', None)
    sourceplace = kwargs.get('sourceplace', 'running')
    destinationplace = kwargs.get('destinationplace', 'start-up')

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

    if sourceplace is 'running' and destinationplace is 'start-up':
        command = "copy running-config startup-config\r"
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])
        if retCode != 0:
            LogOutput(
                'error',
                "Failed to copy running config to startup config")
            returnCls = returnStruct(returnCode=retCode, buffer=overallBuffer)
            return returnCls
        else:
            LogOutput('debug', "Copy Config Runing-Startup" + deviceObj.device)

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    retCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if retCode != 0:
        LogOutput('error', "Failed to exit vty shell")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    bufferString = ""
    for curLine in overallBuffer:
            bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
