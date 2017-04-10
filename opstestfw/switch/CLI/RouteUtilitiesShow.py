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


def get_route_and_nexthops_from_output(output, route, route_type):
    """
    Library function to get the show dump for a route in the command
    "show ip route/show ipv6 route/show rib".

    :param output    : Output of either of the show commands
                       "show ip route/show ipv6 route/show rib"
    :type output     : string
    :param route     : Route which is of the format "Prefix/Masklen"
    :type  route     : string
    :param route_type : Route type which can be "static/BGP"
    :type  route_type : string
    :return: string
    """

    found_route = False
    found_nexthop = False

    # Spilt the output in lines
    lines = output.split('\n')

    # Output buffer for storing the route and its next-hops
    route_output = ''

    # Walk through all the lines for the output of
    # "show ip route/show ipv6 route/show rib"
    for line in lines:

        # If the route ("prefix/mask-length") is not found in the output
        # then try to find the route in the output. Otherwise the route
        # was already found and now try to check whether the next-hop
        # is of type 'route_type'
        if not found_route:

            # If the route ("prefix/mask-length") is found in the line
            # then set 'found_route' to 'True' and add the line to the
            # output buffer
            if route in line:
                found_route = True
                route_output = route_output + line + '\n'
        else:

            # If the route_type occurs in the next-hop line,
            # then add the next-hop line into the output buffer.
            if 'via' in line and route_type in line:
                route_output = route_output + line + '\n'
                found_nexthop = True
            else:
                # If the next-hop is not of type 'route_type',
                # then reset 'found_route' to 'False'
                if not found_nexthop:
                    found_route = False
                    route_output = ''
                else:
                    break

    # Return the output buffer to caller
    return route_output
