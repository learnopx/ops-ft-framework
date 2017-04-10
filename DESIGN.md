Test Framework - opstestfw Library Design
=================

## Introduction
This document discusses the design of the opstestfw library modules.  This framework is used to develop component and feature level tests for the OpenSwitch project.

The opstestfw library module is comprised of core objects that are discussed in the "Framework Objects" section below.  This discusses what the core objects are and how they are interrelated to each other.  Another core aspect of this module is the concept of topology.  This is described in the "Topology" section below.  

Another important aspect of the opstestfw library module is the concept of "Helper Libraries" and how they relate to the objects.  For more information, see Helper Library below.

## Framework objects
The framework has some core object.  This section describes the core objects key function and discusses how to use them.  It is important to know the hierarchy of the objects to be successful with working with them.

### The testEnviron object
This testEnviron object is the first object created in the test suite.  This object preforms the following tasks:

 - Creates the logging structure for the suite. By default, this creates a log structure in /tmp/opsTest-results.  Each test run has an individual date stamp directory under the main results directory.
 - Solves topology specifications and instantiate the topology object.  The topology object is a member of this class.

### The Topology object
The topology object is instantiated and is stored within the testEnviron object.  This is actually created in setup_class pytest method.

The topology code will build and map the topology.  This creates all device objects and enable those objects to create interactive connections with the devices.  One of the most important tasks the Topology object performs is create and populate the linkPortMapping dictionary for each device.

### The Device object
The device objects are stored within the topology objects.  The device object contains connection information and objects for the device.  This objects has methods to interact with the device and also error check the transaction with the device.  The device object also contains the linkPortMapping dictionary that maps a physical port to a logical link for the device.  To get the port number of a switch that is connected over lnk01, you would reference it as dut01Obj.ilnkPortMapping['lnk01'].

The device object is the object that will be passed into the helper library functions.

### The returnStruct object
The helper libraries and many class methods will return the returnStruct object to the calling process.  Helper libraries and class methods will create this object before return it to the calling routine.
The returnStruct object provides consistency in library returns and gives  standard methods for pulling values out of the return structure.  
Arguments to this class are: returnCode, buffer, and data (data can be either a value or a dictionary).  Methods to retrieve data…

 - returnCode() -- Gets he returnCode for the library called.
 - buffer() -- Returns the raw buffer if one is given to the object on creation.
 - dataKeys() -- Gives top level dictionary keys of the data stored.
 - valueGet(key=) -- If no key is given, just returns data.  If a key is
   given, will return the value for the key in the dictionary.
 - retValueString() -- Method to return a JSON string of the returnCode,
   buffer, and data.
 - printValueString() -- Same as retValueString, but prints the JSON string.


## Topology
Each test case must have a "topoDict" dictionary defined.  This dictionary describes the way the topology is configured.  Below is an example topology.
```
topoDict = {"topoTarget": "dut01",
			"topoDevices": "dut01 wrkston01 wrkston02",
            "topoLinks": "lnk01:dut01:wrkston01,lnk02:dut01:wrkston02",
            "topoFilters": "dut01:system-category:switch,dut02:system-category:switch"}

```
The names used in the dictionary values should follow this notation:

 - **Switches**:  These should be named "dut0x",  If there was a two switch topology,  these switches would logically be called dut01 and dut02.
 - **Workstations / Hosts**:  These should be named "wrkston0x".  If there were three workstations in the topology, these should be referred to as wrkston01, wrkston02, and wrkston03.
 - **Links**:  Links are connections between two entities and should be named similar to the following:  lnk0x.  For example, if there are three links in the topology then would be named lnk01, lnk02, and lnk03 respectively.

Below is a description of the topoDict key / value pairs.

 - **topoTarget**:  This identifies the switches that installs the build under test.  If there are three switches in the topology, the value would look like "dut01 dut02 dut03".
 - **topoDevices**:  This identifies all the logical devices in the topology.  If there are two switches and three workstations the topology, the values of this would look like "dut01 dut02 wrkston01 wrkston02 wrkston03".
 - **topoLinks**:  This defines the links for the topology and specifies the entities that the link interconnects.  The link definition is delimited by the ":" character.  The notation of a link definition statement is linkname:device1:device2.  Multiple links are delimited by the "," character.  If there were 3 links defined the statement might look like "lnk01:dut01:wrkston01,lnk02:dut01:wrkston02,lnk03:dut01:dut02".  This example states that "lnk01" is a connection between dut01 and wrkston01, "lnk02" is a connection between dut01 and wrkston02, and "lnk03" is a connection between dut01 and dut02.
 - **topoFilters**:  This gives base definition of what each device is.  This is in the form of  "device":"attribute":"value".  The one attribute that is currently accepted today is "system-category" and the value of this is either switch or workstation.
 - **topoLinkFilter**:  This is a filter that can add requirements to a specific link.  For example, to make sure a port is connected to a specific port on the switch, add it in the following notation: 
 "topoLinkFilter": "lnk01:dut01:interface:eth0" - this makes sure that lnk01 port on dut01 is over eth0.  This topology key is optional.



## Helper and utility libraries
Helper and utility libraries are used for performing certain functions like enabling an interface, or configuring or unconfiguring a feature.  Currently the framework packages up these libraries in the opstestfw.host package for any host specific libraies and the opstestfw.switch.CLI package for switch CLI libraries.

## Supporting Documentation
Please refer to the "Writing a Feature Test Case" document that describes the core pieces of the test case.  This document will help get you started on creating automated test cases for OpenSwitch.