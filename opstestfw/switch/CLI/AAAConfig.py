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


def AAAConfig(**kwargs):
    """
    Library function to configure LAG parameters on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param radiushost : interface to configure
    :type  interface : integer
    :param lacpAggKey: Range betwen 1 and 65535. Key used to identify all
                       members of LAG to be of the same 2 switches.
    :type  lacpAggKey: integer
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    aaaLocal = kwargs.get('aaaLocal', "Enabled")
    config = kwargs.get('config', True)

    # Definition of the return dictionary
    returnCode = 0
    retStruct = dict()
    overallBuffer = []
    bufferString = ""

    # Check if parameter required is used, if not return error -- Constrains
    if deviceObj is None:
        LogOutput('error', "Need to pass switch device object deviceObj")
        returnCode = 1
        returnCls = returnStruct(returnCode=returnCode, buffer=overallBuffer,
                                 data=retStruct)
        return returnCls

    # Navigation to the config Context
    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString,
                                 data=retStruct)
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
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString,
                                 data=retStruct)
        return returnCls

    # Getting into the config mode
    if config is True:
        # enable aaa authention as local
        command = 'aaa authentication login local '
        print command
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])

        if retCode != 0:
            LogOutput('error', "Failed to configure AAA \
                     authentication Local " + deviceObj.device)
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
                returnCls = returnStruct(
                    returnCode=returnCode, buffer=bufferString,
                    data=retStruct)
        else:
            LogOutput(
                'debug',
                "AAA authentication login local configured on " +
                deviceObj.device)

        command = 'aaa authentication login fallback error local '
        print command
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])

        if retCode != 0:
            LogOutput('error', "Failed to configure aaa \
                     authentication local " + deviceObj.device)
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
                returnCls = returnStruct(
                    returnCode=returnCode, buffer=bufferString,
                    data=retStruct)
        else:
            LogOutput(
                'debug',
                "Radius server configured on " +
                deviceObj.device)

    else:
        command = 'aaa authentication login radius '
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to configure aaa authentication login + \
                          radius on device " + deviceObj.device)
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
                returnCls = returnStruct(
                    returnCode=returnCode, buffer=bufferString,
                    data=retStruct)
        else:
            LogOutput(
                'debug',
                "configure aaa authentication login radius " +
                deviceObj.device)

        command = command = 'aaa authentication login fallback error local '
        returnDevInt = deviceObj.DeviceInteract(command=command)
        retCode = returnDevInt['returnCode']
        overallBuffer.append(returnDevInt['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to configure aaa authentication login + \
                          fallback to local on device " + deviceObj.device)
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
                returnCls = returnStruct(
                    returnCode=returnCode, buffer=bufferString,
                    data=retStruct)
        else:
            LogOutput(
                'debug',
                "configure aaa authentication login fallback to local " +
                deviceObj.device)

    # Get out of  config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get out of vtysh config context")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    retCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if retCode != 0:
        LogOutput('error', "Failed to exit vty shell")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString,
                                 data=retStruct)
        return returnCls
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString,
                             data=retStruct)
    return returnCls
