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


def LogoutInbandSshSession(** kwargs):
    """
    Library function to logout/exit from a user initiated 
    inband SSH session
    The device object that must be passed here references the inband ssh session 
    initiated from the workstations . 
 
    :param deviceObj : Device object(Pass the device object of the ssh DUT session)
    :type  deviceObj : object

    :return: returnStruct Object
    :returnType: object

    """
    # Params
    deviceObj = kwargs.get('deviceObj', None)
    # Variables
    bufferString = ''
    overallBuffer = []
    returnCode = 0
    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device object")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson
    expectList = ['\[root@\S+.*\]#',
                 'root@\S+#',
                  pexpect.EOF,
                  pexpect.TIMEOUT]
    # Clear out buffer
    try:
        buf = deviceObj.expectHndl.read_nonblocking(128, 0)
    except pexpect.TIMEOUT:
        pass
    except pexpect.EOF:
        pass

    command = "exit"
    deviceObj.expectHndl.sendline(command)
    index = deviceObj.expectHndl.expect(expectList, timeout=5)
    bufferString += str(deviceObj.expectHndl.before)
    print index
    if index == 0 or index == 1:
       bufferString += str(deviceObj.expectHndl.before)
       opstestfw.LogOutput("info","Logged out from the session **")
    else :
       bufferString += str(deviceObj.expectHndl.before)
       opstestfw.LogOutput("error","Session not logged out**")
       returnCode = 1

    deviceObj.expectHndl.expect(['$'], timeout=2)
    bufferString += str(deviceObj.expectHndl.after)
    overallBuffer.append(bufferString)
    for curLine in overallBuffer:
        bufferString += str(curLine)

    #Compile information to return
    returnCls = opstestfw.returnStruct(
        returnCode=returnCode,
        buffer=overallBuffer)
    return returnCls
