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
from opstestfw import *
import opstestfw.switch
import time
import re
from Topology import Topology

"""
This is the base class for any device - This gives the test case developer the
ability to connect to the device along with interacting with the device
"""


class Device (object):
    """
    This is the base class for any device.
    """

    def __init__(self, **kwargs):
        """
        Device class object is created and will contain all connection
        information about the device.

        :param topology: Topology dictionary defined in the testcase
        :type topology: dictionary
        :param device: Name of the device
        :type device: string
        """
        self.topology = kwargs.get('topology', None)
        self.device = kwargs.get('device', None)
        self.expectHndl = None
        self.expectList = ['login:\s*$',
                           'root@\S+:.*#\s*$',
                           'bash-\d+.\d+#',
                           pexpect.EOF,
                           pexpect.TIMEOUT]
        self.Connect()

    def cmd(self, cmd):
        """
        Method to allow you to send a command to a device

        :param arg1: Command string
        :type arg1:  string
        :return: string of the output from command execution
        :rtype: string
        """
        retStruct = self.DeviceInteract(command=cmd)
        returnCode = retStruct.get('returnCode')
        if returnCode != 0:
            opstestfw.LogOutput('error',
                                "Failed to send command " + cmd + " to device"
                                + self.device)
            return None
        returnBuffer = retStruct.get('buffer')
        return returnBuffer

    def Connect(self):
        """
        Method to connect to device
        """
        # Look up and see if we are physical or virtual
        xpathString = ".//reservation/id"
        rsvnEtreeElement = XmlGetElementsByTag(self.topology.TOPOLOGY,
                                               xpathString)
        if rsvnEtreeElement is None:
            # We are not in a good situation, we need to bail
            opstestfw.LogOutput('error',
                                "Could not find reservation id tag in topology")
            return None

        rsvnType = rsvnEtreeElement.text

        # Look up the device name in the topology - grab connectivity
        # information
        xpathString = ".//device[name='" + self.device + "']"
        etreeElement = XmlGetElementsByTag(self.topology.TOPOLOGY,
                                           xpathString)
        if etreeElement is None:
            # We are not in a good situation, we need to bail
            opstestfw.LogOutput('error', "Could not find device "
                                + self.device + " in topology")
            return None
        if rsvnType == 'virtual':
            # Code for virtual
            # Go and grab the connection name
            xpathString = ".//device[name='\
                          " + self.device + "']/connection/name"
            virtualConn = XmlGetElementsByTag(self.topology.TOPOLOGY,
                                              xpathString)
            if virtualConn is None:
                opstestfw.LogOutput('error',
                                    "Failed to virtual connection for "
                                    + self.device)
                return None
            telnetString = "docker exec -ti " + self.device + " /bin/bash"
        else:
            # Code for physical
            # Grab IP from etree
            xpthStr = ".//device[name='" + self.device + "']/connection/ipAddr"
            ipNode = XmlGetElementsByTag(self.topology.TOPOLOGY, xpthStr)
            if ipNode is None:
                opstestfw.LogOutput('error',
                                    "Failed to obtain IP address for device "
                                    + self.device)
                return None

            self.ipAddress = ipNode.text
            opstestfw.LogOutput('debug', self.device
                                + " connection IP address:  "
                                + self.ipAddress)

            # Grab Port from etree
            xpathStr = ".//device[name='" + self.device + "']/connection/port"
            portNode = XmlGetElementsByTag(self.topology.TOPOLOGY, xpathStr)
            if portNode is None:
                opstestfw.LogOutput('error',
                                    "Failed to obtain Port for device "
                                    + self.device)
                return None

            self.port = portNode.text
            opstestfw.LogOutput('debug', self.device + " connection port:  "
                                + self.port)

            # Grab a connetion element - not testing this since this should
            # exist since we obtained things before us
            # xpathString = ".//device[name='" + self.device + "']/connection"
            # connectionElement = XmlGetElementsByTag(self.topology.TOPOLOGY,
            #                                        xpathString)

            # Create Telnet handle
            # Enable expect device Logging for every connection
            # Single Log file exists for logging device exchange using pexpect
            # logger.  Device logger  name format :: devicename_IP-Port

            telnetString = "telnet " + self.ipAddress + " " + self.port
            FS = self.device + "_" + self.ipAddress + "--" + self.port + ".log"

            ExpectInstance = opstestfw.ExpectLog.DeviceLogger(FS)
            expectLogFile = ExpectInstance.OpenExpectLog(expectFileString)
            if expectLogFile == 1:
                opstestfw.LogOutput('error',
                                    "Unable to create expect log file")
                exit(1)
            # Opening an expect connection to the device with the specified
            # log file
            opstestfw.LogOutput('debug', "Opening an expect connection to "
                                "the device with the specified log file"
                                + expectFileString)
            if rsvnType == 'virtual':
                logFile = opstestfw.ExpectLog.DeviceLogger(expectLogFile)
                self.expectHndl = pexpect.spawn(telnetString,
                                                echo=False,
                                                logfile=logFile)
                self.expectHndl.delaybeforesend = 1
            else:
                logFile = opstestfw.ExpectLog.DeviceLogger(expectLogFile)
                self.expectHndl = pexpect.spawn(telnetString,
                                                echo=False,
                                                logfile=logFile)

            # Lets go and detect our connection - this will get us to a context
            # we know about
            retVal = self.DetectConnection()
            if retVal is None:
                opstestfw.LogOutput('error', "Failed to detect connection "
                                    "for device - looking to reset console")
                # Connect to the console
                conDevConn = console.Connect(self.ipAddress)
                # now lets logout the port we are trying to connect to
                # print("send logout seq")
                retCode = console.ConsolePortLogout(connection=conDevConn,
                                                    port=self.port)
                if retCode != 0:
                    return None
                console.ConnectionClose(connection=conDevConn)
                # Now retry the connect & detect connection
                logFile = opstestfw.ExpectLog.DeviceLogger(expectLogFile)
                self.expectHndl = pexpect.spawn(telnetString,
                                                echo=False,
                                                logfile=logFile)
                retVal = self.DetectConnection()
            if retVal is None:
                return None

    def DetectConnection(self):
        """
        Method to detect device connections.  This method is only called from
        the self.Connect method.
        """
        bailflag = 0

        self.expectHndl.send('\r')
        time.sleep(2)
        connectionBuffer = []
        sanitizedBuffer = ""
        while bailflag == 0:
            index = self.expectHndl.expect(self.expectList,
                                           timeout=200)
            if index == 0:
                # Need to send login string
                opstestfw.LogOutput("debug", "Login required::")
                self.expectHndl.sendline("root")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 1:
                bailflag = 1
                opstestfw.LogOutput("debug", "Root prompt detected:")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 2:
                # Got prompt.  We should be good
                bailflag = 1
                opstestfw.LogOutput("debug", "Root prompt detected: Virtual")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 3:
                # Got EOF
                opstestfw.LogOutput('error', "Telnet to switch failed")
                return None
            elif index == 4:
                # Got a Timeout
                opstestfw.LogOutput('error', "Connection timed out")
                return None
            else:
                connectionBuffer.append(self.expectHndl.before)
        # Append on buffer after
        connectionBuffer.append(self.expectHndl.after)
        self.expectHndl.expect(['$'], timeout=2)
        # Now lets put in the topology the expect handle
        for curLine in connectionBuffer:
            sanitizedBuffer += curLine
        opstestfw.LogOutput('debug', sanitizedBuffer)
        return self.expectHndl

    def DeviceInteract(self, **kwargs):
        """
        Routine to interact with a device CLI over a connection.

        :param command: command string to send to the device
        :type command: string
        :param errorCheck: boolean to turn on / off error checking
        :type errorCheck: boolean
        :param CheckError:  Type of error to check - CLI / ONIE
        :type CheckError: string
        :return: Dictionary with returnCode and buffer keys
        :rtype: dictionary
        """
        command = kwargs.get('command')
        errorCheck = kwargs.get('errorCheck', True)
        ErrorFlag = kwargs.get('CheckError', None)

        # Local variables
        bailflag = 0
        returnCode = 0
        retStruct = dict()
        retStruct['returnCode'] = 1
        retStruct['buffer'] = []

        # Send the command
        self.expectHndl.send(command)
        self.expectHndl.send('\r')
        time.sleep(1)
        connectionBuffer = []

        while bailflag == 0:
            index = self.expectHndl.expect(self.expectList,
                                           timeout=120)
            if index == 0:
                # Need to send login string
                self.expectHndl.send("root \r")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 1:
                # Got prompt.  We should be good
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 2:
                # Got bash prompt - virtual
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
            elif index == 3:
                # got EOF
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                opstestfw.LogOutput('error', "connection closed to console")
                returnCode = 1
            elif index == 4:
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

        # Error Check routine identification
        # There are seperate Error check libraries for CLI,OVS and REST
        # commands.  The following portion checks for Errors for OVS commands
        if errorCheck is True and returnCode == 0 and ErrorFlag is None:
            # Dump the buffer the the debug log
            opstestfw.LogOutput('debug', "Sent and received from device: \n"
                                + santString + "\n")

        # The following portion checks for Errors in CLI commands
        if ErrorFlag == 'CLI':
            opstestfw.LogOutput('debug', "CLI ErrorCode")
        if ErrorFlag == 'Onie':
            opstestfw.LogOutput('debug', "NEED TO FIX")

        # Return dictionary
        opstestfw.LogOutput('debug', "Sent and received from device: \n"
                            + santString + "\n")
        retStruct['returnCode'] = returnCode
        retStruct['buffer'] = santString
        return retStruct

    def ErrorCheck(self, **kwargs):
        """
        Method for error checking the buffer

        :param buffer: output buffer from self.DeviceInteract to check
        :type buffer: string
        :return: dictionary with returnCode key
        :rtype: dictionary
        """
        buffer = kwargs.get('buffer')
        # Local variables
        returnCode = 0

        retStruct = dict()
        retStruct['returnCode'] = returnCode

        # Set up the command for error check
        command = "echo $?"
        buffer = ""
        self.expectHndl.send(command)
        self.expectHndl.send('\r\n')

        index = self.expectHndl.expect(['root@\S+:.*#\s*$',
                                        'bash-\d+.\d+#\s*$'], timeout=200)
        if index == 0 or index == 1:
            buffer += self.expectHndl.before
            buffer += self.expectHndl.after
        else:
            opstestfw.LogOutput('error',  "Received timeout in "
                                "opstestfw.switch.ErrorCheck")
            retStruct['returnCode'] = 1
            return retStruct

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
