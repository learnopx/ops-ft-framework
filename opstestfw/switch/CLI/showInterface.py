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
###############################################################################
import opstestfw


def showInterface(**kwargs):

    """
    Library function to get specific interface information from the device

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface number context (optional)
    :type  interface : integer
    :return: returnStruct Object
            buffer

    :returnType: object
    """
    deviceObj = kwargs.get('deviceObj', None)
    interface = kwargs.get('interface', None)

    overallBuffer = []
    bufferString = ""

# If Device object is not passed, we need to error out
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass switch deviceObj"
                            + "to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

# Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

##########################################################################
# Send Command
##########################################################################
    if interface is None:
        command = "show interface"
    else:
        command = "show interface " + str(interface)

    opstestfw.LogOutput('debug', "Sending: " + command)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])

    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to get information ." + command)

###########################################################################
# Get out of the Shell
###########################################################################
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

###########################################################################
# Exit for context and validate buffer with information
###########################################################################
    for curLine in overallBuffer:
        bufferString += str(curLine)

    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
