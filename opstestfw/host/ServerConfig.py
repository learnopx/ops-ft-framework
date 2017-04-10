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
import pdb

def ServerConfig(** kwargs):
    """
    Library function to configure workstations with server configuration.
    Take a backup of default server files and edit with customized configuration
    when the action = config (default)
    Start the respective service specified for the server (dhcpd/tftp/radiusd)
    When (action = "unconfig") move the backed up files to restore the workstation
    and stop the server services configured.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param serverConfigs : server string to be configured
    :type serverConfigs  : string
    :param serviceConfig : server service configuration
    :type serviceConfig  : string
    :param backupFile    : backup file path for server configuration files
    :type backupFile     : string
    :param serverConfigFile    : Filepath of server configuration files
    :type serverConfigFile   : string
    :param service    : server service to be configured (restart/stop/start)
    :type  service    : string
    :param action     : config(configure server parameters) , "unconfig" (to unconfigure)
    :type  action     : string

    :return: returnStruct Object
    :returnType: object
    """

    # Params
    deviceObj = kwargs.get('deviceObj', None)
    service = kwargs.get('service', None)
    serverConfigFile = kwargs.get('serverConfigFile', None)
    backupFile = kwargs.get('backupFile', None)
    serverConfigs = kwargs.get('serverConfigs', None)
    serviceConfig = kwargs.get('serviceConfig', None)
    action = kwargs.get('action', "config")

    # Variables
    bufferString = ''
    returnCode = 0
    overallBuffer = []
    retDictionary = []

    # If device is not passed, we need error message
    if deviceObj is None:
        opstestfw.LogOutput('error', "Need to pass device to configure")
        returnJson = opstestfw.returnStruct(returnCode=1)
        return returnJson

    # Define the server configuration files depending on the service to be
    # configured/unconfigured
    if service == "dhcpd":
        serverConfigFile = "/etc/dhcp/dhcpd.conf"
        backupFile = "/etc/dhcp/dhcpd_bkup.conf"
    elif service == "tftp" :
        serverConfigFile = "/etc/default/tftpd-hpa"
        backupFile = "/etc/default/tftpd-hpa_bkup"
    #Configuring TFTP server 
    if service == "tftp" :
     #Configure Tftp server configure 
     serverConfigs = """ 'TFTP_USERNAME="'tftp'"\nTFTP_DIRECTORY="'/var/lib/tftpboot'"\nTFTP_ADDRESS="'0.0.0.0:69'"\nTFTP_OPTIONS="'\--secure \-c'"' """
     #Appropriate permissions to the /var/lib/tftpboot directory 
     command = "chmod 777 /var/lib/tftpboot/"
     returnStruct = deviceObj.DeviceInteract(command=command)
     returnCode = returnStruct.get('returnCode')
     buffer = returnStruct.get('buffer')
     if returnCode != 0:
        opstestfw.LogOutput('error', " command %s not send on workstation" %
                            (command))
        returnCls = opstestfw.returnStruct(returnCode=returnCode, buffer=buffer)
        return returnCls
     else:
        opstestfw.LogOutput('info', "command %s executed " %
                            (command))

     command = "sudo chown -R nobody /var/lib/tftpboot/"
     returnStruct = deviceObj.DeviceInteract(command=command)
     returnCode = returnStruct.get('returnCode')
     buffer = returnStruct.get('buffer')
     if returnCode != 0:
        opstestfw.LogOutput('error', " command %s not send on workstation" %
                            (command))
        returnCls = opstestfw.returnStruct(returnCode=returnCode, buffer=buffer)
        return returnCls
     else:
        opstestfw.LogOutput('info', "command %s executed " %
                            (command))

    if action == "config":
    # Configure the server
    # Move the server file and take a backup
        returnStruct = opstestfw.host.MoveFile(
            deviceObj=deviceObj,
            sourceFilePath=serverConfigFile,
            destinationFilePath=backupFile)
        returnCode = returnStruct.returnCode()
        buffer = returnStruct.buffer()
        overallBuffer.append(buffer)
        if returnCode != 0:
            opstestfw.LogOutput(
                'error', "Failed to move file %s on %s ->" %
                (serverConfigFile, deviceObj.device))
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=buffer)
            return returnCls
        else:
            opstestfw.LogOutput(
                'info', "Moved the file %s to %s-->" %
                (serverConfigFile, backupFile))

        # Edit the server file
        returnStruct = opstestfw.host.FileEdit(
            deviceObj=deviceObj,
            stringEdit=str(serverConfigs),
            filename=serverConfigFile)
        returnCode = returnStruct.returnCode()
        buffer = returnStruct.buffer()
        overallBuffer.append(buffer)
        if returnCode != 0:
            opstestfw.LogOutput(
                'error', "Failed to edit server file %s ->" %(serverConfigFile))
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=buffer)
            return returnCls

        # Check the pid and kill the service of it is already running (Residue
        # process should be killed)
        if service is not None:
            if serviceConfig != "stop":
                # Stop the service if it already running
                # Killing the old pid is important , since the service needs to
                # resume newly after configuration edit
                retStruct = opstestfw.host.GetServicePID(
                    deviceObj=deviceObj, service=service)
                retDictionary = retStruct.dataKeys()
                if retDictionary:
                    ProcessID = retStruct.valueGet(key='pid')
                    command = "kill " + ProcessID
                    returnStruct = deviceObj.DeviceInteract(command=command)
                    returnCode = returnStruct.get('returnCode')
                    if returnCode != 0:
                        opstestfw.LogOutput(
                            'error', "running (residue) process for service %s not killed" %
                            (service))
                        returnCls = opstestfw.returnStruct(
                            returnCode=returnCode,
                            buffer=buffer)
                        return returnCls
                    else:
                        opstestfw.LogOutput(
                            'info', "killed the running process for service %s" %
                            (service))
            else:
                opstestfw.LogOutput(
                    'info', "Stop service %s explicitly before starting it after configuration change" %
                    (service))

        # Pass service configurations to workstations and get the PID to check
        # if the service is running/stopped
        if service is not None:
            returnStruct = opstestfw.host.ServicesConfig(
                deviceObj=deviceObj,
                service=service,
                action=serviceConfig)
            returnCode = returnStruct.returnCode()
            buffer = returnStruct.buffer()
            overallBuffer.append(buffer)
            if returnCode != 0:
                opstestfw.LogOutput(
                    'error', "Failed to configure action %s on service %s for %s ->" %
                    (serviceConfig, service, deviceObj.device))
                returnCls = opstestfw.returnStruct(
                    returnCode=returnCode,
                    buffer=buffer)
                return returnCls
            else:
                retStruct = opstestfw.host.GetServicePID(
                    deviceObj=deviceObj, service=service)
                retDictionary = retStruct.dataKeys()
                if (retDictionary and serviceConfig == "start") or (retDictionary and serviceConfig == "restart"):
                    opstestfw.LogOutput(
                        'info', "Service %s --> %s" %
                        (service, serviceConfig))
                elif retDictionary is None and serviceConfig == "stop":
                    opstestfw.LogOutput(
                        'info', "Service %s --> %s" %
                        (service, serviceConfig))
                else:
                    opstestfw.LogOutput(
                        'error', "Service %s --> %s failed" %
                        (service, serviceConfig))
                    returnCls = opstestfw.returnStruct(
                        returnCode=1, buffer=buffer)
                    return returnCls
    else:
        opstestfw.LogOutput(
            'info',
            "Unconfigure Server configurations , restore backup files")
        # Move the backedup config file
        returnStruct = opstestfw.host.MoveFile(
            deviceObj=deviceObj,
            sourceFilePath=backupFile,
            destinationFilePath=serverConfigFile)
        returnCode = returnStruct.returnCode()
        buffer = returnStruct.buffer()
        overallBuffer.append(buffer)
        if returnCode != 0:
            opstestfw.LogOutput(
                'error', "Failed to move backup file %s  on ->" %
                (backupFile, deviceObj.device))
            returnCls = opstestfw.returnStruct(
                returnCode=returnCode,
                buffer=buffer)
            return returnCls

        # Stop the service if it already running
        if service is not None:
            retStruct = opstestfw.host.GetServicePID(
                deviceObj=deviceObj, service=service)
            retDictionary = retStruct.dataKeys()
            if retDictionary:
                ProcessID = retStruct.valueGet(key='pid')
                command = "kill " + ProcessID
                returnStruct = deviceObj.DeviceInteract(command=command)
                returnCode = returnStruct.get('returnCode')
                if returnCode != 0:
                    opstestfw.LogOutput(
                        'error', "Failed to kill %s service while unconfiguring " %
                        (service))
                    returnCls = opstestfw.returnStruct(
                        returnCode=returnCode,
                        buffer=buffer)
                    return returnCls
                else:
                    opstestfw.LogOutput(
                        'info', "Kill %s service while unconfiguring " %
                        (service))

    bufferString = ' '
    for curLine in overallBuffer:
        bufferString += str(curLine)
    # Compile information to return
    returnCls = opstestfw.returnStruct(returnCode=0, buffer=bufferString)
    return returnCls
