#!/usr/bin/env python3
import os
import random
import json
from math import radians, cos, sin, sqrt, atan2

module_path = os.path.abspath('../mininet')

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli  import CLI

import argparse

# ------------------------------------------------------------------
# Constants for Simulation Environment
# ------------------------------------------------------------------

city_config = {}
with open('./city_config.json') as f_city_config:
    city_config = json.load(f_city_config)

# light speed in glass fiber is ~2/3 of c
SPEED_COEFFICIENT=0.66

# ------------------------------------------------------------------
# 1. CLI arguments
# ------------------------------------------------------------------
parser = argparse.ArgumentParser(
    prog='sudo python3 main.py',
    description='Mininet interface for Xiangchi',
    epilog='')

parser.add_argument('--n_peer', required=True, type=int, help='Total of peers')

args = parser.parse_args()
print(f"{vars(args)}") # refer to when reading logs later

if (args.n_peer > 1000 | args.n_peer < 1):
    print("max n_peer is 1000")
    exit(1)

# ------------------------------------------------------------------
# Mininet Construction
# ------------------------------------------------------------------

class NetworkTopo( Topo ):
    def build(self):
        # regional router, switch, and hosts
        for region, (_, _, ip_prefix) in REGIONS.items():
            # router to switch
            router = self.addHost(f'r_{region}')
            switch = self.addSwitch(f's_{region}', dpid=f'00000000000000{ip_prefix}')
            self.addLink( switch, router, intfName2=f'r-{region}-eth0' ) # random ip will be assigned to this interface. (mininet limitation of a Node)

            # switch to hosts
            for i in range(args.n_client):
                host = self.addHost( f'h_{region}_{i}', ip=f'{ip_prefix}.0.1.{i+1}/8',
                                    defaultRoute=f'via {ip_prefix}.0.0.1' )
                self.addLink( switch, host, intfName2=f'h-eth0', delay=f'{random.uniform(0.0, 2.0)}ms' ) # mini suburban delay
            
        # inter-router links
        for region1, (lat1, lon1, ip_prefix1) in REGIONS.items():
            for region2, (lat2, lon2, ip_prefix2) in REGIONS.items():
                if (ip_prefix1 < ip_prefix2): # filter duplicates

                    # calculate transmission delay
                    d_km = haversine_km(lat1, lon1, lat2, lon2)
                    one_way_ms = (d_km / (299_792.458 * SPEED_COEFFICIENT)) * 1000
                    delay_str = f'{one_way_ms:.1f}ms'

                    linkid = f'{ip_prefix1[0]}{ip_prefix2[0]}'
                    self.addLink( f'r_{region1}', f'r_{region2}', 
                                intfName1=f'r-{region1}-eth{linkid}', intfName2=f'r-{region2}-eth{linkid}',
                                delay=delay_str) # also we need to configure their IP later.

if __name__ == '__main__':
    setLogLevel( 'info' )
    net = Mininet( topo=NetworkTopo(), link=TCLink, waitConnected=True )

    net.start()

    # configure router's regional interface
    for region, (_, _, ip_prefix) in REGIONS.items():
        router = net.get(f'r_{region}')
        router.cmd( f'ifconfig r-{region}-eth0 {ip_prefix}.0.0.1/8' )
        
        # enable forwarding
        router.cmd('sysctl -w net.ipv4.ip_forward=1')

    # configure routing table.
    for region1, (_, _, ip_prefix1) in REGIONS.items():
        for region2, (_, _, ip_prefix2) in REGIONS.items():
            if (ip_prefix1 < ip_prefix2): # filter duplicates
                router1 = net.get(f'r_{region1}')
                router2 = net.get(f'r_{region2}')

                linkid = f'{ip_prefix1[0]}{ip_prefix2[0]}'

                # assign IP. #intfName1=f'', intfName2=f'r_{region2}-eth{linkid}',
                router1.cmd( f'ifconfig r-{region1}-eth{linkid} 1.{linkid}.0.1/30' )
                router2.cmd( f'ifconfig r-{region2}-eth{linkid} 1.{linkid}.0.2/30' )

                # add routing table entry
                router1.cmd( f'route add -net {ip_prefix2}.0.0.0/8 gw 1.{linkid}.0.2' )
                router2.cmd( f'route add -net {ip_prefix1}.0.0.0/8 gw 1.{linkid}.0.1' )

    
    #### application logic
    print("starting application")
    server_host = net.get(f'h_{args.server_region}_0')
    gateway_switch = net.get(f's_{args.server_region}')

    # limit server bandwidth
    print("limiting server bandwidth")
    intf = server_host.connectionsTo(gateway_switch)[0][0]
    intf.config(bw=args.server_bandwidth)

    # run server and take log
    print("running server")
    server_host.cmd(f'./server.sh 0.0.0.0:3000 {args.n_client * len(REGION_NAMES) - 1} > server_log.txt 2> server_err.txt &')

    server_addr = f'{REGIONS[args.server_region][2]}.0.1.1:3000'

    # run clients
    print("running clients")
    for region, (_, _, ip_prefix) in REGIONS.items():
        for i in range(args.n_client):
            if region == args.server_region and i == 0:
                continue

            host_name = f'h_{region}_{i}'
            host = net.get(host_name)
            host.cmd(f'./client.sh {server_addr} {host_name} > ../client_log/{host_name}.txt &')
            host.cmd(f'chmod 666 ../client_log/{host_name}.txt')

    CLI( net )

    #### application cleanup
    # clear server
    server_host.cmd('./server_clear.sh')
    
    # clear clients
    for region, (_, _, ip_prefix) in REGIONS.items():
        for i in range(args.n_client):
            if region == args.server_region and i == 0:
                continue

            host_name = f'h_{region}_{i}'
            host = net.get(host_name)
            host.cmdPrint(f'./client_clear.sh {host_name}')

    net.stop()