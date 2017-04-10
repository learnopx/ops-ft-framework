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
            "topoDevices": "dut01",
            "topoFilters": "dut01:system-category:switch"}

class Test_ft_framework_basics:

    def setup_class(cls):

        # Create Topology object and connect to devices
        Test_ft_framework_basics.testObj = testEnviron(topoDict=topoDict)
        Test_ft_framework_basics.topoObj = \
            Test_ft_framework_basics.testObj.topoObjGet()

    def teardown_class(cls):

        # Terminate all nodes
        Test_ft_framework_basics.topoObj.terminate_nodes()

    def test_ping(self):

        LogOutput('info', "ping over oobm")
#         dut01Obj = self.topoObj.deviceObjGet(device="dut01")
#         dut01Obj.setDefaultContext(context="vtyShell")
#         wrkston01Obj = self.topoObj.deviceObjGet(device="wrkston01")
#         
#         # Configure dut01 magmet interface
#         InterfaceIpConfig(deviceObj=dut01Obj,
#                           interface="mgmt",
#                           addr="140.1.1.1",
#                           mask="24")
#         
#         wrkston01Obj.NetworkConfig(interface=wrkston01Obj.linkPortMapping['lnk01'],
#                                    ipAddr="140.1.1.10",
#                                    netMask="255.255.255.0", broadcast="140.1.1.0")
#         retObj = wrkston01Obj.Ping(ipAddr="140.1.1.1")
#         retObj.printValueString()
        
        

