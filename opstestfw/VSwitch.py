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
import time
import re
from Topology import Topology
from Device import Device
from opstestfw import *

class VSwitch(Device):

    """
    Virtual Switch Class definition

    This Class defines the switch connections and interface connectivity
    """
    def __init__(self, **kwargs):
        """
        VSwitch init method

        This method will create a VSwitch object that will contain all
        connection information to interact with the device and also contain
        the logical port to physical port mapping information on device
        connectivity

        :param topology: topology dictionary defined in the test case
        :type topology: dictionary
        :param device: device name to create the object
        :type device: string
        :param noConnect:  Boolean to flag not actually connecting to the
                           device
        :type noConnect: boolean
        """
        self.topology = kwargs.get('topology', None)
        self.device = kwargs.get('device', None)
        self.noConnect = kwargs.get('noConnect', False)
        # Lets initialize some member variables
        self.memberDefaults()
        if self.noConnect is False:
            self.Connect()
            self.defaultContextEnter()

    def memberDefaults(self):
        """
        membersDefaults method

        This method just defines the defaults for all the members assocated
        with this method.
        """
        self.expectHndl = None
        self.connectStringBase = "docker exec -ti "
        self.expectList = ['login:\s*$',
                           'root@\S+:.*#\s*$',
                           'bash-[0-9.]+#',
                           '[A-Za-z0-9]+#',
                           '\(config\)#',
                           '\(config-\S+\)#\s*$',
                           'ONIE:/\s+#\s*$',
                           'telnet: Unable to connect to remote host:',
                           'Connection refused',
                           '--More--',
                           'Password:',
                           'switch:~[#$]\s*$',
                           '\(yes/no\)?',
                           '\[y/n\]?',
                           pexpect.EOF,
                           pexpect.TIMEOUT]
        # Device Contexts
        # linux - assumed root
        # vtyShell
        # vtyShellConfig
        self.deviceContext = ""
        self.defaultContext = "linux"
        self.loginUser = "root"
        self.loginPassword = ""
        self.commandErrorCheck = 1

    def setSwitchAuthentication(self, **kwargs):
        self.loginUser = kwargs.get('username', "root")
        self.loginPassword = kwargs.get('password', "")

    def setDefaultContext(self, **kwargs):
        self.defaultContext = kwargs.get('context', "linux")

        #if self.defaultContext != "linux" or self.defaultContext != "vtyShell" or self.defaultContext != "vtyShellConfig":
            # Got an invalid entry, thus set to linux
        #    self.defaultContext = "linux"
        LogOutput('info', "Default switch context = " + self.defaultContext)
        self.defaultContextEnter()

    def defaultContextEnter(self):
        """
        defaultContextEnter method

        This method will get you to the appropriate context needed
        """
        if self.defaultContext == "":
            self.defaultContext = "linux"

        retstruct = None

        if self.defaultContext == "vtyShell":
            if self.deviceContext == "linux":
                retstruct = self.VtyshShell(enter=True)
            elif self.defaultContext == "vtyShellConfig":
                retstruct = self.ConfigVtyShell(enter=False)
        elif self.defaultContext == "linux":
            if self.deviceContext == "vtyShell":
                retstruct = self.VtyshShell(enter=False)
            elif self.defaultContext == "vtyShellConfig":
                retstruct = self.ConfigVtyShell(enter=False)
                retstruct = self.VtyshShell(enter=False)
        elif self.defaultContext == "vtyShellConfig":
            if self.deviceContext == "linux":
                retstruct = self.VtyshShell(enter=True)
                retstruct = self.ConfigVtyShell(enter=True)
            elif self.defaultContext == "vtyShell":
                retstruct = self.ConfigVtyShell(enter=True)
        return retstruct


    def cmdVtysh(self, **kwargs):
        """
        cmdVtysh method

        This method will get the device into a vtysh context, run the command
        specified, and exit the vtysh context.  It will return the output of
        the command

        :param command: command string to execute
        :type command: string
        :return: string buffer from the vty command execution
        :rtype: string
        """
        # Get into the VTYsh
        cmd = kwargs.get('command', None)

        # Get into the VTY Shell
        vtyEnterRet = self.VtyshShell(enter=True)
        retCode = vtyEnterRet.returnCode()
        if retCode != 0:
            LogOutput('error', "Unable to enter vtysh")
            return None
        else:
            LogOutput('debug', "Entered vtysh")

        retStruct = self.DeviceInteract(command=cmd)
        returnCode = retStruct.get('returnCode')
        if returnCode != 0:
            LogOutput('error',
                      "Failed to send command " + cmd + " to "
                      "device " + self.device)
            return None
        returnBuffer = retStruct.get('buffer')
        # Exit vtysh
        vtyExitRet = self.VtyshShell(enter=False)
        retCode = vtyExitRet.returnCode()
        if retCode != 0:
            LogOutput('error', "Unable to exit vtysh")
        else:
            LogOutput('debug', "Exited vtysh")
        returnBuffer = retStruct.get('buffer')
        return returnBuffer

    def Connect(self):
        """
        Connect Method

        This method is used to connect to the VSwitch device.  This is called
        by the init method.
        """
        # Look up the device name in the topology - grab connectivity
        # information
        xpathString = ".//device[name='" + self.device + "']"
        etreeElement = XmlGetElementsByTag(self.topology.TOPOLOGY, xpathString)
        if etreeElement is None:
            # We are not in a good situation, we need to bail
            LogOutput('error',
                      "Could not find device " + self.device + " in topology")
            return None
        # Code for virtual
        # Go and grab the connection name
        xpathString = ".//device[name='" + self.device + "']/connection/name"
        virtualConn = XmlGetElementsByTag(self.topology.TOPOLOGY, xpathString)
        if virtualConn is None:
            LogOutput('error',
                      "Failed to virtual connection for " + self.device)
            return None
        telnetString = self.connectStringBase + self.device + " /bin/bash"
        expectFileString = self.device + ".log"
        ExpectInstance = DeviceLogger(expectFileString)
        expectLogFile = ExpectInstance.OpenExpectLog(expectFileString)
        if expectLogFile == 1:
            LogOutput('error', "Unable to create expect log file")
            exit(1)
        # Opening an expect connection to the device with the specified log
        # file
        LogOutput('debug',
                  "Opening an expect connection to the device with the"
                  " specified log file" + expectFileString)
        self.expectHndl = pexpect.spawn(telnetString,
                                        echo=False,
                                        logfile=DeviceLogger(expectLogFile))
        # self.expectHndl.delaybeforesend = .50

        # Lets go and detect our connection - this will get us to a context
        # we know about
        retVal = self.DetectConnection()
        if retVal is None:
            return None

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
        time.sleep(2)
        connectionBuffer = []
        sanitizedBuffer = ""
        while bailflag == 0:
            index = self.expectHndl.expect(self.expectList,
                                           timeout=30)
            LogOutput('debug', "Index -> " + str(index))
            if index == 0:
                # Need to send login string
                LogOutput("debug", "Login required::")
                self.expectHndl.sendline("root")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 1:
                # logged-in in prompt
                bailflag = 1
                LogOutput("debug", "Root prompt detected:")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 2:
                # Got prompt.  We should be good
                bailflag = 1
                LogOutput("debug", "Root bash prompt detected: Virtual")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 3:
                LogOutput("debug", "vtysh prompt detected: Revert to root")
                self.expectHndl.send('exit\r')
                connectionBuffer.append(self.expectHndl.before)
            elif index == 4:
                LogOutput("debug",
                          "vtysh config prompt detected: Revert to root")
                self.expectHndl.send('exit\r')
                connectionBuffer.append(self.expectHndl.before)
            elif index == 5:
                LogOutput("debug",
                          "vtysh config subcontext prompt detected:"
                          " Revert to root")
                self.expectHndl.send('exit \r')
                connectionBuffer.append(self.expectHndl.before)
            elif index == 6:
                # Got ONIE prompt - reboot and get to where we need to be
                self.expectHndl.sendline("reboot")
                connectionBuffer.append(self.expectHndl.before)
            elif index == 7:
                # Got EOF
                LogOutput('error', "Telnet to switch failed")
                return None
            elif index == 8:
                # Got EOF
                LogOutput('error', "Connection Refused")
                return None
            elif index == 9:
                # Got EOF
                LogOutput('debug', "More prompt")
                self.expectHndl.send(' ')
            elif index == 10:
                # Got EOF
                LogOutput('error', "Telnet to switch failed")
                return None
            elif index == 11:
                # Got a Timeout
                LogOutput('error', "Connection timed out")
                return None
            else:
                connectionBuffer.append(self.expectHndl.before)
        # Append on buffer after
        connectionBuffer.append(self.expectHndl.after)
        self.expectHndl.expect(['$'], timeout=2)
        # Now lets put in the topology the expect handle
        for curLine in connectionBuffer:
            sanitizedBuffer += str(curLine)
        LogOutput('debug', sanitizedBuffer)
        self.deviceContext = "linux"
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
        :param CheckError: Type of error to check CLI for CLI command.
                           ONIE for onie context.
        :type CheckError: string
        :return: dictionary containing returnCode and buffer
        :rtype: dictionary
        """
        command = kwargs.get('command')
        errorCheck = kwargs.get('errorCheck', True)
        ErrorFlag = kwargs.get('CheckError')
        yesPromptResp = kwargs.get('yesPrompt', "yes")
        timeout = kwargs.get('timeout', 120)

        # Local variables
        bailflag = 0
        returnCode = 0
        retStruct = dict()
        retStruct['returnCode'] = 1
        retStruct['buffer'] = []

        # Clear out buffer
        try:
            #LogOutput('debug', "Flushing buffer")
            buf = self.expectHndl.read_nonblocking(128, 0)
            #LogOutput('debug', "Buffer data \n" + buf)
        except pexpect.TIMEOUT:
            # pass
            LogOutput('debug', "Timeout on clear buffer read")
        except pexpect.EOF:
            # pass
            LogOutput('debug', "EOF on clear buffer read")

        # Send the command
        self.expectHndl.send(command)
        self.expectHndl.send('\r')
        # time.sleep(1)
        connectionBuffer = []

        while bailflag == 0:
            index = self.expectHndl.expect(self.expectList,
                                           timeout=timeout)
            LogOutput('debug', "Index ->" + str(index))
            if index == 0:
                # Need to send login string
                self.expectHndl.sendline(self.loginUser)
                connectionBuffer.append(self.expectHndl.before)
            elif index == 1:
                # root prompt
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 2:
                # Got bash prompt - virtual
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 3:
                LogOutput("debug", "vtysh prompt detected")
                ErrorFlag = "CLI"
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 4:
                # Got vtysh config prompts
                LogOutput('debug', "config prompt")
                ErrorFlag = "CLI"
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 5:
                # Got vtysh config interface prompts
                LogOutput('debug', "config subcontext prompt")
                ErrorFlag = "CLI"
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 6:
                # Got ONIE prompt - reboot and get to where we need to be
                LogOutput('debug', "Got Onie prompt")
                ErrorFlag = "Onie"
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                break
            elif index == 7:
                # got EOF
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('error', "connection closed to console")
                returnCode = 1
                break
            elif index == 8:
                # got EOF
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('error', "connection closed to console")
                returnCode = 1
                break
            elif index == 9:
                # more prompt
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('debug', "saw more prompt")
                self.expectHndl.send(" \r")
            elif index == 10:
                # Password prompt
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('debug', "saw password prompt")
                #if self.loginUser == "admin":
                #    self.expectHndl.sendline("admin")
                self.expectHndl.sendline(self.loginPassword)
            elif index == 11:
                # Password prompt
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('debug', "saw start shell prompt")
                bailflag = 1
                break
            elif index == 12:
                # yes / no prompt
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                if yesPromptResp == "yes":
                    self.expectHndl.send("yes")
                else:
                    self.expectHndl.send("no")
                self.expectHndl.send("\r")
                break
            elif index == 13:
                # y/n prompt
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                if yesPromptResp == "yes":
                    self.expectHndl.send("y")
                else:
                    self.expectHndl.send("n")
                self.expectHndl.send("\r")
                break
            elif index == 14:
                # got EOF
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('error', "connection closed to console")
                returnCode = 1
                exit(105)
                break
            elif index == 15:
                # got Timeout
                bailflag = 1
                connectionBuffer.append(self.expectHndl.before)
                LogOutput('error', "command timeout")
                returnCode = 1
                break
            else:
                connectionBuffer.append(self.expectHndl.before)
        # Move collecting after buffer until after we flush the buffer
        # connectionBuffer.append(self.expectHndl.after)
        self.expectHndl.expect(['$'], timeout=0.05)
        connectionBuffer.append(self.expectHndl.before)
        connectionBuffer.append(self.expectHndl.after)
        #LogOutput('debug',
        #          "Index = " + str(index) + " Command = " + command
        #          + "\nOutput\n" + str(connectionBuffer))
        self.santString = ""
        for curLine in connectionBuffer:
            self.santString += str(curLine)

        # Error Check routine identification
        # There are seperate Error check libraries for CLI,OVS and
        # REST commands.
        # The following portion checks for Errors for OVS commands
        #if errorCheck is True and returnCode == 0 and ErrorFlag is None:
            # Dump the buffer the the debug log
        LogOutput('debug',
                  "Sent and received from "
                  "device: \n" + self.santString + "\n")
        # The following portion checks for Errors in CLI commands
        if self.commandErrorCheck == 1:
            if ErrorFlag == 'CLI':
                LogOutput('debug', "Doing error check for CLI prompt in vtysh")
                errCheckRetStr = self.ErrorCheckCLI(buffer=self.santString)
                returnCode = errCheckRetStr['returnCode']
            if ErrorFlag == 'Onie':
                errCheckRetStr = self.ErrorCheckOnie(connection=self.expectHndl,
                                                     buffer=self.santString)
                returnCode = errCheckRetStr['returnCode']
                LogOutput('debug', "Doing error check for Onie prompt")

        # Special Logic for Segmentation Faults
        if returnCode == 14:
            assert False, "Received a Segmentation Fault during sending cmd " +\
                str(command)
        # Return dictionary
        #LogOutput('debug', "Sent and received from "
        #          "device: \n" + self.santString + "\n")
        retStruct['returnCode'] = returnCode
        retStruct['buffer'] = self.santString
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

        retStruct = dict()
        retStruct['returnCode'] = returnCode

        # Set up the command for error check
        command = "echo $?"
        buffer = ""
        self.expectHndl.send(command)
        self.expectHndl.send('\r')

        index = self.expectHndl.expect(['root@\S+:.*#\s*$',
                                        'bash-\d+.\d+#\s*$'], timeout=200)
        if index == 0 or index == 1:
            buffer += self.expectHndl.before
            buffer += self.expectHndl.after
        else:
            LogOutput('error',
                      "Received timeout in opstestfw.switch.ErrorCheck")
            retStruct['returnCode'] = 1
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

    def ErrorCheckCLI(self, **kwargs):
        """
        ErrorCheckCLI Method

        This method is used to do error checking specifically over the switch
        CLI.
        :param buffer: buffer string from self.DeviceInteract to get checked
        :type buffer: string
        """
        self.buffer = kwargs.get('buffer')
        # Local variables
        returnCode = 0
        returnDict = dict()
        returnDict['returnCode'] = returnCode
        bufferSplit = self.buffer.split("\n")
        for line in bufferSplit:
            # Enter a error code for every failure
            # Error codes correspond to errors in expect buffer interactions
            # with switch
            Error_Code1 = re.match(".*(command not found)", line, re.I)
            if re.match(".*(command not found)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code1.group(1))
                returnCode = 2
            Error_Code2 = re.match(".*(Unknown command)", line, re.I)
            if re.match(".*(unknown command)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code2.group(1))
                returnCode = 3
            Error_Code3 = re.match(".*(Command incomplete)", line, re.I)
            if re.match(".*(Command incomplete)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code3.group(1))
                returnCode = 4
            Error_Code4 = re.match(".*(LAG\s+port\s+doesn't\s+exist)",
                                   line, re.I)
            if re.match(".*(LAG\s+port\s+doesn't\s+exist)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code4.group(1))
                returnCode = 5
            Error_Code5 = re.match(".*(no\s+matched\s+command)",
                                   line, re.I)
            if re.match(".*(no\s+matched\s+command)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code5.group(1))
                returnCode = 6
            #ssh error codes
            Error_Code7 = re.match(".*(Permission denied)",
                                   line, re.I)
            if re.match(".*(Permission denied)", line, re.I):
                LogOutput("error",
                          "Error detected--->" + Error_Code7.group(1))
                returnCode = 7 
            #User add/remove error codes
            Error_Code8 = re.match(".*(user [A-Za-z0-9]+ already exists)",
                                   line, re.I)
            if Error_Code8:
                LogOutput("error",
                          "Detected--->" + Error_Code8.group(1))
                returnCode = 8
            Error_Code9 = re.match(".*(Passwords do not match)",
                                   line, re.I)
            if Error_Code9:
                LogOutput("error",
                          "Detected--->" + Error_Code9.group(1))
                returnCode = 9
            Error_Code10 = re.match(".*(Unknown user:)",
                                   line, re.I)
            if Error_Code10:
                LogOutput("error",
                          "Detected--->" + Error_Code10.group(1))
                returnCode = 10
            Error_Code11 = re.match(".*(Cannot delete the last user:)",
                                   line, re.I)
            if Error_Code11:
                LogOutput("error",
                          "Detected--->" + Error_Code11.group(1))
                returnCode = 11
            Error_Code12 = re.match(".*(user [A-Za-z0-9_]+ is currently used by process)",
                                   line, re.I)
            if Error_Code12:
                LogOutput("error",
                          "Detected--->" + Error_Code12.group(1))
                returnCode = 12
            Error_Code13 = re.match(".*(Cannot add more interfaces to LAG. Maximum interface count is reached)",
                                   line, re.I)
            if Error_Code13:
                LogOutput("error",
                          "Detected--->" + Error_Code13.group(1))
                returnCode = 13
            Error_Code14 = re.match("Segmentation fault", line, re.I)
            if Error_Code14:
                returnCode = 14


        returnDict['returnCode'] = returnCode
        return returnDict

    def Reboot(self, **kwargs):
        """
        Reboot Method

        This method is there to reboot the switch.  In the virtual switch,
        we cannot technically reboot it.  This will always pass.
        """
        LogOutput('info', "Reboot not supported for Virtual Switch")
        pass

    def VtyshShell(self, **kwargs):
        """
        VtyshShell Method

        This method will get the device into the vtysh context or exit the
        context

        :param enter: boolean True to enter, False to exit
        :type enter: boolean
        :returnType: returnStruct Class
        :rtype: object
        """
        # Parameters
        # we are not advertising configOption as a parameter since it is
        # being deprecated.
        configOption = kwargs.get('configOption', "config")
        option = kwargs.get('enter', True)
        # Transitioning away from configOption, so option will always override
        if option is True:
            configOption = "config"
        else:
            configOption = "unconfig"
        # returnDict = dict()
        overallBuffer = []
        if configOption == "config" or option is True:
            if self.deviceContext == "vtyShell":
                # LogOutput('debug', "Already in vtysh context")
                returnCls = returnStruct(returnCode=0)
                return returnCls
            if self.deviceContext == "linux":
                # Enter vtysh shell when configOption is config
                command = "vtysh"
                # LogOutput("debug", "Enter vtysh Shell***")
                # Get the device response buffer as json return structure here
                devIntRetStruct = self.DeviceInteract(command=command,
                                                      CheckError='CLI')
                returnCode = devIntRetStruct.get('returnCode')
                overallBuffer.append(devIntRetStruct.get('buffer'))
                if returnCode != 0:
                    LogOutput('error', "Failed to get into the vtysh shell")
                    bufferString = ""
                    for curLine in overallBuffer:
                        bufferString += str(curLine)
                    returnCls = returnStruct(returnCode=returnCode,
                                             buffer=bufferString)
                    return returnCls
                self.deviceContext = "vtyShell"
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
            returnCls = returnStruct(returnCode=0, buffer=bufferString)
            return returnCls
        else:
            if self.defaultContext == "vtyShell":
                returnCls = returnStruct(returnCode=0)
                return returnCls

            # Exit vtysh shell
            # LogOutput("debug", "Vtysh shell Exit")
            command = "exit"
            # Get the device response buffer as json return structure here
            devIntRetStruct = self.DeviceInteract(command=command,
                                                  CheckError='CLI')
            returnCode = devIntRetStruct.get('returnCode')
            overallBuffer.append(devIntRetStruct.get('buffer'))
            if returnCode != 0:
                LogOutput('error', "Failed to exit the vtysh shell")
                bufferString = ""
                for curLine in overallBuffer:
                    bufferString += str(curLine)
                returnCls = returnStruct(returnCode=returnCode,
                                         buffer=bufferString)
                return returnCls
            self.deviceContext = "linux"
            bufferString = ""
            for curLine in overallBuffer:
                bufferString += str(curLine)
            returnCls = returnStruct(returnCode=returnCode,
                                     buffer=bufferString)
            return returnCls

    def ConfigVtyShell(self, **kwargs):
        """
        ConfigVtyShell Method

        This method is responsible for getting the device in or out of
        the vty config context

        :param enter: boolean True to enter, False to exit
        :type enter: boolean
        :returnType: returnStruct Class
        :rtype: object
        """
        # Parameters
        option = kwargs.get('enter', True)

        overallBuffer = []
        if option is True:
            if self.deviceContext == "vtyShellConfig":
                LogOutput('debug', "Already in vtysh config context")
                returnCls = returnStruct(returnCode=0)
                return returnCls

            if self.deviceContext == "linux":
                # Get into vtyshell
                vtyRetStruct = self.VtyshShell(enter=True)
                retCode = vtyRetStruct.returnCode()
                if retCode != 0:
                    LogOutput('error',
                              "Failed to get into the vtyshell context")
                    returnCls = returnStruct(returnCode=1)
                    return returnCls

            # Validate we are in the vtyShell context
            if self.deviceContext == "vtyShell":

                # Enter vtysh shell when configOption is config
                command = "config terminal\r"
                LogOutput("debug", "Enter vtysh shell config context***")
                # Get the device response buffer as json return structure here
                devIntRetStruct = self.DeviceInteract(command=command,
                                                      CheckError='CLI')
                returnCode = devIntRetStruct.get('returnCode')
                overallBuffer.append(devIntRetStruct.get('buffer'))
                if returnCode != 0:
                    LogOutput('error', "Failed to get into the vtysh shell")
                    bufferString = ""
                    for curLine in overallBuffer:
                        bufferString += str(curLine)
                    returnCls = returnStruct(returnCode=1, buffer=bufferString)
                    return returnCls
                else:
                    self.deviceContext = "vtyShellConfig"
                    bufferString = ""
                    for curLine in overallBuffer:
                        bufferString += str(curLine)
                    returnCls = returnStruct(returnCode=0, buffer=bufferString)
                    return returnCls
        else:
            if self.defaultContext == "vtyShellConfig":
                returnCls = returnStruct(returnCode=0)
                return returnCls

            if self.deviceContext == "vtyShellConfig":
                # Exit vtysh shell
                LogOutput("debug", "vtysh config context exit")
                command = "exit\r"
                devIntRetStruct = self.DeviceInteract(command=command,
                                                      CheckError='CLI')
                returnCode = devIntRetStruct.get('returnCode')
                overallBuffer.append(devIntRetStruct.get('buffer'))
                if returnCode != 0:
                    LogOutput('error', "Failed to exit the vtysh shell")
                    bufferString = ""
                    for curLine in overallBuffer:
                        bufferString += str(curLine)
                    returnCls = returnStruct(returnCode=returnCode,
                                             buffer=bufferString)
                    return returnCls
                self.deviceContext = "vtyShell"
                bufferString = ""
                for curLine in overallBuffer:
                    bufferString += str(curLine)
                returnCls = returnStruct(returnCode=returnCode,
                                         buffer=bufferString)
                return returnCls
            else:
                if self.deviceContext == "vtyShell":
                    bufferString = ""
                    for curLine in overallBuffer:
                        bufferString += str(curLine)
                    returnCls = returnStruct(returnCode=returnCode,
                                             buffer=bufferString)
                    return returnCls
