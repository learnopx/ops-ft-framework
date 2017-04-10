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


def IpRouteConfig(**kwargs):

    """
    Library function configure IPv4 or IPv6 address on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param route     : route address to configure
    :type  route     : string
    :param ipv6flag  : True for IPv6, False is IPv4.  Default is False
    :type  ipv6flag  : boolean
    :param mask      : subnet mask bits
    :type  mask      : integer
    :param nexthop   : Can be an ip address or a interface
    :type  nexthop   : string
    :param config    : True to configure, False to unconfigure
    :type  config    : boolean
    :param metric    : route address to configure
    :type  metric    : integer

    :return: returnStruct Object
    :returnType: object
    """

    deviceObj = kwargs.get('deviceObj', None)
    ipv6flag = kwargs.get('ipv6flag', False)
    route = kwargs.get('route', None)
    mask = kwargs.get('mask', None)
    config = kwargs.get('config', True)
    nexthop = kwargs.get('nexthop', None)
    metric = kwargs.get('metric', None)

    overallBuffer = []
    # If Device object is not passed, we need to error out
    if deviceObj is None or route is None or mask is None or nexthop is None:
        LogOutput('error', "Need to pass switch device object deviceObj, "
                  "route, mask, and nexthop to this routine")
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
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
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

    # Build route command
    command = ""
    if config is False:
        command += "no "
    if ipv6flag is False:
        command += "ip "
    else:
        command += "ipv6 "
    command += "route " + str(route) + "/" + str(mask) + " " + str(nexthop)

    if metric is not None:
        command += " " + str(metric)

    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    if retCode != 0:
        LogOutput('error', "Failed to configure route command " + command)
    else:
        LogOutput('debug', "Configured route command " + command)

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
