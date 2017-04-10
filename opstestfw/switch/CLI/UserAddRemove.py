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
import pexpect
import time


def UserAddRemove(** kwargs):
    """
    Library function to add / remove user on switch
    The function also changes password for an existing user

    :param deviceObj : Device object
    :type  deviceObj : object
    :param action  : add - adds user(default)
                   : password - changes password of an existing user
                   : remove  - removes local user on switch
    :type action  : string

    :param user : username
    :type user  : string

    :param password : password string
    :type password  : string

    :return: returnStruct Object
    :returnType: object

    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    action = kwargs.get('action', "add")
    user = kwargs.get('user', "user1")
    password = kwargs.get('password', "openswitch")
    # Variables
    bufferString = ''
    overallBuffer = []
    returnCode = 0
    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device to configure")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson

    # Get into vtyshell
    returnStructure = deviceObj.VtyshShell(enter=True)
    overallBuffer.append(returnStructure.buffer())
    returnCode = returnStructure.returnCode()
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode, buffer=bufferString)
        return returnCls

    expectList = ['Enter password:',
                  'Confirm password:',
                  '[A-Za-z0-9]+#',
                  'User added successfully',
                  'Enter new password:',
                  'Confirm new password:',
                  pexpect.EOF,
                  pexpect.TIMEOUT]
    # Add user block
    time.sleep(1)
    # Clear out buffer
    try:
        buf = deviceObj.expectHndl.read_nonblocking(128, 0)
    except pexpect.TIMEOUT:
        pass
    except pexpect.EOF:
        pass

    if action == "add":
        command = 'user add ' + user
        opstestfw.LogOutput(
            'debug', "Adding user %s on the device :%s  " % (user, deviceObj.device))
        deviceObj.expectHndl.sendline(command)
        index = deviceObj.expectHndl.expect(expectList,
                                            timeout=5)
        bufferString += str(deviceObj.expectHndl.before)
        # Entering passwords for the user
        if index == 0:
            command = password
            deviceObj.expectHndl.sendline(command)
            index = deviceObj.expectHndl.expect(expectList, timeout=5)
            if index == 1:
                command = password
                deviceObj.expectHndl.sendline(command)
                bufferString += str(deviceObj.expectHndl.before)
                index = deviceObj.expectHndl.expect(
                    expectList, timeout=5)
                if index == 3:
                    opstestfw.LogOutput(
                        "info", "User : %s added successfully on device %s **" %
                        (user, deviceObj.device))
        elif index == 6:
            # Got EOF
            opstestfw.LogOutput('error', "End of File")
            return None
        elif index == 7:
            # Got a Timeout
            opstestfw.LogOutput('error', "Connection timed out")
            return None
    elif action == "password":
        # Password change
        opstestfw.LogOutput("info", "Password Change ***")
        command = "password " + str(user)
        deviceObj.expectHndl.sendline(command)
        index = deviceObj.expectHndl.expect(expectList, timeout=5)
        if index == 4:
            command = password
            deviceObj.expectHndl.sendline(command)
            bufferString += str(deviceObj.expectHndl.before)
            index = deviceObj.expectHndl.expect(
                expectList, timeout=5)
            if index == 5:
                deviceObj.expectHndl.sendline(command)
                bufferString += str(deviceObj.expectHndl.before)
                index = deviceObj.expectHndl.expect(
                    expectList, timeout=5)
                if index == 2:
                    opstestfw.LogOutput(
                        "info", "User : %s password changed successfully on device %s **" %
                        (user, deviceObj.device))
                else:
                    opstestfw.LogOutput(
                        "error", "User : %s password not changed  on device %s **" %
                        (user, deviceObj.device))
    else:
        # Remove user
        opstestfw.LogOutput(
            'info', "remove user %s on device %s" %
            (user, deviceObj.device))
        command = 'user remove ' + user
        opstestfw.LogOutput(
            'debug', "Removing user %s on the device :%s  " % (user, deviceObj.device))
        deviceObj.expectHndl.sendline(command)
        index = deviceObj.expectHndl.expect(expectList,
                                            timeout=5)
        bufferString += str(deviceObj.expectHndl.before)
        if index == 0:
            opstestfw.LogOutPut('info', "User %s removed from DUT " % (user))

    deviceObj.expectHndl.expect(['$'], timeout=5)
    bufferString += str(deviceObj.expectHndl.before)
    bufferString += str(deviceObj.expectHndl.after)

    overallBuffer.append(bufferString)
    for curLine in overallBuffer:
        bufferString += str(curLine)
    errCheckRetStr = deviceObj.ErrorCheckCLI(buffer=bufferString)
    returnCode = errCheckRetStr['returnCode']

    #Compile information to return
    returnCls = opstestfw.returnStruct(
        returnCode=returnCode,
        buffer=overallBuffer)
    return returnCls
