opstestfw Library Reference 
=======

 [TOC]


This is a Library Reference to the opstestfw library set that are in the ops-ft-framework.

## Topology Definition ##
Each test case must have a "topoDict" dictionary defined.  This dictionary describes the way the topology is configured.  Below is an example topology.
```
topoDict = {"topoTarget": "dut01",
			"topoDevices": "dut01 wrkston01 wrkston02",
            "topoLinks": "lnk01:dut01:wrkston01,lnk02:dut01:wrkston02",
            "topoFilters": "dut01:system-category:switch,dut02:system-category:switch"}

```
The names used in the dictionary values should follow this notation..

 - **Switches**:  These should be named "dut0x",  If I have a two switch topology I would call these switches logically dut01 and dut02.
 - **Workstations / Hosts**:  These should be named "wrkston0x".  If I have three workstations in the topology, these should be referred to as wrkston01, wrkston02, and wrkston03.
 - **Links**:  Links aer connections between two entities and should be named in the following way, lnk0x.  If I have three links in my topology they should be named lnk01, lnk02, and lnk03 respectively.

Below is a description of the topoDict key / value pairs.

 - **topoTarget**:  This is identifying in the topology (switches) that will install the build under test.  If I have three switches in the topology, the value would look like "dut01 dut02 dut03".
 - **topoDevices**:  This identifies all the logical devices in the topology.  If I have two switches and three workstations in my topology the value of this would look like "dut01 dut02 wrkston01 wrkston02 wrkston03".
 - **topoLinks**:  This defines the links for the topology and specifies the entities that the link interconnects.  The link definition is delimited by the ":" character.  The notation of a link definition statement is linkname:device1:device2.  Multiple links are delimited by the "," character.  If I had 3 links defined the statement might look like "lnk01:dut01:wrkston01,lnk02:dut01:wrkston02,lnk03:dut01:dut02".  This example states that "lnk01" is a connection between dut01 and wrkston01, "lnk02" is a connection between dut01 and wrkston02, and "lnk03" is a connection between dut01 and dut02.
 - **topoFilters**:  This gives base definition of what each device is.  This is in the form of  "device":"attribute":"value".  The one attribute that is currently accepted today is "system-category" and the value of this is either switch or workstation.
 - **topoLinkFilter**:  This is a filter on the link that can add requirements to a specific link.  For example, if we want to make sure a port is connected to a specific port on the switch you would add it in the following notation <lnkName:>:<device>:interface:<interfaceName>
"topoLinkFilter": "lnk01:dut01:interface:eth0" - this makes sure that lnk01 port on dut01 is over eth0.  This topology key is optional.

## Classes / Objects##
This section will not explain each class in full, but will highlight all the portions of the classes that test case developers might find useful.

All the class libraries can be brought into the environment by the following import statement...
```
	import opstestfw
		or
	from opstestfw import *
```
### testEnviron Class ###
The testEnviron Class is the main class that sets up the testing environment.  Once instantiated, this object will set up the logging infrastucture which includes a summary log, detail log to debug library routine level debugging, and individual device logs.

This class will also initiate the topology build process along with the device console connection process.

This object is to be instantiated in the pytest setup_class method.  The topology dictionary which is defined at the top of the test case is a parameter into the testEnviron class.
```
class Test_suite:
    def setup_class(cls):
        # Create Topology object and connect to devices
        Test_suite.testObj = testEnviron(topoDict=topoDict)
        Test_suite.topoObj = Test_suite.testObj.topoObjGet()
```
Once this class in instantiated, you can retrieve the Topology Object from it.

### Topology Class ###
The Topology class is actually created within the testEnviron object automatically.  This section will describe some methods and members that the test case developer can take advantage of.
#### terminate_nodes() Method####
This is typically called during the pytest teardown_class method.  This will shutdown all topology devices and free up resources
```
def teardown_class(cls):
        # Terminate all nodes
        Test_suite.topoObj.terminate_nodes()
```
#### deviceObjList()####
This method will return all the logical device entities that you can query from the topology.  A list of logical device names as defined in the topoDevice topoDict key.  The device objects can then be referenced by these names.
```
	deviceList = self.topoObj.deviceObjList()
```
#### deviceObjGet()####
This method will return a device object that has been created and ultimately stored in the Topology Object.  
**Arguments**:  *device* - logical name of the device
```
	device1Obj = self.topoObj.deviceObjGet(device="dut01")
```
### Device Class ###
This class is the base class for the VHost and VSwitch Classes.  This section will describe key methods that VHost / VSwitch classes will inherit.
####linkPortMapping Dictionary###
The linkPortMapping Dictionary is a key data structure for each device.  The logical link name is the key into the dictionary.  The result of this query is the physical interface that is associated with that device over that link.

Below is an example of where to use this dictionary...
```
	
	retStruct = InterfaceEnable(deviceObj=dut01,enable=True,
	          interface=dut01Obj.linkPortMapping['lnk01'])
    
```
Notice that in this example,  we do not hardcode an interface name / number into the interface parameter.  When referencing interfaces of a device, this dictionary reference should always be used.
#### cmd() Method ####
The "cmd" method will send a command directly to the interactive console / telnet session of the device and return back the output string

        :param arg1: Command string
        :type arg1:  string
        :return: string of the output from command execution
        :rtype: string

```
	cmdOutput = device1Obj.cmd("ps -ef")
```
The call above will run a process query on the device and return back the output of that command in the cmdOutput variable.
#### DeviceInteract() Method ####
The "DeviceInteract" method like the "cmd" method will send a command to the device over the established connection.  What DeviceInteract does in addition to cmd is to do error checking on the output and to give the calling function a returnCode along with the buffer in a dictionary.  If an error is found, returnCode is returned a 1.  If no error is detected, then a 0 is returned

		:param command: command string to send to the device
        :type command: string
        :param errorCheck: boolean to turn on / off error checking
        :type errorCheck: boolean
        :param CheckError:  Type of error to check - CLI / ONIE
        :type CheckError: string
        :return: Dictionary with returnCode and buffer keys
        :rtype: dictionary
        
```
	returnDict = device1Obj.DeviceInteract(command="ps -ef")
	returnCode = returnDict.get('returnCode')
	
	returnBuffer = returnDict.get('buffer')
```
 
### VHost Class ###
The "VHost" Class inherits the Device Class.  This class is initiated for any workstation in the topology.  We will describe some helpful methods that will be useful to the test case developer.
#### NetworkConfig() ####
This method will configure an IPv4 address over a network interface

        :param interface: network interface to configure address on
        :type interface: string
        :param ipAddr: ip address string
        :type ipAddr: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param broadcast: broadcast address for interface
        :type broadcast: string
        :param config: True to config / False to unconfig interface
        :type config: boolean
        :return: returnStruct Object
        :rtype: object

```
retStructObj = wrksObj.NetworkConfig(ipAddr="140.1.2.10",
				netMask="255.255.255.0",
				broadcast="140.1.2.255",
		        interface=wrkston02.linkPortMapping['lnk02'],
		        config=True)
if retStructObj.returnCode() != 0:
	LogOutput('error', "Failed to configure IP on workstation")
    
```
#### Network6Config() ####
This method will configure an IPv6 address over a network interface

        :param interface: network interface to configure address on
        :type interface: string
        :param ipAddr: ip address string
        :type ipAddr: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param config: True to config / False to unconfig interface
        :type config: boolean
        :return: returnStruct Object
        :rtype: object

```
retStructObj = wrksObj.Network6Config(ipAddr="3ffe:1::10",
				netMask=96,
		        interface=wrkston02.linkPortMapping['lnk02'],
		        config=True)
if retStructObj.returnCode() != 0:
	LogOutput('error', 
			  "Failed to configure IPv6 on workstation")
    
```
#### Ping() ####
The "Ping" method will source a ping from the host to a destination.

        :param ipAddr: destination ip address string
        :type ipAddr: string
        :param ipv6Flag: True to ipv6 / False to ipv4
        :type ipv6Flag: boolean
        :param packetCount: no of echo packets to be sent
        :type packetCount: integer
        :param packetSize: size of the echo packet
        :type packetSize: integer
        :param interface: host network interface to be used
        :type interface: string
        :return: returnStruct Object
        :rtype: object

```
	retStruct = wrk01.Ping(ipAddr="140.1.2.10",packetCoung=10)
    if retStruct.returnCode() != 0:
        LogOutput('error', "Failed to ping")
        retCode = 1
    else:
        LogOutput('info', "IPv4 Ping Succeded")
        packet_loss = retStruct.valueGet(key='packet_loss')
        packets_sent = retStruct.valueGet(key='packets_transmitted')
        packets_received = retStruct.valueGet(key='packets_received')
        LogOutput('info', "Packets Sent:\t"+ str(packets_sent))
        LogOutput('info', "Packets Recv:\t"+ str(packets_received))
        LogOutput('info', "Packet Loss %:\t"+str(packet_loss))
        if packet_loss != 0:
            LogOutput('error', "Packet Loss > 0%")
            retCode = 1
    
```
#### IpRouteConfig() ####
This method will be used to configure route on a interface

        :param config: True to config / False to unconfig interface
        :type config: boolean
        :param destNetwork: destination network address string
        :type destNetwork: string
        :param netMask: network mask string in IP format
        :type netMask: string
        :param gateway: gateway address
        :type gateway: string
        :param interface: host network interface to be used
        :type interface: string
        :param metric: route metric to be used
        :type metric: string
        :param ipv6Flag: True to ipv6 / False to ipv4
        :type ipv6Flag: boolean
        :return: returnStruct Object
        :rtype: object


```
	retStruct = wrkston01.IPRoutesConfig(config=True,
						destNetwork="140.1.2.0",
						netMask=24,
						gateway="140.1.1.1")
    if retStruct.returnCode() != 0:
        LogOutput('error', "Failed to configure IP route")
        retCode = 1
    else:
	    cmdOut = wrkston01.cmd("netstat -rn")
	    LogOutput('info', "IPv4 Route table for workstation 1:\n" + cmdOut)
 
```        
### VSwitch Class ###
The "VSwitch" Class inherits the Device Class.  This class is initiated for any switch in the topology.  We will describe some helpful methods that will be useful to the test case developer.

#### cmdVtySh() ####
This method will get the device into a vtysh context, run the command        specified, and exit the vtysh context.  It will return the output of the command

		:param command: command string to execute
        :type command: string
        :return: string buffer from the vty command execution
        :rtype: string

```
	cmdOut = dut01.cmdVtysh(command="show run")
    LogOutput('info', "Command output \n"+cmdOut)
```
#### VtyShShell() ####
This method will get the device into the vtysh context or exit the context

        :param enter: boolean True to enter, False to exit
        :type enter: boolean
        :returnType: returnStruct Class
        :rtype: object


```
	returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=returnCode,
						        buffer=bufferString)
        return returnCls
```
#### ConfigVtyShell() ####
This method is responsible for getting the device in or out of the vty config context.

        :param enter: boolean True to enter, False to exit
        :type enter: boolean
        :returnType: returnStruct Class
        :rtype: object

```
	returnStructure = deviceObj.ConfigVtyShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        LogOutput('error', "Failed to get vtysh config prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = returnStruct(returnCode=1, buffer=bufferString)
        return returnCls
```
### returnStruct Class ###
The returnStruct Class is the return structure that routines will use to return status, data, and output back to the calling routine.
#### returnCode() method####
The returnCode method will return the integer returnCode member.
```
	retStructRouteCfg = = IpRouteConfig(deviceObj=dut01,
                                      route="140.1.10.0",
                                      mask=24,
                                      nexthop="140.1.2.20") 
	if retStructRouteCfg.returnCode() != 0:
        LogOutput('error', "Failed to configure route")
```
#### buffer() method####
The buffer method will return the buffer member.

```
	output = retStructRouteCfg.buffer()
	LogOutput('info', "Command output = " + output)
```
#### dataKeys() method####
The dataKeys method will return the keys of the dictionary data in the returnStruct object.  This will return a list of keys that are accessible through the top level of the dictionary.  This will not traverse the entire dictionary if there are dictionaries within dictionaries.

#### valueGet() method####
The valueGet method will return value in for the key passed for the data dictionary

        :param key : key from a dictionary, if none is past, data is just
                     passed back
        :type: key : index
        :return: data
        :returnType: string / integer / dictionary

```
	packet_loss = retStruct.valueGet(key='packet_loss')
```

#### retValueString() method####
The retValueString method will return JSON data string.  This will make multi-level dictionaries easy to read.
```
	jsonString = retstruct.retValueString()
	LogOutput('info', 
			"JSON Represntation of data = " + jsonString)
```
#### printValueString() method####
The printValueString method will print returnStruct in JSON string format.  Like the retValueString() routine, this will print the JSON string to standard out.

## Switch Helper Libraries ##
The switch helper libraries are libraries that are designed to have a switch device object passed into it.  This allows the routine to interact with the device and perform the action that needs to be taken.  These libraries can be brought into the test case by doing the following import...

```
	import opstestfw.switch.CLI
		
		or
		
	from opstestfw.switch.CLI import *
```

### VLAN Libraries ###
####AddPortToVlan()####
Library function to add a port to a VLAN.
```
	:param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param interface : Id of the interface to add to the VLAN.
                       Routing will be disabled in the interface.
                       Send here a string "lag X" to add a lag.
    :type interface  : int
    :param access    : True to add access to the command, False to add
                       trunk to the command. Defaults to False.
    :type access     : boolean
    :param allowed   : True to add allowed after trunk, False to add
                       native after trunk. Defaults to False.
    :type allowed    : boolean
    :param tag       : True to add tag after native. False to add nothing.
                       Defaults to False.
    :type tag        : boolean
    :param config    : True if a port is to be added to the VLAN,
                       False if a port is to be removed from a VLAN.
                       Defaults to True.
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
   
```
####AddVlan()####
Library function to add a VLAN.
```
    :param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param config    : True if a port is to be added to the VLAN,
                       False if a port is to be removed from a VLAN.
                       Defaults to True.
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
```
####ShowVlan()####
Library function to show the VLANs.
```
    :param deviceObj : Device object
    :type  deviceObj : object
    :return: returnStruct Object
            buffer
            data keys
                Status - string set to "up" or "down"
                Reserved - string
                Name - string set to the name of the VLAN
                VLAN - string set to the id of the VLAN
                Reason - string
                Ports - list of strings
    :returnType: object
```
####VlanDescription()####
Library function to show the VLANs.
```
    :param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param description : string with the VLAN description. This is casted to
                         string.
    :type description : string
    :param config     : True if a VLAN description is to be added,
                        False if a VLAN description is to be deleted.
                        Defaults to True.
    :return: returnStruct Object
    :returnType: object
```
####VlanStatus()####
Library function to set a VLAN status.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param vlanId    : Id of the VLAN to be added. This is casted to string
                      (optional)
    :type  vlanId    : integer
    :param status    : True to set the status to up, False to set the status
                       to down
    :return: returnStruct Object
    :returnType: object

### Interface Libraries ###
#### InterfaceEnable() ####
Library function enable / disable interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface number context (optional)
    :type  interface : integer
    :param vlan      : vlan id (optional)
    :type  vlan      : integer
    :param lag       : lag id (optional)
    :type  lag       : integer
    :param enable    : True to enable interface, vlan or lag
                       False to disable interface, vlan or lag
                       Defaults to True
    :type enable     : boolean
    :return: returnStruct Object
    :returnType: object
#### InterfaceIpConfig()####
Library function configure IPv4 / IPv6 address on an interface, vlan,
    or lag

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface number context (optional)
    :type  interface : integer
    :param vlan      : vlan id (optional)
    :type  vlan      : integer
    :param lag       : lag id (optional)
    :type  lag       : integer
    :param addr      : address string for IPv4 or IPv6 address
    :type addr       : string
    :param mask      : subnet mask bit
    :type maks       : int
    :param secondary : True for secondary address, False for not
    :type secondary  : boolean
    :param config    : True to configure address
                       False to unconfigure address
                       Defaults to True
    :type config     : boolean
    :return: returnStruct Object
    :returnType: object
####InterfaceStatisticsShow()####
Library function get statistics for an specific interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer

    :return: returnStruct Object
                 data:
                   RX: inputPackets,inputErrors,shortFrame,CRC_FCS,bytes,
                       dropped,overrun
                   TX: outputPackets,inputError,collision,bytes,dropped

    :returnType: object

### Routing Table Libraries ###
####IpRouteConfig() ####
Library function configure IPv4 or IPv6 address on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param route     : route address to configure
    :type  route     : string
    :param ipv6flag  : True for IPv6, False is IPv4.  Default is False
    :type  ipv6flag  : boolean
    :param mask      : subnet mask bits
    :type  mask      : integer
    :param nexthop   : Can be an ip address or a interface
    :type  nexthop   : string
    :param config    : True to configure, False to unconfigure
    :type  config    : boolean
    :param metric    : route address to configure
    :type  metric    : integer

    :return: returnStruct Object
    :returnType: object

### LAG / LACP Libraries ###
####InterfaceLacpAggKeyConfig()####
Library function to configure LAG parameters on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer
    :param lacpAggKey: Range betwen 1 and 65535. Key used to identify all
                       members of LAG to be of the same 2 switches.
    :type  lacpAggKey: integer
    :return: returnStruct Object
    :returnType: object
 
 

####InterfaceLacpPortIdConfig()####
Library function to configure LAG parameters on an interface

    :param deviceObj: device object
    :type deviceObj:  VSwitch device object
    :param interface: interface to config
    :type interface: int
    :param lacpPortId: Range beteen 1 and 65535 to identify port in LACP
    :type lacpPortId: int
    :return: returnStruct object
    :rtype: object
 
####InterfaceLacpPortPriorityConfig()####
Library function to configure LAG parameters on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer
    :param lacpPortPriority: Range between 1 and 65535 to assign priority of
                             interface between members of same dynamic
                             LAG (LACP)
    :type  lacpPortPriority: integer
    :return: returnStruct Object
    :returnType: object

####InterfaceLagIdConfig()####
Library function to configure LAG parameters on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer
    :param lacpPortPriority: Range between 1 and 65535 to assign priority of
                             interface between members of same dynamic
                             LAG (LACP)
    :type  lacpPortPriority: integer
    :return: returnStruct Object
    :returnType: object

####InterfaceLagShow()####
    Library function to configure LAG parameters on an interface

    :param deviceObj : Device object
    :type  deviceObj : object
    :param interface : interface to configure
    :type  interface : integer

    :return: returnStruct Object
                 data:
                     "localPort":  "lagId","systemId","portId","key",
                                   "activeFlag","shortTimeFlag",
                                   "collectingFlag","stateExpiredFlag",
                                   "passiveFlag","longTimeOutFlag",
                                   "distributingFlag","aggregableFlag",
                                   "inSyncFlag","neighborStateFlag",
                                   "individualFlag","outSyncFlag"
                     "remotePort":"lagId","systemId","portId","key",
                                   "activeFlag","shortTimeFlag",
                                   "collectingFlag","stateExpiredFlag",
                                   "passiveFlag","longTimeOutFlag",
                                   "distributingFlag","aggregableFlag",
                                   "inSyncFlag","neighborStateFlag",
                                   "individualFlag","outSyncFlag"
    :returnType: object

####LacpAggregatesShow()####
Library function to display settings configured on 1 or several LAGs

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG identifier
    :type  lagId     : integer

    :return: returnStruct Object
             data
                Keys: LAG numeric identifier
                Values:
                      interfaces:   - List of interfaces part of LAG
                      lacpFastFlag: - True for fast heartbeat,
                                      False for slow heartbeat
                      fallbackFlag: - True when enabled, False otherwise
                      hashType:     - l2-src-dst/l3-src-dst depending on
                                      configured settings on LAG
                      lacpMode:     - LAG configured mode: off for static and
                                      active/passive for dynamic
    :returnType: object

####lagCreation()####
Library function to create/delete a LAG

    :param deviceObj: device object
    :type deviceObj:  VSwitch device object
    :param lagId: LAG identifier
    :type lagId: int
    :param configFlag: True for configuration / False for removing LAG
    :type configFlag: boolean
    :return: returnStruct object
    :rtype: object

####lagFallback()####
Library function to configure fallback settings for a LAG working in
    dynamic mode

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG Identifier
    :type  lagId     : integer
    :param fallbackFlag :  off: Static LAG
                           active: Active dynamic LAG
                           passive: Passive dynamic LAG
    :type  fallbackFlag : string

    :return: returnStruct Object
    :returnType: object

####lagHash()####
Library function to configure fallback settings for a LAG working in
    dynamic mode

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG Identifier
    :type  lagId     : integer
    :param hashType  : l2-src-dst/l3-dsrc-dst hashing algortihms
    :type  hashType  : string

    :return: returnStruct Object
    :returnType: object

####lagHeartbeat()####
Library function to configure heartbeat speed on a LAG

    :param deviceObj: device object
    :type deviceObj:  VSwitch device object
    :param lagId: LAG identifier
    :type lagId: int
    :param lacpFastFlag: True for LACP fast heartbeat, false for slow heartbeat
    :type lacpFastFlag: boolean
    :return: returnStruct object
    :rtype: object

####lagMode()####
Library function to configure a LAGs mode (static/dynamic)

    :param deviceObj : Device object
    :type  deviceObj : object
    :param lagId     : LAG Identifier
    :type  lagId     : integer
    :param lacpMode  : off: Static LAG
                       active: Active dynamic LAG
                       passive: Passive dynamic LAG
    :type  lacpMode  : string

    :return: returnStruct Object
    :returnType: object

####lagpGlobalSystemID()####
Function to configure Global LACP system ID

    :param deviceObj : Device object
    :type  deviceObj : object
    :param systemID  : Identification Default is system MAC address,
                       can be changed for another one
    :type  systemID  : string
    :param configure : (Optional -Default is True)
                       True to configure,
                       False to unconfigure
    :type  configure : boolean

    :return: returnStruct Object
    :returnType: object

####lagpGlobalSystemPriority()####
Function to configure Global LACP system Priority

    :param deviceObj : Device object
    :type  deviceObj : object
    :param systemPriority  : Identification Default is system MAC address,
                             can be changed for another one
    :type  systemPriority  : string
    :param configure : (Optional -Default is True)
                       True to configure,
                       False to unconfigure
    :type  configure : boolean

    :return: returnStruct Object
    :returnType: object

####lagpGlobalSystemShow()####
Function to extract Global LACP configuration

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
         data    dictionary with the following keys/values
                 System-id = <int>
                 System-priority = <int> [0-65534]
    :returnType: object

### LLDP Libraries ###
####LldpConfig()####
The library configures LLDP on switches

    :param device : Device Object
    :type device  : object
    :param enable : string (configures if enable,unconfigures in other case)
    :type enable  : string

    :return: returnStruct Object
    :returnType: object

####LldpInterfaceConfig()####
Interface level configuration for LLDP

    :param deviceObj : Device Object
    :type deviceObj  : object
    :param interface : Switch Interface
    :type interface  : integer
    :param transmission : Enables transmission when True
    :type transmission  : Boolean
    :param reception : enables reception when True
    :type reception  : Boolean

    :return: returnStruct Object
    :returnType: object

####ShowLldpNeighborInfo()####
This routine shows LLDP neighbor information on a switch

    :param deviceObj : Device object
    :type  deviceObj : object
    :param port      : Device port (optional)
    :type  port      : integer
    :return: returnStruct Object
             portStats - dictionary of ports, each port is a dictionary
                     portKeys - Neighbor_Entries_Deleted,
                                Neighbor_Entries_Dropped
                                Neighbor_Entries
                                Neighbor_Chassis-ID
                                Neighbor_chassisName
                                Neighbor_chassisDescription
                                Chassis_Capabilities_Available
                                Neighbor_Port-ID
                                Chassis_Capabilities_Enabled
                                TTL
             globalStats - dictionary of global statistics
                                Total_Neighbor_Entries
                                Total_Neighbor_Entries_Aged-out
                                Total_Neighbor_Entries_Deleted
                                Total_Neighbor_Entries_Dropped
    :returnType: object

## Host Helper Libraries ##
The helper helper libraries are libraries that are designed to have a workstation / host device object passed into it.  This allows the routine to interact with the device and perform the action that needs to be taken.  These libraries can be brought into the test case by doing the following import...

```
		import opstestfw.host
		
				or
		
		from opstestfw.host import *
```
### Iperf Libraries ###
####hostIperfClientStart()####
Library function to generate traffic using iperf.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param time    : amount of time in seconds where traffic will be sent
    :type  time    : integer
    :param protocol : UDP or TCP
    :type protocol  : string
    :param interval : Result reporting interval
    :type interval  : integer
    :param port   : server port number
    :type port    : integer

    :return: returnStruct Object
    :returnType: object

####hostIperfClientStop()####
Library function to stop traffic using iperf.

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
        data: - Dictionary:
               'Client IP': Server IP address
               'Client port': Client port
               'Server IP': Server IP address
               'Server port': Server port
    :returnType: object

####hostIperfServerStart()####
Library function to receive traffic using iperf.

    :param deviceObj : Device object
    :type  deviceObj : object
    :param protocol : UDP or TCP
    :type protocol  : string
    :param interval : Result reporting interval
    :type interval  : integer
    :param port   : server port number
    :type port    : integer

    :return: returnStruct Object
        data: - Dictionary:
               'Client IP': Server IP address
               'Client port': Client port
               'Server IP': Server IP address
               'Server port': Server port
    :returnType: object

####hostIperfServerStop()####
Library function to process stop iperf server.

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
        data: - Dictionary:
               'Client IP': Server IP address
               'Client port': Client port
               'Server IP': Server IP address
               'Server port': Server port
    :returnType: object

## Additional Libraries ##
The additional libraries are accessed by importing the following...
```
	import opstestfw
		
			or

	from opstestfw import *
```

####GetLinuxInterfaceIp()####
Library function to get the IP address on an eth0 interface

    :param deviceObj : Device object
    :type  deviceObj : object

    :return: returnStruct Object
    :returnType: object

####LogOutput()####
Library routine to write the logger message to stdout along with dest
    log file

    :param arg1 : dest
    :type  arg1 : string
    :param arg2 : message
    :type  arg2 : string
    :param datastamp : True to put date stamp in or False to leave out
    :type  datastamp : boolean

####Sleep####
Library routine to sleep for a tiem and print messaging and countdown
    timer for seconds

    :param message : String of message to print in sleep message
    :type  message : string
    :param seconds : number of seconds to sleep
    :type  seconds : integer
