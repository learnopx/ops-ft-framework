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


def OvsVlanConfig(**kwargs):

    """
     Create a vlan via ovs-vsctl

    :param device    : Device object
    :type  device    : object
    :param action    : config or unconfig
    :type  action    : string
    :param bridge    : bridge name
    :type bridge     : string
    :param vlans     : list of Vlans to add to the bridge "1 10 20"
    :type vlans      : list

    :return: returnStruct Object
    :returnType: object
    """

    device = kwargs.get('device', None)
    action = kwargs.get('action', 'config')
    bridge = kwargs.get('bridge', 'bridge_normal')
    vlans = kwargs.get('vlans', None)

    if device is None or vlans is None:
        retString = returnStruct(returnCode=1)
        return retString

    if action == 'config':
        #   command = "ovs-vsctl add-vlan " + bridge + " " +
        LogOutput("info", "Configuring Vlan over OVS bridge")
        for curVlan in vlans:
            command = "ovs-vsctl add-vlan " + bridge + " " + str(curVlan)\
                + " admin=up"
            # Send command to the switch
            devIntRetStruct = device.DeviceInteract(command=command)
            retCode = devIntRetStruct.get('returnCode')
            buffer = devIntRetStruct.get('buffer')
            if retCode != 0:
                LogOutput('error', "Failed to create vlan " + str(curVlan)
                          + " over bridge " + bridge)
                retString = returnStruct(returnCode=1, buffer=buffer)
                return retString
    else:
        # We are in unconfig
        for curVlan in vlans:
            LogOutput("info", "Unconfiguring Vlan over OVS bridge")
            command = "ovs-vsctl del-vlan " + bridge + " " + str(curVlan)
            # Send command to the switch
            devIntRetStruct = device.DeviceInteract(command=command)
            retCode = devIntRetStruct.get('returnCode')
            buffer = devIntRetStruct.get('buffer')
            if retCode != 0:
                LogOutput('error', "Failed to delete vlan " + str(curVlan)
                          + " over bridge " + bridge)
                retString = returnStruct(returnCode=1, buffer=buffer)
                return retString

    retString = returnStruct(returnCode=0, buffer=buffer)
    return retString
