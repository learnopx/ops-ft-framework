#!/usr/bin/python

# (c) Copyright 2015 Hewlett Packard Enterprise Development LP
#
# GNU Zebra is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# GNU Zebra is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Zebra; see the file COPYING.  If not, write to the Free
# Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.

from opstestfw import *
from opstestfw.switch.CLI import *
from opstestfw.switch.OVS import *
from RouteUtilitiesShow import *
import re


def get_route_from_show_route(**kwargs):

    """
    Library function to get the show dump for a route in the command
    "show ip route/show ipv6 route".

    :param deviceObj : Device object
    :type  deviceObj : object
    :param if_ipv4   : If the route passed is IPv4 or IPv6 route. If
                       the route passed in IPv4, then if_ipv4 should
                       be 'True' otherwise it should be 'False'
    :type  if_ipv4   : boolean
    :param route     : Route which is of the format "Prefix/Masklen"
    :type  route     : string
    :param routetype : Route type which can be "static/BGP"
    :type  routetype : string
    :return: returnStruct Object
            buffer
            data keys
                Route - string set to route which is of the format
                        "Prefix/Masklen"
                NumberNexthops - string set to the number of next-hops
                                 of the route
                Next-hop - string set to the next-hop port or IP/IPv6
                           address as the key and a dictionary as value
                data keys
                    Distance - String whose numeric value is the administration
                               distance of the next-hop
                    Metric - String whose numeric value is the metric of the
                             next-hop
                    RouteType - String which is the route type of the next-hop
                                which is among "static/BGP"
    :returnType: object
    """
    overallBuffer = []
    deviceObj = kwargs.get('deviceObj', None)
    if_ipv4 = kwargs.get('if_ipv4', True)
    route = kwargs.get('route', None)
    routetype = kwargs.get('routetype', None)

    # If Device object is not passed, we need to error out
    if deviceObj is None:
        opstestfw.LogOutput('error',
                            "Need to pass switch device object deviceObj "
                            "to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # If route object is not passed, we need to error out
    if route is None:
        opstestfw.LogOutput('error',
                            "Need to pass route to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # If route type object is not passed, we need to error out
    if routetype is None:
        opstestfw.LogOutput('error',
                            "Need to pass route type to this routine")
        returnCls = opstestfw.returnStruct(returnCode=1)
        return returnCls

    # Get into vtyshelll
    returnStructure = deviceObj.VtyshShell(enter=True)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to get vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # if 'if_ipv4' is 'True', then the command to be executed is
    # "show ip route" otherwise the command is "show ipv6 route"
    if if_ipv4 is True:
        command = "show ip route"
    else:
        command = "show ipv6 route"

    # Execute the command in the vtyshell
    returnDevInt = deviceObj.DeviceInteract(command=command)
    retCode = returnDevInt['returnCode']
    overallBuffer.append(returnDevInt['buffer'])
    show_ip_route_output = returnDevInt['buffer']
    if retCode != 0:
        opstestfw.LogOutput('error', "No route in route table: " + command)
    else:
        opstestfw.LogOutput('debug', "Found routes in route table: " + command)

    # Get out of vtyshell
    returnStructure = deviceObj.VtyshShell(enter=False)
    returnCode = returnStructure.returnCode()
    overallBuffer.append(returnStructure.buffer())
    if returnCode != 0:
        opstestfw.LogOutput('error', "Failed to exit vtysh prompt")
        bufferString = ""
        for curLine in overallBuffer:
            bufferString += str(curLine)
        returnCls = opstestfw.returnStruct(returnCode=1, buffer=bufferString)
        return returnCls

    # Get the route and the next-hops for the 'routetype' from the
    # "show ip route/show ipv6 route".
    route_output = get_route_and_nexthops_from_output(show_ip_route_output,
                                                      route, routetype)

    # Initialize the return route dictionary
    RouteDict = dict()

    # Add the prefix and the mask length of the route in the return
    # dictionary
    RouteDict['Route'] = route

    lines = route_output.split('\n')

    # Walk through all the lines of the route output for the route and
    # populate the return route distionary
    for line in lines:

        # Match the route ("prefix/mask-length") against the regular expression
        routeline = re.match("(%s)(,  )(\d+)( unicast next-hops)" %(route),
                             line)

        # The output line matches the route, then populate the route and number
        # of next-hops in the return route dictionary
        if routeline:
            RouteDict['Route'] = routeline.group(1)
            RouteDict['NumberNexthops'] = routeline.group(3)

        # Match the next-hop lines against the regular expression and populate
        # the next-hop dictionary with distance, metric and routetype
        nexthopline = re.match("(.+)via  ([0-9.:]+),  \[(\d+)/(\d+)\],  (.+)",
                               line)
        if nexthopline:
            RouteDict[nexthopline.group(2)] = dict()
            RouteDict[nexthopline.group(2)]['Distance'] = nexthopline.group(3)
            RouteDict[nexthopline.group(2)]['Metric'] = nexthopline.group(4)
            RouteDict[nexthopline.group(2)]['RouteType'] = nexthopline.group(5).rstrip('\r')

    # Return results in the form of the structure 'returnCls'
    bufferString = ""
    for curLine in overallBuffer:
        bufferString += str(curLine)
    returnCls = returnStruct(
        returnCode=0,
        buffer=bufferString,
        data=RouteDict)
    return returnCls


def verify_route_in_show_route(switch, if_ipv4, ExpRouteDictStaticRoute,
                               RouteType):
    """
    Library function tests whether a route ("prefix/mask-length") in the
    command "show ip route/show ipv6 route" exactly matches an expected route
    dictionary that is passed to this function. In case the route dictionary
    returned by 'get_route_from_show_route()' is not same as the expected route
    dictionary, then this function will fail the test case by calling assert().

    :param deviceObj : Device object
    :type  deviceObj : object
    :param if_ipv4   : If the route passed is IPv4 or IPv6 route. If
                       the route passed in IPv4, then if_ipv4 should
                       be 'True' otherwise it should be 'False'
    :type  if_ipv4   : boolean
    :param ExpRouteDictStaticRoute: Expected route dictionary
    :type  ExpRouteDictStaticRoute: dictionary
    :param routetype : Route type which can be "static/BGP"
    :type  routetype : string
    """

    LogOutput('info', "\nCheck ipv4 route table for "
              + ExpRouteDictStaticRoute['Route'])

    # Get the actual route dictionary for the route
    retStruct = get_route_from_show_route(deviceObj=switch, if_ipv4=if_ipv4, route=ExpRouteDictStaticRoute['Route'],
                                          routetype=RouteType)

    # If there was error getting the actual route dictionary, then assert and
    # fail the test case
    retCode = retStruct.returnCode()
    assert retCode == 0, "Failed to get the dictionary for route " + ExpRouteDictStaticRoute['Route'] + " and route type " + RouteType

    # Get the actual route dictionary from the returned object
    ActualRouteDictStaticRoute = retStruct.data

    # Print the actual and expected route dictionaries for debugging purposes
    LogOutput('info', "\nThe expected route dictionary is: "
              + str(ExpRouteDictStaticRoute))
    LogOutput('info', "\nThe actual route dictionary is: "
              + str(ActualRouteDictStaticRoute))

    # Assert if the two route dictionaries are not equal
    assert cmp(ExpRouteDictStaticRoute, ActualRouteDictStaticRoute) == 0, "Verfication failed for the route " + ExpRouteDictStaticRoute['Route']
