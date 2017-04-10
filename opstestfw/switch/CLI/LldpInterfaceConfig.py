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


def LldpInterfaceConfig(**kwargs):

    """
    Interface level configuration for LLDP

    :param deviceObj : Device Object
    :type deviceObj  : object
    :param interface : Switch Interface
    :type interface  : integer
    :param transmission : Enables transmission when True
    :type transmission  : Boolean
    :param reception : enables reception when True
    :type reception  : Boolean

    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    interface = kwargs.get('interface', None)
    transmission = kwargs.get('transmission', None)
    reception = kwargs.get('reception', None)

    # If Device object is not passed, we need to error out
    if deviceObj is None or interface is None:
        LogOutput(
            'error',
            "Need to pass switch device object deviceObj and interface to "
            "this routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    overallBuffer = []
    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Get into the interface context
    command = "interface " + str(interface)
    returnDict = deviceObj.DeviceInteract(command=command)
    retCode = returnDict['returnCode']
    overallBuffer.append(returnDict['buffer'])
    if retCode != 0:
        LogOutput(
            'error',
            "Failed to enter interface context for interface "
            + str(interface))
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Need to get into the Interface context
    if transmission is True:
        command = "lldp transmit\r"
        returnDict = deviceObj.DeviceInteract(command=command)
        retCode = returnDict['returnCode']
        overallBuffer.append(returnDict['buffer'])
        if retCode != 0:
            LogOutput(
                'error',
                "Failed to enable lldp tranmission on interface "
                + str(interface))
        else:
            LogOutput(
                'debug',
                "Enabled lldp transmission on interface " + str(interface))

    if transmission is False:
        command = "no lldp transmit\r"
        returnDict = deviceObj.DeviceInteract(command=command)
        retCode = returnDict['returnCode']
        overallBuffer.append(returnDict['buffer'])
        if retCode != 0:
            LogOutput(
                'error',
                "Failed to disable lldp transmission on interface "
                + str(interface))
        else:
            LogOutput(
                'debug',
                "Disabled lldp transmission on interface " + str(interface))

    if reception is True:
        command = "lldp receive\r"
        returnDict = deviceObj.DeviceInteract(command=command)
        retCode = returnDict['returnCode']
        overallBuffer.append(returnDict['buffer'])
        if retCode != 0:
            LogOutput(
                'error',
                "Failed to enable lldp reception on interface  "
                + str(interface))
        else:
            LogOutput(
                'debug',
                "Enabled lldp reception on interface " + str(interface))

    if reception is False:
        command = "no lldp receive\r"
        returnDict = deviceObj.DeviceInteract(command=command)
        retCode = returnDict['returnCode']
        overallBuffer.append(returnDict['buffer'])
        if retCode != 0:
            LogOutput(
                'error',
                "Failed to disable lldp reception on interface  "
                + str(interface))
        else:
            LogOutput(
                'debug',
                "Disabled lldp reception on interface " + str(interface))

    # Get out of the interface context
    command = "exit \r"
    returnDict = deviceObj.DeviceInteract(command=command)
    retCode = returnDict['returnCode']
    overallBuffer.append(returnDict['buffer'])
    if retCode != 0:
        LogOutput('error', "Failed to exit the interface context")

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to exit vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
