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


def OvsBridgeConfig(**kwargs):

    """
     Library to create a simple bridge via ovs-vsctl

    :param device    : Device object
    :type  device    : object
    :param action    : config or unconfig
    :type  action    : string
    :param bridge    : bridge name
    :type bridge     : string
    :param ports     : List of ports "1 2 3"
    :type ports      : list
    :param vlanMode  : choices are access, trunk, native-tagged,
                       native-untagged
    :type vlanMode   : string
    :param nativeVlan: for access & native-tagged,  native-untagged,
                       this is the vlan   to set the tag
    :type nativeVlan  : integer
    :param trunkVlans  : list of vlans for trunked mode
    :type trunkVlans  : list
    :return: returnStruct Object
    :returnType: object
    """

    device = kwargs.get('device', None)
    action = kwargs.get('action', 'config')
    bridge = kwargs.get('bridge', 'bridge_normal')
    ports = kwargs.get('ports', None)
    vlanMode = kwargs.get('vlanMode', 'access')
    nativeVlan = kwargs.get('nativeVlan', '1')
    trunkVlans = kwargs.get('trunkVlans', None)

    if device is None:
        retCls = returnStruct(returnCode=1)
        return retCls

    if action == 'config':
        # Commands to configure bridge
        # check to see if the bridge device is defined...
        command = "ovs-vsctl br-exists " + bridge
        devIntRetStruct = device.DeviceInteract(command=command)
        retCode = devIntRetStruct['returnCode']
        if retCode != 0:
            # This means we need to add the bridge
            command = "ovs-vsctl add-br " + bridge
            devIntRetStruct = device.DeviceInteract(command=command)
            retCode1 = devIntRetStruct.get('returnCode')
            if retCode1 != 0:
                LogOutput('error', "Failed to create bridge " + bridge)
                retCls = returnStruct(returnCode=1)
                return retCls
        else:
            LogOutput('debug', "Bridge " + bridge + " exists")

        # Now add ports to the  bridge
        if ports is not None:
            for curPort in ports:
                command = "ovs-vsctl add-port " + bridge + " " + str(curPort)\
                    + " -- set Interface " + str(curPort)\
                    + " user_config:admin=up"
                devIntRetStruct = device.DeviceInteract(command=command)
                retCode = devIntRetStruct['returnCode']
                if retCode != 0:
                    # Failed to add the port to the bridge
                    LogOutput('error',
                              "Failed to add port " + str(curPort)
                              + " to bridge " + bridge)
                    retCls = returnStruct(returnCode=1)
                    return retCls
                else:
                    LogOutput('debug',
                              "Added port " + str(curPort) + " to bridge "
                              + bridge)
                    # Add vlan to port
                if vlanMode == 'access':
                    # configure access mode
                    command = "ovs-vsctl set port " + str(curPort) + " tag="\
                        + str(nativeVlan)
                    devIntRetStruct = device.DeviceInteract(command=command)
                    retCode = devIntRetStruct['returnCode']
                    if retCode != 0:
                        LogOutput('error', "Failed to set vlan tag "
                                  + str(nativeVlan) + " on port "
                                  + str(curPort))
                        retString = returnStruct(returnCode=1)
                        return retString
                    else:
                        LogOutput('debug', "Set port " + str(curPort)
                                  + " tag attribute to " + str(nativeVlan))

                        command = "ovs-vsctl set port " + str(curPort)\
                            + " vlan_mode=access"
                        devIntRetStruct =\
                            device.DeviceInteract(command=command)
                        retCode = devIntRetStruct['returnCode']
                        if retCode != 0:
                            LogOutput('error', "Failed to set port "
                                      + str(curPort)
                                      + " vlan_mode to access")
                            retString = returnStruct(returnCode=1)
                            return retString
                        else:
                            LogOutput('debug', "Set port " + str(curPort)
                                      + " vlan_mode to access")
                elif vlanMode == 'trunk':
                        if trunkVlans is not None:
                            command = "ovs-vsctl set port " + str(curPort)\
                                + " trunks=" + str(trunkVlans)
                        devIntRetStruct =\
                            device.DeviceInteract(command=command)
                        retCode = devIntRetStruct['returnCode']
                        if retCode != 0:
                            LogOutput('error', "Failed to set port "
                                      + str(curPort)
                                      + " trunks to " + str(trunkVlans))
                            retString = returnStruct(returnCode=1)
                            return retString
                        else:
                            LogOutput('debug', "Set port " + str(curPort)
                                      + " trunks=" + str(trunkVlans))

    retCls = returnStruct(returnCode=0)
    return retCls
