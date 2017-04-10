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
import re
import opstestfw


def lagpGlobalSystemShow(**kwargs):
    """
    Function to extract Global LACP configuration

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
         data    dictionary with the following keys/values
                 System-id = <int>
                 System-priority = <int> [0-65534]
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)

    # Variables
    overallBuffer = []
    data = dict()
    bufferString = ""
    command = ""

    # Dictionary initialization
    data['System-id'] = ""
    data['System-priority'] = 0

    # If Device object is not passed, we need to error out
    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch deviceObj to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtysh
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    # Show command
    command += ("show lacp configuration")
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to execute LACP configuration show")
    else:
        opstestfw.LogOutput('debug', "LACP configuration show succeeded")

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit enable prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.retStruct(returnCode=returnCode,
                                        buffer=bufferString)
        return returnCls

    # Return results
    for curLine in overallBuffer:
        bufferString += str(curLine)

    # Fill dictionary out
    for curLine in bufferString.split('\r\n'):
        print curLine
        showLine1 = re.match(
            r'System-id\s*:\s*(([A-Za-z0-9]{2}:?){6})', curLine)
        if showLine1:
            data['System-id'] = showLine1.group(1)
            continue

        showLine2 = re.match(r'System-priority \s*:\s*(\d+)', curLine)
        if showLine2:
            data['System-priority'] = int(showLine2.group(1))
            continue

    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString,
                                       data=data)
    return returnCls
