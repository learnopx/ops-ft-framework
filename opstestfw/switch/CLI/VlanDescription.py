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


def VlanDescription(**kwargs):

    """
    Library function to show the VLANs.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param description : string with the VLAN description. This is casted to
                         string.
    :type description : string
    :param config     : True if a VLAN description is to be added,
                        False if a VLAN description is to be deleted.
                        Defaults to True.
    :return: returnStruct Object
    :returnType: object
    """
    deviceObj = kwargs.get('deviceObj', None)
    vlanId = kwargs.get('vlanId', None)
    description = kwargs.get('description', None)
    config = kwargs.get('config', True)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None or description is None or vlanId is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch device object deviceObj, "
                            "VLAN id vlanId and VLAN description description "
                            "to this routine")
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

    # Get into config context
    returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    command = "vlan " + str(vlanId)

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to get into vlan prompt."
                            + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Created VLAN." + command)

    if config:
        command = ""
    else:
        command = "no "

    command = command + "description " + str(description)

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        if config:
            opstestfw.LogOutput('error',
                                "Failed to set the VLAN description."
                                + command)
        else:
            opstestfw.LogOutput('error',
                                "Failed to remove the VLAN description."
                                + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "VLAN description set." + command)

    command = "end"

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vlan context." + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Exited VLAN context." + command)

    # Get out of vtyshell
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

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
