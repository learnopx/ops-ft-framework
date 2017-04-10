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
import pexpect
import opstestfw.switch
import time
import os
import re
from Device import Device
import socket
import opstestfw
import paramiko
import json


class VHost(Device):

    """
    Virtual Host Class definition

    This Class defines the host connections and interface connectivity
    """

    def __init__(self, **kwargs):
        """
        VHost init method

        This method will create a VHost object that will contain all
        connection information to interact with the device and also contain
        the logical port to physical port mapping information on device
        connectivity

        :param topology: topology dictionary defined in the test case
        :type topology: dictionary
        :param device: device name to create the object
        :type device: string
        """
        self.topology = kwargs.get('topology', None)
        self.device = kwargs.get('device', None)
        # Bring in Default member values
        self.defaultMembers()
        self.expectDefaultPrompts = ['login:\s*$',
                                     'Password:',
                                     '\[root@\S+.*\]#',
                                     'root@\S+#',
                                     '\(yes/no\)?',
                                     'password:',
                                     'Connection closed by foreign host.',
                                     'Login incorrect',
                                     pexpect.EOF,
                                     pexpect.TIMEOUT]
        self.initExtMembers()
        self.Connect()

    def defaultMembers(self):
        """
        membersDefaults method

        This method just defines the defaults for all the members assocated
        with this method.
        """
        self.expectHndl = ""
        self.connectStringBase = "docker exec -ti "
        self.commandErrorCheck = 1

    def initExtMembers(self):
        """
        initExtMembers method

        This method just defines host base interface config commands
        """
        self.LIST_ETH_INTERFACES_CMD = 'ifconfig -a | grep Ethernet'
        self.LIST_INTERFACE_IP_CMD = 'ifconfig %s | grep inet'
        self.ENABLE_ETH_INTERFACE_CMD = 'ifconfig %s up'
        self.ETH_INTERFACE_CFGIP_CMD = 'ip addr add %s/%d dev %s'
        self.ETH_INT_CFGIP_IFCFG_CMD = 'ifconfig %s %s netmask %s broadcast %s'
        self.ETH_INTERFACE_CFGIP_CLEAR_CMD = 'ip addr del %s/%d dev %s'
        self.ETH_INTERFACE_CFGIP_IFCFG_CLEAR_CMD = 'ifconfig %s 0.0.0.0'
        self.fwbase = os.path.dirname(opstestfw.__file__)

    def Connect(self):
        """
        Connect Method

        This method is used to connect to the VHost device.  This is called
        by the init method.
        """
        # Look up the device name in the topology - grab connectivity
        # information
        xpathString = ".//device[name='" + self.device + "']"
        etreeElement = opstestfw.XmlGetElementsByTag(self.topology.TOPOLOGY,
                                                     xpathString)
        if etreeElement is None:
            # We are not in a good situation, we need to bail
            opstestfw.LogOutput('error',
                                "Could not find"
                                " device " + self.device + " in topology")
            return None
        # Code for virtual
        # Go and grab the connection name
        xpathString = ".//device[name='" + self.device + "']/connection/name"
        virtualConn = opstestfw.XmlGetElementsByTag(self.topology.TOPOLOGY,
                                                    xpathString)
        if virtualConn is None:
            opstestfw.LogOutput('error',
                                "Failed to virtual connection "
                                "for " + self.device)
            return None
        telnetString = self.connectStringBase + self.device + " /bin/bash"
        self.expectHndl = pexpect.spawn(telnetString, echo=False)
        expectFileString = self.device + ".log"

        ExpectInstance = opstestfw.DeviceLogger(expectFileString)
        expLog = ExpectInstance.OpenExpectLog(expectFileString)
        if expLog == 1:
            opstestfw.LogOutput('error', "Unable to create expect log file")
            exit(1)
        # Opening an expect connection to the device with the specified
        # log file
        opstestfw.LogOutput('debug', "Opening an expect connection to "
                            "the device with the specified log "
                            "file" + expectFileString)
        self.expectHndl = pexpect.spawn(telnetString,
                                        echo=False,
                                        logfile=opstestfw.DeviceLogger(expLog))
        # self.expectHndl.delaybeforesend = .05

        # Lets go and detect our connection - this will get us to a context
        # we know about
        retVal = self.DetectConnection()

        if retVal is None:
            return None
        return self.expectHndl

    def DetectConnection(self):
        """
        DetectConnection Method

        This method called during the connect process to establish a connection
        with the device.  This method is used internally and only by the
        Connect functionality.

        :return: expect handle
        :rtype: expect object
        """

        bailflag = 0
        self.expectHndl.send('\r')
        connectionBuffer = []
        sanitizedBuffer = ""
        while bailflag == 0:
            time.sleep(1)
            index = self.expectHndl.expect(self.expectDefaultPrompts,
                                           timeout=30)
            opstestfw.LogOutput('debug', "Got index ->" + str(index))
            if index == 0:
                # Need to send login string
                connectionBuffer.append(self.expectHndl.before)
                self.expectHndl.send("root")
                self.expectHndl.send("\r")
            elif index == 1:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                self.expectHndl.send("procurve")
                self.expectHndl.send("\r")
            elif index == 2:
                # Got prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 3:
                # Got prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 4:
                # Got yes / no prompt.  We should be good
                self.expectHndl.send("yes")
                self.expectHndl.send("\r")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 5:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                self.expectHndl.send("procurve")
                self.expectHndl.send("\r")
            elif index == 6:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "Telnet to host failed")
                return None
            elif index == 7:
                # Got EOF
                opstestfw.LogOutput('debug', "Login incorrect error")
                #return None
            elif index == 8:
                # Got EOF
                opstestfw.LogOutput('error', "Telnet to host failed")
                return None
            elif index == 9:
                # Got a Timeout
                opstestfw.LogOutput('error', "Connection timed out")
                return None
            else:
                connectionBuffer.append(self.expectHndl.before)
        # Append on buffer after
        connectionBuffer.append(self.expectHndl.after)
        # Now lets put in the topology the expect handle
        self.expectHndl.expect(['$'], timeout=2)
        for curLine in connectionBuffer:
            sanitizedBuffer += curLine
        opstestfw.LogOutput('debug', sanitizedBuffer)

        return self.expectHndl

    def DeviceInteract(self, **kwargs):
        """
        DeviceInteract Method

        This method will send commands over an established connection with
        the device, obtain the output from the command transaction, and then
        send the return buffer off to the appropriate error check routine

        :param command: string of the command to execute
        :type command: string
        :param errorCheck: boolean True to error check, False to turn off
                           error checking.
        :type errorCheck: boolean
        :param yesPrompt: yes prompt answer - choice yes / no
        :type yesPrompt: string
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        """

        command = kwargs.get('command')
        yesPromptResp = kwargs.get('yesPrompt', "yes")
        errorCheck = kwargs.get('errorCheck', True)
        timeout = kwargs.get('timeout', 30)

        # Local variables
        bailflag = 0
        retStruct = dict()
        retStruct['returnCode'] = 1
        retStruct['buffer'] = []
        # Clear out buffer
        try:
            opstestfw.LogOutput('debug', "Flushing buffer")
            buf = self.expectHndl.read_nonblocking(128, 0)
            opstestfw.LogOutput('debug', "Buffer data \n" + buf)
        except pexpect.TIMEOUT:
            pass
        except pexpect.EOF:
            pass

        # Send the command
        self.expectHndl.send(command)
        self.expectHndl.send('\r')
        connectionBuffer = []

        while bailflag == 0:
            index = self.expectHndl.expect(self.expectDefaultPrompts,
                                           timeout=timeout)
            opstestfw.LogOutput('debug', "index = " + str(index))
            if index == 0:
                # Need to send login string
                self.expectHndl.send("root")
                self.expectHndl.send("\r")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 1:
                # Need to send password string
                self.expectHndl.send("procurve")
                self.expectHndl.send("\r")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 2:
                # Got prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 3:
                # Got prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 4:
                # Got yes / no prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                if yesPromptResp == "yes":
                    self.expectHndl.send("yes")
                else:
                    self.expectHndl.send("no")
                self.expectHndl.send("\r")
            elif index == 5:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                self.expectHndl.send("procurve")
                self.expectHndl.send("\r")
            elif index == 6:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "Connection closed")
                returnCode = 1
                bailflag = 1
            elif index == 7:
                # Need to send password string
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "Login incorrect")
                #returnCode = 1
                # bailflag = 1
            elif index == 8:
                # got EOF
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "reached EOF")
                returnCode = 1
                exit(105)
            elif index == 9:
                # got Timeout
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "command timeout")
                returnCode = 1
            else:
                connectionBuffer.append(self.expectHndl.before)

        connectionBuffer.append(self.expectHndl.after)
        self.expectHndl.expect(['$'], timeout=1)
        santString = ""
        for curLine in connectionBuffer:
            santString += str(curLine)

        returnCode = 0
        if errorCheck is True and returnCode == 0 and self.commandErrorCheck == 1:
            # time.sleep(1)
            errorCheckRetStruct = self.ErrorCheck(buffer=santString)
            returnCode = errorCheckRetStruct['returnCode']
        # Dump the buffer the the debug log
        opstestfw.LogOutput('debug',
                            "Sent and received from device:"
                            " \n" + santString + "\n")

        # Return dictionary
        retStruct['returnCode'] = returnCode
        retStruct['buffer'] = santString

        return retStruct

    def ErrorCheck(self, **kwargs):
        """
        ErrorCheck Method

        This method is used to error check a buffer after self.DeviceInteract
        method is run.
        :param buffer: buffer from selfDeviceInteract to check for errors
        :type buffer: string
        :return: dictionary containing returnCode key
        :rtype: dictionary
        """

        buffer = kwargs.get('buffer')
        # Local variables
        returnCode = 0
        exitValue = 0
        retStruct = dict()
        retStruct['returnCode'] = returnCode

        # Set up the command for error check
        command = "echo $?"
        buffer = ""
        self.expectHndl.send(command)
        self.expectHndl.send('\r')
        index = self.expectHndl.expect(['\[root@.*\]#',
                                        'root@.*#',
                                        pexpect.EOF,
                                        pexpect.TIMEOUT], timeout=30)
        if index == 0 or index == 1:
            buffer += self.expectHndl.before
            buffer += self.expectHndl.after
        else:
            opstestfw.LogOutput('error',
                                "Received timeout in ErrorCheck " + str(index))
            retStruct['returnCode'] = 1
            self.expectHndl.expect(['$'], timeout=1)
            return retStruct
        self.expectHndl.expect(['$'], timeout=1)

        bufferSplit = buffer.split("\n")
        for curLine in bufferSplit:
            testforValue = re.match("(^[0-9]+)\s*$", curLine)
            if testforValue:
                # Means we got a match
                exitValue = int(testforValue.group(1))
            if exitValue != 0:
                returnCode = exitValue
            else:
                returnCode = 0
        retStruct['returnCode'] = returnCode
        return retStruct

    def NetworkConfig(self, **kwargs):
        """
        NetworkConfig Method

        This method will configure an ip address over a network interface
        :param interface: network interface to configure address on
        :type interface: string
        :param ipAddr: ip address string
        :type ipAddr: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param broadcast: broadcast address for interface
        :type broadcast: string
        :param config: True to config / False to unconfig interface
        :type config: boolean
        :return: returnStruct Object
        :rtype: object
        """

        eth = kwargs.get('interface')
        ipAddr = kwargs.get('ipAddr')
        netMask = kwargs.get('netMask')
        broadcast = kwargs.get('broadcast')
        config = kwargs.get('config', True)

        bailflag = 0
        interfaceUpOption = 0
        returnCode = 0

        if self.ipFormatChk(ipAddr) is False:
            opstestfw.LogOutput('error', 'invalid ipaddress format :' + ipAddr)
            returnCode = 1
        elif self.ipFormatChk(netMask) is False:
            opstestfw.LogOutput('error', 'invalid netmask format :' + netMask)
            returnCode = 1
        elif self.ipFormatChk(broadcast) is False:
            opstestfw.LogOutput('error',
                                'invalid broadcast format :' + broadcast)
            returnCode = 1

        if returnCode:
            returnCls = opstestfw.returnStruct(returnCode=1)
            return returnCls

        overallBuffer = []
        # Validate that the interface exists
        while bailflag == 0:
            # Send the command
            retDeviceInt = self.DeviceInteract(
                command=self.LIST_ETH_INTERFACES_CMD)
            retCode = retDeviceInt.get('returnCode')
            retBuff = retDeviceInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + self.LIST_ETH_INTERFACES_CMD)
                bailflag = 1
                returnCode = 1
            else:
                opstestfw.LogOutput('debug',
                                    'Successfully executed the command : '
                                    + self.LIST_ETH_INTERFACES_CMD)
                if retBuff.find(eth) != -1:
                    opstestfw.LogOutput('debug',
                                        'eth interface is validated for : '
                                        + eth)
                    bailflag = 1
                else:
                    opstestfw.LogOutput('debug',
                                        "eth interface failed to validate "
                                        "for : " + eth)
                    if interfaceUpOption:
                        bailflag = 1
                        returnCode = 1
                        break
                    interfaceUpOption = 1
                    command = self.ENABLE_ETH_INTERFACE_CMD % eth
                    retDevInt = self.DeviceInteract(command=command)
                    retCode = retDevInt.get('returnCode')
                    retBuff = retDevInt.get('buffer')
                    overallBuffer.append(retBuff)
                    if retCode != 0:
                        opstestfw.LogOutput('error',
                                            'Failed to execute the command : '
                                            + command)
                        bailflag = 1
                        returnCode = 1
                    else:
                        opstestfw.LogOutput('debug',
                                            "Successfully executed the "
                                            "command : " + command)

                    if returnCode:
                        bufferString = ""
                        for curLine in overallBuffer:
                            bufferString += str(curLine)
                        returnCls = opstestfw.returnStruct(returnCode=1,
                                                           buffer=bufferString)
                        return returnCls

        if config is False:
            command = self.ETH_INTERFACE_CFGIP_IFCFG_CLEAR_CMD % eth
            retDevInt = self.DeviceInteract(command=command)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + command)
                returnCode = 1
            else:
                opstestfw.LogOutput('info',
                                    'Successfully executed the command : '
                                    + command)
        else:
            # Here we are configuring the interface
            command = self.ETH_INT_CFGIP_IFCFG_CMD % (eth, ipAddr, netMask,
                                                      broadcast)
            retDevInt = self.DeviceInteract(command=command)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error',
                                    'Failed to execute the command : '
                                    + command)
                returnCode = 1
            else:
                opstestfw.LogOutput('debug',
                                    'Successfully executed the command : '
                                    + command)

            if returnCode != 1:
                command = self.LIST_INTERFACE_IP_CMD % eth
                retDevInt = self.DeviceInteract(command=command)
                retCode = retDevInt.get('returnCode')
                retBuff = retDevInt.get('buffer')
                overallBuffer.append(retBuff)
                if retCode != 0:
                    opstestfw.LogOutput('error',
                                        'Failed to execute the command : '
                                        + command)
                    returnCode = 1
                else:
                    opstestfw.LogOutput('debug',
                                        'Successfully executed the command : '
                                        + command)

            if retBuff.find(ipAddr) == -1:
                opstestfw.LogOutput('error',
                                    "IP addr %s is not configured "
                                    "successfully on interface %s : "
                                    % (ipAddr, eth))
            else:
                opstestfw.LogOutput('info',
                                    "IP addr %s configured successfully on "
                                    "interface %s : " % (ipAddr, eth))

        # Fill out buffer
        bufferString = ""
        for curLin in overallBuffer:
            bufferString += str(curLin)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    def ipFormatChk(self, ip_str):
        """
        ipFormatChk Method

        This method validate ip string format
        :param arg1: ip address string
        :type arg1: string
        :return: boolean
        :rtype: boolean
        """

        patternv4 = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        if re.match(patternv4, ip_str):
            return True
        patternv6 = r"(?:(?:[[:xdigit:]]{0,4}:){1,7}[[:xdigit:]]{0,4})"
        if re.match(patternv6, ip_str):
            return True
        return False

    def Network6Config(self, **kwargs):
        """
        Network6Config Method

        This method will configure an ipv6 address over a network interface
        :param interface: network interface to configure address on
        :type interface: string
        :param ipAddr: ip address string
        :type ipAddr: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param config: True to config / False to unconfig interface
        :type config: boolean
        :return: returnStruct Object
        :rtype: object
        """

        eth = kwargs.get('interface')
        ipAddr = kwargs.get('ipAddr')
        netMask = kwargs.get('netMask')
        config = kwargs.get('config', True)

        # Local variables
        bailflag = 0
        interfaceUpOption = 0
        returnCode = 0
        overallBuffer = []

        try:
            socket.inet_pton(socket.AF_INET6, ipAddr)
        except socket.error:
            returnCode = 1

        if netMask > 128 and netMask < 1:
            returnCode = 1

        if returnCode:
            opstestfw.LogOutput('error',
                                'Invalid ipv6 address or netMask passed ')
            returnCls = opstestfw.returnStruct(returnCode=returnCode)
            return returnCls

        while bailflag == 0:
            # Send the command
            retDevInt = self.DeviceInteract(
                command=self.LIST_ETH_INTERFACES_CMD
            )
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + self.LIST_ETH_INTERFACES_CMD)
                bailflag = 1
                returnCode = 1
            else:
                opstestfw.LogOutput('debug',
                                    'Successfully executed the command : '
                                    + self.LIST_ETH_INTERFACES_CMD)
                if retBuff.find(eth) != -1:
                    opstestfw.LogOutput('info',
                                        'eth interface is validated for : '
                                        + eth)
                    bailflag = 1
                else:
                    opstestfw.LogOutput('error',
                                        'eth interf failed to validate for : '
                                        + eth)
                    if interfaceUpOption:
                        bailflag = 1
                        returnCode = 1
                        break
                    interfaceUpOption = 1
                    command = self.ENABLE_ETH_INTERFACE_CMD % eth
                    retDevInt = self.DeviceInteract(command=command)
                    retCode = retDevInt.get('returnCode')
                    retBuff = retDevInt.get('buffer')
                    overallBuffer.append(retBuff)
                    if retCode != 0:
                        opstestfw.LogOutput('error',
                                            'Failed to execute the command : '
                                            + command)
                        bailflag = 1
                        returnCode = 1
                    else:
                        opstestfw.LogOutput('debug',
                                            'Success executed the command : '
                                            + command)

        if returnCode:
            bufferString = ""
            for curLin in overallBuffer:
                bufferString += str(curLin)

            returnCls = opstestfw.returnStruct(returnCode=1,
                                               buffer=bufferString)
            return returnCls

        if config is False:
            command = self.ETH_INTERFACE_CFGIP_CLEAR_CMD % (
                ipAddr, netMask, eth)
            retDevInt = self.DeviceInteract(command=command)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + command)
                returnCode = 1
            else:
                opstestfw.LogOutput('debug',
                                    'Successfully executed the command : '
                                    + command)
        else:
            command = self.ETH_INTERFACE_CFGIP_CMD % (ipAddr, netMask, eth)
            retDevInt = self.DeviceInteract(command=command)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + command)
                returnCode = 1
            else:
                opstestfw.LogOutput('debug',
                                    'Successfully executed the command : '
                                    + command)

            if returnCode != 1:
                command = self.LIST_INTERFACE_IP_CMD % eth
                retDevInt = self.DeviceInteract(command=command)
                retCode = retDevInt.get('returnCode')
                retBuff = retDevInt.get('buffer')
                overallBuffer.append(retBuff)
                if retCode != 0:
                    opstestfw.LogOutput('error',
                                        'Failed to execute the command : '
                                        + command)
                    returnCode = 1
                else:
                    opstestfw.LogOutput('debug',
                                        'Successfully executed the command : '
                                        + command)

            if retBuff.find(ipAddr) == -1:
                opstestfw.LogOutput('error',
                                    'IP addr %s is not configured successfully\
                                  on interface %s : '
                                    % (ipAddr, eth))
            else:
                opstestfw.LogOutput('info',
                                    'IP addr %s configured successfully on \
                                  interface %s : '
                                    % (ipAddr, eth))

        bufferString = ""
        for curLin in overallBuffer:
            bufferString += str(curLin)
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode, buffer=bufferString)
        return returnCls

    def Ping(self, **kwargs):
        """
        Ping Method

        This method will be used to ping a destination
        :param ipAddr: destination ip address string
        :type ipAddr: string
        :param ipv6Flag: True to ipv6 / False to ipv4
        :type ipv6Flag: boolean
        :param packetCount: no of echo packets to be sent
        :type packetCount: integer
        :param packetSize: size of the echo packet
        :type packetSize: integer
        :param interface: host network interface to be used
        :type interface: string
        :return: returnStruct Object
        :rtype: object
        """

        ipAddr = kwargs.get('ipAddr')
        ipv6Flag = kwargs.get('ipv6Flag', False)
        packetCount = kwargs.get('packetCount', 10)
        packetSize = kwargs.get('packetSize', 128)
        eth = kwargs.get('interface', 'eth1')

        retStruct = dict()
        retStruct['packets_transmitted'] = 0
        retStruct['packets_received'] = 0
        retStruct['packet_loss'] = 0
        retStruct['time'] = 0
        retStruct['rtt_min'] = 0
        retStruct['rtt_avg'] = 0
        retStruct['rtt_max'] = 0
        retStruct['rtt_mdev'] = 0
        overallBuffer = []
        returnCode = 0
        command = ''
        if ipv6Flag:
            try:
                socket.inet_pton(socket.AF_INET6, ipAddr)
                if ipAddr.find('fe80') == -1:
                    command = 'ping6 %s -c %d -s %d' % (ipAddr, packetCount,
                                                        packetSize)
                else:
                    command = 'ping6 -I %s %s -c %d -s %d' % (eth, ipAddr,
                                                              packetCount,
                                                              packetSize)
            except socket.error:
                returnCode = 1
        else:
            try:
                socket.inet_pton(socket.AF_INET, ipAddr)
                command = 'ping %s -c %d -s %d' % (ipAddr, packetCount,
                                                   packetSize)
            except socket.error:
                returnCode = 1

        if returnCode == 0:
            # Send the command
            ping_timeout = 45
            if packetCount > 30:
                ping_timeout = packetCount + 30
            retDevInt = self.DeviceInteract(command=command,
                                            timeout=ping_timeout)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + command)
            else:
                opstestfw.LogOutput(
                    'info', 'Successfully executed the command : ' + command)

            if retBuff.find('bytes from') == -1:
                returnCode = 1
            else:
                returnCode = 0
        else:
            returnCode = 1

        # Fill out buffer
        bufferString = ""
        for curLin in overallBuffer:
            bufferString += str(curLin)

        # Carve the buffer up to get statistics
        # 10 packets transmitted, 10 received, 0% packet loss, time 8997ms
        # rtt min/avg/max/mdev = 0.342/0.456/0.693/0.096 ms
        for curLine in bufferString.split('\r\n'):
            print curLine
            '''
            statsLine1 = re.match(r'(\d+) packets transmitted,\
                                    (\d+) received,\
                                    (\d+)% packet loss,\
                                    time (\d+)ms', curLine)
            '''
            statsLine1 = re.match(r'(\d+) packets transmitted, (\d+) received, (\d+)% packet loss, time (\d+)ms', curLine)
            if statsLine1:
                retStruct['packets_transmitted'] = int(statsLine1.group(1))
                retStruct['packets_received'] = int(statsLine1.group(2))
                retStruct['packets_errors'] = 0
                retStruct['packet_loss'] = int(statsLine1.group(3))
                retStruct['time'] = int(statsLine1.group(4))
                continue

            statsLine1a = re.match(r'(\d+) packets transmitted, (\d+) received, \+(\d+) errors, (\d+)% packet loss, time (\d+)ms', curLine)
            if statsLine1a:
                retStruct['packets_transmitted'] = int(statsLine1a.group(1))
                retStruct['packets_received'] = int(statsLine1a.group(2))
                retStruct['packets_errors'] = int(statsLine1a.group(3))
                retStruct['packet_loss'] = int(statsLine1a.group(4))
                retStruct['time'] = int(statsLine1a.group(5))
                continue

            statsLine2 = re.match(
                r'rtt min/avg/max/mdev = ([0-9]+\.[0-9]+)/([0-9]\.[0-9]+)/([0-9]+\.[0-9]+)/([0-9]+\.[0-9]+) ms',
                curLine)
            if statsLine2:
                retStruct['rtt_min'] = float(statsLine2.group(1))
                retStruct['rtt_avg'] = float(statsLine2.group(2))
                retStruct['rtt_max'] = float(statsLine2.group(3))
                retStruct['rtt_mdev'] = float(statsLine2.group(4))
                continue

        if returnCode == 1 and retStruct['packets_received'] > 0:
            # this is to make up for where had some failures in the ping
            # but we did get packets through during some of the samples.
            # we will call this a pass.
            returnCode = 0
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString, data=retStruct)
        return returnCls

    def IPRoutesConfig(self, **kwargs):
        """
        IPRoutesConfig Method

        This method will be used to configure route on a interface
        :param config: True to config / False to unconfig interface
        :type config: boolean
        :param destNetwork: destination network address string
        :type destNetwork: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param gateway: gateway address
        :type gateway: string
        :param interface: host network interface to be used
        :type interface: string
        :param metric: route metric to be used
        :type metric: string
        :param ipv6Flag: True to ipv6 / False to ipv4
        :type ipv6Flag: boolean
        :return: returnStruct Object
        :rtype: object
        """

        config = kwargs.get('config', True)
        destNetwork = kwargs.get('destNetwork')
        netMask = kwargs.get('netMask')
        gateway = kwargs.get('gateway', None)
        eth = kwargs.get('interface', 'eth1')
        metric = kwargs.get('metric', None)
        ipv6Flag = kwargs.get('ipv6Flag', False)

        overallBuffer = []

        returnCode = 0

        if config is True:
            routeOperation = "add"
        else:
            routeOperation = "del"

        if routeOperation != 'add' and routeOperation != 'del':
            opstestfw.LogOutput('error', "Invalid route operation : "
                                + routeOperation)
            returnCode = 1

        if ipv6Flag:
            try:
                socket.inet_pton(socket.AF_INET6, destNetwork)
                if destNetwork == '::':
                    route_command = 'ip -6 route %s %s via \
                                  %s' % (routeOperation, 'default', gateway)
                else:
                    route_command = \
                        'ip -6 route %s %s/%d via %s' % (
                            routeOperation,
                            destNetwork,
                            netMask,
                            gateway)
                if metric is not None:
                    route_command += " metric " + metric
            except socket.error:
                opstestfw.LogOutput('error', "Invalid destination "
                                    + destNetwork)
                returnCode = 1
        else:
            try:
                socket.inet_pton(socket.AF_INET, destNetwork)
                if destNetwork == '0.0.0.0':
                    route_command = 'route %s %s gw %s' \
                        % (routeOperation, 'default', gateway)
                    if eth is not None:
                        route_command += ' dev ' + eth
                else:
                    route_command = 'route %s -net %s/%d gw %s' \
                        % (routeOperation, destNetwork, netMask, gateway)
                if metric is not None:
                    route_command += ' metric ' + metric
            except socket.error:
                opstestfw.LogOutput('error', "Invalid destination : "
                                    + destNetwork)
                returnCode = 1

        if returnCode == 0:
            # Send the command
            retDevInt = self.DeviceInteract(command=route_command)
            retCode = retDevInt.get('returnCode')
            retBuff = retDevInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + route_command)
                returnCode = 1
            else:
                opstestfw.LogOutput('info',
                                    'Successfully executed the command : '
                                    + route_command)
        else:
            opstestfw.LogOutput('error', "Invalid IP address")

        bufferString = ""
        for curLin in overallBuffer:
            bufferString += str(curLin)
        returnCls = opstestfw.returnStruct(returnCode=returnCode,
                                           buffer=bufferString)
        return returnCls

    def GetDirectLocalLinkAddresses(self):
        """
        GetDirectLocalLinkAddresses Method

        This method will be used to get host neighbour link local addr
        :return: array of dictionary elements containing interface and address
        :rtype: array
        """

        localLinkDict = dict()
        localLinkElements = []
        command = 'ip -6 neighbour show'

        # Send the command
        retDevInt = self.DeviceInteract(command=command)
        retCode = retDevInt.get('returnCode')
        retBuff = retDevInt.get('buffer')
        if retCode != 0:
            opstestfw.LogOutput('error', 'Failed to execute the command : '
                                + command)
            retBuff = retBuff.split('\n')
        for output in retBuff:
            if re.search('^fe80', output):
                localLinkDict['address'] = output.split(' ')[0]
                localLinkDict['eth'] = output.split(' ')[2]
                localLinkElements.append(localLinkDict.copy())
        return localLinkElements


    def FileTransfer(self, filepath, localpath, direction):
        """
        FileTransfer Method

        This method will be used to transfer file from/to host
        :param filepath: host remote file including the path
        :type filepath: string
        :param localpath: host local file including the path
        :type localpath: string
        :param direction: get/put for getting from or copying to host
        :type direction: string
        :return: returnStruct Object
        :rtype: object
       """

        returnCode = 0
        paramiko.util.log_to_file('/tmp/paramiko.log')
        # Look up and see if we are physical or virtual
        xpathString = ".//reservation/id"
        rsvnEtreeElement = opstestfw.XmlGetElementsByTag(
            self.topology.TOPOLOGY,
            xpathString)
        if rsvnEtreeElement is None:
            # We are not in a good situation, we need to bail
            opstestfw.LogOutput(
                'error', "Could not find reservation id tag in topology")
            return None
        rsvnType = rsvnEtreeElement.text
        if rsvnType != 'virtual':
            # Get the credentials of the workstation from XML file (physical
            # devices)
            xpathString = ".//device[name='" + self.device\
                + "']/connection/ipAddr"
            ipNode = opstestfw.XmlGetElementsByTag(
                self.topology.TOPOLOGY, xpathString)
            if ipNode is None:
                opstestfw.LogOutput('error',
                                    "Failed to obtain IP address for device "
                                    + self.device)
                return None
            hostIP = ipNode.text
            opstestfw.LogOutput(
                'debug',
                self.device +
                " connection IP address:  " +
                hostIP)
            port = 22

            # Open a ssh connection to the host
            transport = paramiko.Transport((hostIP, port))

            # Extract username/password for logging in the workstation
            xpathString = ".//device[name='" + \
                self.device + "']/login/adminPassword"
            password = opstestfw.XmlGetElementsByTag(
                self.topology.TOPOLOGY, xpathString)
            if password is None:
                opstestfw.LogOutput(
                    'error',
                    "Failed to obtain password for device " +
                    self.device)
                return None
            password = password.text
            xpathString = ".//device[name='" + \
                self.device + "']/login/adminUser"
            username = opstestfw.XmlGetElementsByTag(
                self.topology.TOPOLOGY, xpathString)
            if username is None:
                opstestfw.LogOutput(
                    'error',
                    "Failed to obtain username for device " +
                    self.device)
                return None
            username = username.text

            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            # Transfer file
            try:
                if direction == "get":
                    try:
                        sftp.stat(localpath)
                    except IOError as e:
                        #                        if e[0] == 2:
                        opstestfw.LogOutput(
                            "error", "File " + localpath + " not exists")
                        return True
                    sftp.get(localpath, filepath)
                else:
                    sftp.put(filepath, localpath)
            except IOError as e:
                opstestfw.LogOutput(
                    "error", "file not transferred to workstation")
                returnCode = 1
                print e
            # Close a connection
            sftp.close()
            transport.close()
        else:
            opstestfw.LogOutput("info", "Topology is virtual **")
            opstestfw.LogOutput(
                "info", "Copy the files from/to docker container")
            try:
                if direction == "get":
                    command = 'ls ' + localpath
                    retDeviceInt = self.DeviceInteract(
                        command=command, errorCheck=False)
                    retCode = retDeviceInt.get('returnCode')
                    if retCode != 0:
                        opstestfw.LogOutput('error',
                                            'Failed to execute the command : '
                                            + command)
                        returnCode = 1
                    else:
                        opstestfw.LogOutput('info', 'Successfully executed \
                                             the command : '
                                            + command)

                    retBuff = retDeviceInt.get('buffer')
                    if retBuff.find('No such file or directory') == -1:
                        file_tobe_copied = filepath.split('/')[-1]
                        cpCommand = "cp %s /shared/%s" % (
                            localpath, file_tobe_copied)
                        retDeviceInt = self.DeviceInteract(command=cpCommand)
                        retCode = retDeviceInt.get('returnCode')
                        if retCode != 0:
                            opstestfw.LogOutput(
                                'error', 'Failed to execute the command : '
                                + cpCommand)
                            returnCode = 1
                        else:
                            opstestfw.LogOutput('info', 'Successfully \
                                      executed the command : '
                                                + cpCommand)
                        command = "cp %s %s" % (self.topology.testdir + "/"
                                   + self.device.split('_')[1] + "/shared/"
                                   + file_tobe_copied, filepath)
                        os.system(command)
                    else:
                        opstestfw.LogOutput(
                           "error", "File " + localpath + " not exists")
                        return True
                else:
                    #/tmp is a shared folder between VM and docker run instance
                    command = "cp %s %s" % (filepath, self.topology.testdir
                               + "/" + self.device.split('_')[1] + "/shared/")
                    os.system(command)
                    file_tobe_copied = filepath.split('/')[-1]
                    cpCommand = "cp /shared/%s %s" % (
                        file_tobe_copied, localpath)
                    retDeviceInt = self.DeviceInteract(command=cpCommand)
                    retCode = retDeviceInt.get('returnCode')
                    if retCode != 0:
                        opstestfw.LogOutput(
                            'error', 'VSI : Failed to execute the command : '
                            + cpCommand)
                        returnCode = 1
                    else:
                        opstestfw.LogOutput('info', 'VSI : Successfully \
                                  executed the command : '
                                            + cpCommand)
            except IOError as e:
                opstestfw.LogOutput(
                    "error", "file not transferred from/to workstation")
                returnCode = 1
                print e
            if returnCode != 0:
                opstestfw.LogOutput(
                    'error',
                    "Failed to copy file to/from device --> " +
                    self.device)
        return returnCode


    def CreateRestEnviron(self):
        """
        CreateRestEnviron Method

        This method will be used to create REST environment on the host
        :return: returnStruct Object
        :rtype: object
        """

        returnCode = 0
        overallBuffer = []
        opstestfw.LogOutput("info", "Creating HostRestEnvironment")
        tarCommand = "cd " + self.fwbase + "; tar -cvzf " + \
            self.fwbase + "/restEnv/rest.tar.gz restEnv"
        os.system(tarCommand)
        self.FileTransfer(
            self.fwbase +
            "/restEnv/rest.tar.gz",
            "/root/rest.tar.gz",
            "put")
        cdCommand = "cd /root"
        retDeviceInt = self.DeviceInteract(command=cdCommand)
        tarCommand = "tar -xvzf /root/rest.tar.gz"
        retDeviceInt = self.DeviceInteract(command=tarCommand)
        retCode = retDeviceInt.get('returnCode')
        retBuff = retDeviceInt.get('buffer')
        overallBuffer.append(retBuff)
        if retCode != 0:
            opstestfw.LogOutput('error', 'Failed to execute the command : '
                                + tarCommand)
            returnCode = 1
        else:
            opstestfw.LogOutput('info',
                                'Successfully executed the command : '
                                + tarCommand)
        opstestfw.LogOutput("info", "Successful in CreateHostRestInfra")
        bufferString = ""
        for curLin in overallBuffer:
            bufferString += str(curLin)
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode, buffer=bufferString)
        return returnCls

    def RestCmd(self, **kwargs):
        """
        RestCmd Method

        This method used to use host as REST client to issue REST request
        :param switch_ip: REST server IP running on the switch
        :type switch_ip: string
        :param url: url or uri of the resource
        :type url: string
        :param method: REST method options POST,GET,PUT and DELETE
        :type method: string
        :param data: JSON data body for POST or PUT
        :type data: string
        :return: returnStruct Object
        :rtype: object
        """

        ip = kwargs.get('switch_ip')
        url = kwargs.get('url')
        method = kwargs.get('method')
        data = kwargs.get('data', None)
        returnCode = 0
        overallBuffer = []
        bufferString = ""
        retStruct = dict()
        try:
            socket.inet_pton(socket.AF_INET, ip)
        except socket.error:
            returnCode = 1
        if returnCode != 1:
            if data is not None:
                with open(self.fwbase + '/restEnv/restdata', 'wb') as f:
                    json.dump(data, f)
                    f.close()
                    self.FileTransfer(
                        self.fwbase +
                        "/restEnv/restdata",
                        "/root/restEnv/restdata",
                        "put")
            restCmd = "python /root/restEnv/resttest.py --ip=%s --url=%s\
                      --method=%s" % (ip, url, method)
            retDeviceInt = self.DeviceInteract(command=restCmd)
            retCode = retDeviceInt.get('returnCode')
            retBuff = retDeviceInt.get('buffer')
            overallBuffer.append(retBuff)
            if retCode != 0:
                opstestfw.LogOutput('error', 'Failed to execute the command : '
                                    + restCmd)
                returnCode = 1
            else:
                opstestfw.LogOutput('info',
                                    'Successfully executed the command : '
                                    + restCmd)
            for curLin in overallBuffer:
                bufferString += str(curLin)

            output = bufferString.split("\n")
            retStruct['http_retcode'] = output[1]
            print "Http Returned Code " + retStruct['http_retcode']
            retStruct['response_body'] = output[4]

        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            buffer=bufferString,
            data=retStruct)
        return returnCls
