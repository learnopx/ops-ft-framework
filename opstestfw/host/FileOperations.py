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


def MoveFile(** kwargs):
    """
    Library function to move files on workstations

    :param deviceObj : Device object
    :type  deviceObj : object
    :param sourceFilePath : Filepath of the file to be moved
    :type sourceFilePath  : string
    :param destinationFilePath : Destination filepath
    :type destinationFilePath  : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    sourceFilePath = kwargs.get('sourceFilePath', None)
    destinationFilePath = kwargs.get('destinationFilePath', None)
    # Variables
    returnCode = 0
    overallBuffer = []

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device to configure")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson

    # Move files on workstation to destination path
    command = "mv -f " + str(sourceFilePath) + " " + str(destinationFilePath)
    returnStruct = deviceObj.DeviceInteract(command=command)
    returnCode = returnStruct.get('returnCode')
    buffer = returnStruct.get('buffer')
    overallBuffer.append(buffer)
    if returnCode != 0:
        opstestfw.LogOutput(
            'error', "Failed to move files %s on %s->" %
            (sourceFilePath, deviceObj.device))
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            buffer=buffer)
        return returnCls
    else:
        opstestfw.LogOutput(
            'info', "Moved the file %s on %s ->" %
            (sourceFilePath, deviceObj.device))

    bufferString = ' '
    for curLine in overallBuffer:
        bufferString += str(curLine)
    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls


def FileEdit(** kwargs):
    """
    Library function to edit/make new files

    :param deviceObj : Device object
    :type  deviceObj : object
    :param stringEdit : File string content
    :type stringEdit  : string
    :param filename : Filepath of the file to be edited
    :type filename  : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    stringEdit = kwargs.get('stringEdit', None)
    filename = kwargs.get('filename', None)
    overallBuffer = []
    command = "echo  " + str(stringEdit) + " > " + filename
    returnStruct = deviceObj.DeviceInteract(command=command)
    returnCode = returnStruct.get('returnCode')
    buffer = returnStruct.get('buffer')
    overallBuffer.append(buffer)
    if returnCode != 0:
        opstestfw.LogOutput(
            'error', "Failed to edit file %s on %s->" %
            (filename, deviceObj.device))
        returnCls = opstestfw.returnStruct(
            returnCode=returnCode,
            buffer=buffer)
        return returnCls
    else:
        opstestfw.LogOutput(
            'info', "Edited file %s on %s->" %
            (filename, deviceObj.device))
    bufferString = ' '
    for curLine in overallBuffer:
        bufferString += str(curLine)
    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
