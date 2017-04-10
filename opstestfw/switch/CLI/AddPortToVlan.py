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


def AddPortToVlan(**kwargs):

    """
    Library function to add a port to a VLAN.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param interface : Id of the interface to add to the VLAN.
                       Routing will be disabled in the interface.
                       Send here a string "lag X" to add a lag.
    :type interface  : int
    :param access    : True to add access to the command, False to add
                       trunk to the command. Defaults to False.
    :type access     : boolean
    :param allowed   : True to add allowed after trunk, False to add
                       native after trunk. Defaults to False.
    :type allowed    : boolean
    :param tag       : True to add tag after native. False to add nothing.
                       Defaults to False.
    :type tag        : boolean
    :param config    : True if a port is to be added to the VLAN,
                       False if a port is to be removed from a VLAN.
                       Defaults to True.
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    vlanId = kwargs.get('vlanId', None)
    interface = kwargs.get('interface', None)
    access = kwargs.get('access', False)
    allowed = kwargs.get('allowed', False)
    tag = kwargs.get('tag', False)
    config = kwargs.get('config', True)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None or vlanId is None or interface is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch device object deviceObj, "
                            "interface interface and VLAN Id vlanId to "
                            "this routine")
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

    command = "interface " + str(interface)

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to get into interface prompt." + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Got into interface prompt." + command)

    command = "no routing"

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error',
                            "Failed to disable routing in the interface."
                            + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Exited interface context." + command)

    if config:
        command = ""
    else:
        command = "no "

    command = command + "vlan "

    if access:
        command = command + "access " + str(vlanId)
    else:
        command = command + "trunk "
        if allowed:
            command = command + "allowed " + str(vlanId)
        else:
            command = command + "native "
            if tag:
                command = command + "tag"
            else:
                command = command + str(vlanId)

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        if config:
            opstestfw.LogOutput('error',
                                "Failed to add the port to the VLAN."
                                + command)
        else:
            opstestfw.LogOutput('error',
                                "Failed to remove the port from the VLAN."
                                + command)

        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Added the port to the VLAN." + command)

    command = "end"

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        opstestfw.LogOutput('error', "Failed to exit interface context."
                            + command)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
    else:
        opstestfw.LogOutput('debug', "Exited interface context." + command)

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
