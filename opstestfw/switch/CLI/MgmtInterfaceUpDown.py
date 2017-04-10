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


def MgmtInterfaceUpDown(**kwargs):
    """
    Library function to get into switch linux mode & execute interface up/down

    :param deviceObj	 : Device object
    :param gotolinuxmode : Goto switch linux mode & execute interface up/down
    :type gotolinuxmode	 : boolean
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    gotolinuxmode = kwargs.get('gotolinuxmode', True)

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

    # Get into switch linux mode
    if gotolinuxmode is True:
        command = "start-shell\r"
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])
        deviceObj.deviceContext = "linux"
        if retCode != 0:
            LogOutput(
                'error',
                "Failed get switch Linux mode")
            returnCls = returnStruct(returnCode=retCode, buffer=overallBuffer)
            return returnCls

        # pass ifconfig eth0 down
        command = "ifconfig eth0 down"
        command += "\r"
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])

        # pass ifconfig eth0 up
        command = "ifconfig eth0 up"
        command += "\r"
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])

    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
