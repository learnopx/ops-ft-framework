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


def InterfaceIpConfig(**kwargs):

    """
    Library function configure IPv4 / IPv6 address on an interface, vlan,
    or lag

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface number context (optional)
    :type  interface : integer
    :param vlan      : vlan id (optional)
    :type  vlan      : integer
    :param lag       : lag id (optional)
    :type  lag       : integer
    :param addr      : address string for IPv4 or IPv6 address
    :type addr       : string
    :param mask      : subnet mask bit
    :type maks       : int
    :param secondary : True for secondary address, False for not
    :type secondary  : boolean
    :param routing  : If the interface needs to used as L3
    :type routing    : string
    :param config    : True to configure address
                       False to unconfigure address
                       Defaults to True
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    interface = kwargs.get('interface', None)
    vlan = kwargs.get('vlan', None)
    lag = kwargs.get('lag', None)
    ipv6flag = kwargs.get('ipv6flag', False)
    addr = kwargs.get('addr', None)
    mask = kwargs.get('mask', None)
    secondary = kwargs.get('secondary', False)
    config = kwargs.get('config', True)
    routing = kwargs.get('routing', None)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None:
        LogOutput('error',
                  "Need to pass switch device object to this routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls

    paramError = 0
    if interface is not None:
        if vlan is not None or lag is not None:
            paramError = 1
    if vlan is not None:
        if interface is not None or lag is not None:
            paramError = 1
    if lag is not None:
        if interface is not None or vlan is not None:
            paramError = 1
    if interface is None and vlan is None and lag is None:
        paramError = 1
    if paramError == 1:
        LogOutput('error',
                  "Need to only pass interface, vlan or lag into this routine")
        returnCls = returnStruct(returnCode=1)
        return returnCls
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
    if interface is not None:
        command = "interface " + str(interface)
    elif vlan is not None:
        command = "interface vlan" + str(vlan)
    elif lag is not None:
        command = "interface lag " + str(lag)
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
    if retCode != 0:
        LogOutput('error', "Failed to enter interface context for interface "
                  + str(interface))
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Need to get into the Interface context
    command_formed = False
    if addr is not None and mask is not None:
        command_formed = True
        command = ""
        if config is False:
            command += "no "
        if ipv6flag is False:
            command += "ip "
        else:
            command += "ipv6 "
        if interface == "mgmt":
            command += "static "

        if interface != "mgmt":
            command += "address " + str(addr) + "/" + str(mask)
        else:
            command += str(addr) + "/" + str(mask)

        if secondary is True:
            command += " secondary"

    if routing is not None:
        command_formed = True
        command = ""
        if config is False:
            command += "no "
        command += "routing"

    if command_formed is True:
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        if retCode != 0:
            LogOutput('error', "Failed to configure address command "
                      + command + " on interface " + str(interface))
        else:
            LogOutput('debug', "Configured address command "
                      + command + " on interface " + str(interface))

    # Get out of the interface context
    command = "exit \r"
    returnStructure = deviceObj.DeviceInteract(command=command)
    retCode = returnStructure['returnCode']
    overallBuffer.append(returnStructure['buffer'])
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
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
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
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    # Return results
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
