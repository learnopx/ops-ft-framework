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
import re


def MgmtInterfaceShow(**kwargs):
        """
        Library function to return management interface details
        :param deviceObj	: Device object
	:type deviceObj         : object
        :returnType             : returnStruct object
	    data:- Dictionary
                'Mgmt_IPV4_Address'	    : Mgmt IPV4 addr
                'Mgmt_IPV6_Address'	    : Mgmt IPV6 addr
                'Mgmt_IPV4_Gateway_Address' : Mgmt IPV4 GW addr
                'Mgmt_IPV6_Gateway_Address' : Mgmt IPV6 GW addr
                'MgmtIPV6PrimaryNS'	    : Mgmt IPV6 Primary NS Addr
                'MgmtIPV6SecondaryNS'	    : Mgmt IPV6 Secondary NS Addr
                'MgmIPV4PrimaryNS'	    : Mgmt IPV4 Primary NS Addr
                'MgmtIPV4SecondaryNS'	    : Mgmt IPV4 Secondary NS Addr
        """

        deviceObj = kwargs.get('deviceObj')
        returnDict = dict()
        overallBuffer = []
        returnCode = 0
        # If Device object is not passed, we need to error out
        if deviceObj is None:
            LogOutput('error', "Need to pass switch device object to this "
                               "routine")
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
            returnCls = returnStruct(returnCode=returnCode,
                                     buffer=bufferString)
            return returnCls

        # Pass show commands here
        command = "show interface mgmt"
        returnStructure = deviceObj.DeviceInteract(command=command)
        retCode = returnStructure['returnCode']
        overallBuffer.append(returnStructure['buffer'])
        rawBuffer = returnStructure.get('buffer')
        bufferSplit = rawBuffer.split("\r\n")
        
        for line in bufferSplit:
            line = line.strip()

            MgmtIPV4 = re.match(
                "IPv4 address\/subnet-mask\s+: ((?:[0-9]{1,3}\.){3}[0-9]{1,3})"
                "\/\d+", line)
            if MgmtIPV4:
                returnDict['Mgmt_IPV4_Address'] = MgmtIPV4.group(1)

            MgmtIPV6 = re.match("IPv6 address/prefix\s+: ([A-Za-z::.0-9]+)",
                                line)
            if MgmtIPV6:
                returnDict['Mgmt_IPV6_Address'] = MgmtIPV6.group(1)

            MgmtIPV4gateway = re.match(
                "Default gateway IPv4\s+: ((?:[0-9]{1,3}\.){3}[0-9]{1,3})",
                line)
            if MgmtIPV4gateway:
                returnDict[
                    'Mgmt_IPV4_Gateway_Address'] = MgmtIPV4gateway.group(1)

            MgmtIPV6gateway = re.match(
                "Default gateway IPv6\s+: ([A-Za-z::.0-9]+)", line)
            if MgmtIPV6gateway:
                returnDict[
                    'Mgmt_IPV6_Gateway_Address'] = MgmtIPV6gateway.group(1)

            MgmtIPV6PrimaryNameserver = re.match(
                "Primary Nameserver\s+: ([A-Za-z::.0-9]+)",
                line)
            if MgmtIPV6PrimaryNameserver:
                returnDict[
                    'MgmtIPV6PrimaryNS'] = MgmtIPV6PrimaryNameserver.group(1)

            MgmtIPV6SecondaryNameserver = re.match(
                "Secondary Nameserver\s+: ([A-Za-z::.0-9]+)",
                line)
            if MgmtIPV6SecondaryNameserver:
                returnDict[
                    'MgmtIPV6SecondaryNS'] = \
                    MgmtIPV6SecondaryNameserver.group(1)

            MgmtIPV4PrimaryNameserver = re.match(
                "Primary Nameserver\s+: ((?:[0-9]{1,3}\.){3}[0-9]{1,3})",
                line)
            if MgmtIPV4PrimaryNameserver:
                returnDict[
                    'MgmIPV4PrimaryNS'] = MgmtIPV4PrimaryNameserver.group(1)

            MgmtIPV4SecondaryNameserver = re.match(
                "Secondary Nameserver\s+: ((?:[0-9]{1,3}\.){3}[0-9]{1,3})",
                line)
            if MgmtIPV4SecondaryNameserver:
                returnDict[
                    'MgmtIPV4SecondaryNS'] = \
                    MgmtIPV4SecondaryNameserver.group(1)

        # Exit the vtysh shell
        returnStructure = deviceObj.VtyshShell(configOption="unconfig")
        returnCode = returnStructure.returnCode()
        if returnCode != 0:
            LogOutput('error', "Failed to exit vtysh prompt")
            returnCls = returnStruct(returnCode=returnCode)
            return returnCls

       # Return results
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(
            returnCode=0,
            data=returnDict,
            buffer=bufferString)
        return returnCls
