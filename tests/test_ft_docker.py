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

import pytest
from opstestfw.switch.CLI import *
from opstestfw import *

topoDict = {"topoTarget": "dut01",
            "topoDevices": "dut01 wrkston01 wrkston02",
            "topoLinks": "lnk01:dut01:wrkston01,lnk02:dut01:wrkston02",
            "topoFilters": "dut01:system-category:switch,\
                            wrkston01:system-category:workstation,\
                            wrkston01:docker-image:openswitch/ubuntutest,\
                            wrkston02:system-category:workstation"}

def ping_to_switch(dut01, wrkston01):

    # Switch configuration
    retCode = 0
    LogOutput('info', "Configuring Switch to be an IPv4 router")
    retStruct = InterfaceEnable(deviceObj=dut01,
                                enable=True,
                                interface=dut01.linkPortMapping['lnk01'])
    if retStruct.returnCode() != 0:
        LogOutput('error', "Failed to enable port on switch")
        retCode = 1
        assert(False)
    else:
        LogOutput('info', "Successfully enabled port on switch")

    retStruct = InterfaceIpConfig(deviceObj=dut01,
                                  interface=dut01.linkPortMapping['lnk01'],
                                  addr="140.1.1.1",
                                  mask=24,
                                  config=True)

    # Workstation configuration
    LogOutput('info', "Configuring workstations")
    retStruct = wrkston01.NetworkConfig(ipAddr="140.1.1.10",
                                        netMask="255.255.255.0",
                                        broadcast="140.1.1.255",
                                        interface=wrkston01.linkPortMapping['lnk01'],
                                        config=True)
    if retStruct.returnCode() != 0:
        LogOutput('error', "Failed to configure IP on workstation")
        retCode = 1
        assert 1 == 0, "Failed to configure IP on workstation"

    cmdOut = wrkston01.cmd("ifconfig " + wrkston01.linkPortMapping['lnk01'])
    LogOutput('info', "Ifconfig info for workstation 1:\n" + cmdOut)

    cmdOut = dut01.cmdVtysh(command="show run")
    LogOutput('info', "Running config of the switch:\n" + cmdOut)

    LogOutput('info', "Pinging between workstation1 and dut01")
    retStruct = wrkston01.Ping(ipAddr="140.1.1.1")
    if retStruct.returnCode() != 0:
        LogOutput('error', "Failed to ping switch")
        retCode = 1
        assert 1 == 0, "Failed to ping switch"
    else:
        LogOutput('info',
                  "IPv4 Ping from workstation 1 to dut01 return JSON:\n"
                  + str(retStruct.retValueString()))
        packet_loss = retStruct.valueGet(key='packet_loss')
        packets_sent = retStruct.valueGet(key='packets_transmitted')
        packets_received = retStruct.valueGet(key='packets_received')
        LogOutput('info', "Packets Sent:\t" + str(packets_sent))
        LogOutput('info', "Packets Recv:\t" + str(packets_received))
        LogOutput('info', "Packet Loss %:\t" + str(packet_loss))
        if packet_loss != 0:
            LogOutput('error', "Packet loss in the ping was no 0%")
            retCode = 1
            assert 1 == 0, "Packet loss in the ping was no 0%"

    ptosRetStruct = returnStruct(returnCode=retCode)
    return ptosRetStruct

class Test_ft_framework_basics:

    def setup_class(cls):

        # Create Topology object and connect to devices
        Test_ft_framework_basics.testObj = testEnviron(topoDict=topoDict)
        Test_ft_framework_basics.topoObj = \
            Test_ft_framework_basics.testObj.topoObjGet()

    def teardown_class(cls):

        # Terminate all nodes
        Test_ft_framework_basics.topoObj.terminate_nodes()

    def test_reboot_switch(self):

        LogOutput('info', "Reboot the switch")
        dut01Obj = self.topoObj.deviceObjGet(device="dut01")
        #dut01Obj.reboot()

    def test_ping_to_switch(self):

        LogOutput('info', "Configure and ping to switch")
        dut01Obj = self.topoObj.deviceObjGet(device="dut01")
        wrkston01Obj = self.topoObj.deviceObjGet(device="wrkston01")
        wrkston01Obj.commandErrorCheck = 0
        pingSwitchRetStruct = ping_to_switch(dut01Obj, wrkston01Obj)
        if pingSwitchRetStruct.returnCode() != 0:
            LogOutput('error', "Failed to ping to the switch")
            assert 1 == 0, "Failed to ping to the switch"
        else:
            LogOutput('info', "Passed ping to switch test")