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
import re
import pexpect


def lagMode(**kwargs):

    """
    Library function to configure a LAGs mode (static/dynamic)

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG Identifier
    :type  lagId     : integer
    :param lacpMode  : off: Static LAG
                       active: Active dynamic LAG
                       passive: Passive dynamic LAG
    :type  lacpMode  : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    lagId = kwargs.get('lagId', None)
    deviceObj = kwargs.get('deviceObj', None)
    lacpMode = kwargs.get('lacpMode', 'off')

    # Variables
    overallBuffer = []
    initialStatus = ''
    finalReturnCode = 0

    # If deviceObj, lagId or lacpMode are not present, thorw an error
    if deviceObj is None or lagId is None:
        opstestfw.LogOutput('error',
                            "Need to pass deviceObj and lagId to use this "
                            "routine")
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

    # Query switch for LAG configuration
    # Note this command is not the core of the function, but it is so
    # important that if the initial status of the LAG mode cannot be
    # determined, the other will always fail
    command = 'show lacp aggregates lag' + str(lagId)
    returnDevInt = deviceObj.DeviceInteract(command=command)
    finalReturnCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if finalReturnCode != 0:
        opstestfw.LogOutput('error',
                            "Could not obtain LAG LACP mode initial status")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
    else:
        # TEMPORARY
        # Obtain result of command
        buffer2 = ''
        while True:
            result = deviceObj.expectHndl.expect(['# ', pexpect.TIMEOUT],
                                                 timeout=5)
            buffer2 += str(deviceObj.expectHndl.before) + str(deviceObj.expectHndl.after)
            if result == 1:
                break
        overallBuffer.append(buffer2)
        # END OF TEMPORARY

        # Parse buffer for values of interest
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        result = re.search('Aggregate mode[ ]+: (off|passive|active)',
                           bufferString)
        if result is None:
            opstestfw.LogOutput('error',
                                "Could not identify LAG LACP mode initial "
                                "status")
            returnCls = opstestfw.returnStruct(returnCode=1,
                                               buffer=bufferString)
            return returnCls
        else:
            initialStatus = result.group(1)
            opstestfw.LogOutput('debug',
                                "LAG LACP mode initial status identified as "
                                + initialStatus)

        # mVerify if the LAG was already in static mode and will be changed
        # again
        if initialStatus == lacpMode and lacpMode == 'off':
            opstestfw.LogOutput('debug',
                                "LACP mode is set to off already. No change "
                                "is performed")
        else:
            # Get into config context
            returnStructure = deviceObj.ConfigVtyShell(enter=True)
            returnCode = returnStructure.returnCode()
            overallBuffer.append(returnStructure.buffer())
            if returnCode != 0:
                opstestfw.LogOutput('error',
                                    "Failed to get vtysh config prompt")
                bufferString = ""
                for curLine in overallBuffer:
                    bufferString += str(curLine)
                returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                                   buffer=bufferString)
                return returnCls

            # enter LAG configuration context
            command = "interface lag " + str(lagId)
            returnDevInt = deviceObj.DeviceInteract(command=command)
            returnCode = returnDevInt['returnCode']
            overallBuffer.append(returnDevInt['buffer'])
            if returnCode != 0:
                opstestfw.LogOutput('error', "Failed to enter LAG"
                                    + str(lagId)
                                    + " configuration context on device "
                                    + deviceObj.device)
                bufferString = ""
                for curLine in overallBuffer:
                    bufferString += str(curLine)
                returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                                   buffer=bufferString)
            else:
                opstestfw.LogOutput('debug', "Entered LAG" + str(lagId)
                                    + " configuration context on device "
                                    + deviceObj.device)

            # configure LAG mode
            if str(lacpMode) != 'off':
                command = "lacp mode " + str(lacpMode)
            else:
                command = "no lacp mode " + initialStatus
            returnDevInt = deviceObj.DeviceInteract(command=command)
            finalReturnCode = returnDevInt['returnCode']
            overallBuffer.append(returnDevInt['buffer'])
            if finalReturnCode != 0:
                opstestfw.LogOutput('error',
                                    "Failed to configure LACP mode to "
                                    + lacpMode + " on device "
                                    + deviceObj.device)
            else:
                opstestfw.LogOutput('debug', "Changed LACP mode to "
                                    + lacpMode + " on device "
                                    + deviceObj.device)
                # exit LAG configuration context
                command = "exit"
                returnDevInt = deviceObj.DeviceInteract(command=command)
                returnCode = returnDevInt['returnCode']
                overallBuffer.append(returnDevInt['buffer'])
                if returnCode != 0:
                    opstestfw.LogOutput('error', "Failed to exit LAG "
                                        + str(lagId)
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
                                    "Failed to get out of vtysh config "
                                    "context")
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
