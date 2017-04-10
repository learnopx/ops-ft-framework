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
import opstestfw


def lagHeartbeat(**kwargs):

    """
    Library function to configure heartbeat speed on a LAG

    :param deviceObj: device object
    :type deviceObj:  VSwitch device object
    :param lagId: LAG identifier
    :type lagId: int
    :param lacpFastFlag: True for LACP fast heartbeat, false for slow heartbeat
    :type lacpFastFlag: boolean
    :return: returnStruct object
    :rtype: object
    """

    # Params
    lagId = kwargs.get('lagId', None)
    deviceObj = kwargs.get('deviceObj', None)
    lacpFastFlag = kwargs.get('lacpFastFlag', True)

    # Variables
    overallBuffer = []
    finalReturnCode = 0

    # If device, LAG Id or lacpFastFlag are not passed, return an error
    if deviceObj is None or lagId is None or lacpFastFlag is None:
        opstestfw.LogOutput('error',
                            "Need to pass deviceObj and lagId to use "
                            "this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # enter LAG configuration context
    command = "interface lag %s" % str(lagId)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    returnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to create LAG " + str(lagId)
                            + " on device " + deviceObj.device)
    else:
        opstestfw.LogOutput('debug', "Created LAG " + str(lagId)
                            + " on device " + deviceObj.device)

    # configure LAG heartbeat settings
    command = ""
    if lacpFastFlag is False:
        command = "no "
    command += "lacp rate fast"
    returnDevInt = deviceObj.DeviceInteract(command=command)
    finalReturnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if finalReturnCode != 0:
        if lacpFastFlag is True:
            opstestfw.LogOutput('error',
                                "Failed to configure LACP fast heartbeat on "
                                "interface lag " + str(lagId) + " on device "
                                + deviceObj.device)
        else:
            opstestfw.LogOutput('error',
                                "Failed to configure LACP slow heartbeat on "
                                "interface lag " + str(lagId) + " on device "
                                + deviceObj.device)
    else:
        if lacpFastFlag is True:
            opstestfw.LogOutput('debug',
                                "Configured LACP fast heartbeat on interface"
                                " lag " + str(lagId) + " on device "
                                + deviceObj.device)
        else:
            opstestfw.LogOutput('debug',
                                "Configure LACP slow heartbeat on interface"
                                " lag " + str(lagId) + " on device "
                                + deviceObj.device)

    # exit LAG configuration context
    command = "exit"
    returnDevInt = deviceObj.DeviceInteract(command=command)
    returnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit LAG " + str(lagId)
                            + " configuration context")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Get out of  config context
    returnStructure = deviceObj.ConfigVtyShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to get out of vtysh config context")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vty shell")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Compile information to return
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(returnCode=finalReturnCode,
                                       buffer=bufferString)
    return returnCls
