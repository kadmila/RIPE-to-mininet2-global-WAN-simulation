#!/usr/bin/env python3
# ------------------------------------------------------------------
# Global-Scale WAN Simulation Setup
# Creates a fully-connected mesh of city routers with realistic latencies
# ------------------------------------------------------------------

import os
import sys
import json
import math

# Add mininet to path
module_path = os.path.abspath('../mininet')
if module_path not in sys.path:
    sys.path.append(module_path)

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel


# ------------------------------------------------------------------
# Global Configuration
# ------------------------------------------------------------------

CONFIG_PATH = './city_config.json'
DEFAULT_BANDWIDTH = 1000  # 1 Gbps

# Network emulation parameters for realistic WAN simulation
JITTER_DISTRIBUTION = 'normal'  # Use normal distribution for realistic WAN jitter
DELAY_CORRELATION = 25  # Correlation percentage for successive packets (0-100)

# IP addressing for point-to-point router links
# Each link between two cities gets a /30 subnet (2 usable IPs)

def load_city_config():
    """Load and return city configuration from JSON file."""
    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        print(f'Loaded configuration for {len(config)} cities from {CONFIG_PATH}')
        return config
    except FileNotFoundError:
        print(f'Error: Configuration file not found: {CONFIG_PATH}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in {CONFIG_PATH}: {e}')
        sys.exit(1)


def preprocess_city_links(city_config):
    """
    Pre-process all city pairs and assign incremental link IDs.
    This ensures deterministic, collision-free link IDs for IP addressing.
    
    Args:
        city_config: Dictionary of city configurations
        
    Returns:
        Dictionary mapping (city1, city2) tuples to link IDs (1-based)
    """
    link_id_map = {}
    cities = list(city_config.keys())
    link_id = 1
    
    for i, city1 in enumerate(cities):
        for city2 in cities[i + 1:]:
            # Store both orderings for easy lookup
            link_id_map[(city1, city2)] = link_id
            link_id_map[(city2, city1)] = link_id
            link_id += 1
    
    print(f'Pre-processed {link_id - 1} city-to-city links with incremental IDs (1-{link_id - 1})')
    return link_id_map


# Parse configuration once at module level
CITY_CONFIG = load_city_config()
CITY_ABBRS = list(CITY_CONFIG.keys())  # List of city abbreviations
CITY_NAMES = {abbr: data['city'] for abbr, data in CITY_CONFIG.items()}  # Map abbr -> full city name
LINK_ID_MAP = preprocess_city_links(CITY_CONFIG)


# ------------------------------------------------------------------
# Topology Class
# ------------------------------------------------------------------

class GlobalWANTopo(Topo):
    """
    Global WAN topology with 19 cities.
    Each city has a router (host with IP forwarding), fully connected with realistic latencies.
    """

    def build(self):
        """Build the topology with city routers and inter-city links."""
        
        # Use the pre-loaded global configuration
        city_config = CITY_CONFIG
        
        # Store link metadata for routing configuration
        self.links_info = []
        
        # Create a router for each city
        print("Creating city routers...")
        for city_abbr in CITY_ABBRS:
            router_name = f'r_{city_abbr}'
            
            # Add host node that will act as a router
            # IP addresses will be configured later in configure_routers()
            self.addHost(router_name, ip=None)
            
            #print(f'  Created router {router_name} for {CITY_NAMES[city_abbr]}')
        
        # Create fully-connected mesh between all city routers
        print("\nCreating inter-city links...")
        link_count = 0
        
        for i, city1 in enumerate(CITY_ABBRS):
            for city2 in CITY_ABBRS[i + 1:]:
                # Get network statistics from city1 to city2
                stats = city_config[city1]['network_stats'][city2]
                mean_rtt = stats['mean']
                stddev_rtt = stats['stddev']
                
                # Calculate one-way delay (RTT / 2)
                delay_ms = mean_rtt / 2.0
                
                # Add jitter based on standard deviation
                # Use stddev as jitter to simulate variance
                jitter_ms = stddev_rtt / 2.0
                
                # Get pre-assigned incremental link ID
                link_id = LINK_ID_MAP[(city1, city2)]
                
                # Create link with named interfaces for explicit routing
                self.addLink(
                    f'r_{city1}',
                    f'r_{city2}',
                    intfName1=f'r-{city1}-{city2}',
                    intfName2=f'r-{city2}-{city1}',
                    cls=TCLink,
                    delay=f'{delay_ms:.2f}ms',
                    jitter=f'{jitter_ms:.2f}ms',
                    bw=DEFAULT_BANDWIDTH
                )
                
                # Store link metadata for routing configuration
                self.links_info.append({
                    'city1': city1,
                    'city2': city2,
                    'link_id': link_id,
                    'intf1': f'r-{city1}-{city2}',
                    'intf2': f'r-{city2}-{city1}',
                    'delay_ms': delay_ms,
                    'jitter_ms': jitter_ms
                })
                
                link_count += 1
                # print(f'  Link {link_count}: {city1} <-> {city2} '
                #       f'(delay: {delay_ms:.2f}ms ± {jitter_ms:.2f}ms, link_id: {link_id})')
        
        print(f'\nTopology built: {len(CITY_ABBRS)} routers, {link_count} links')


# ------------------------------------------------------------------
# Network Setup and Configuration
# ------------------------------------------------------------------

def router_systemctl_config(router):
    router.cmd('sysctl -w net.ipv4.ip_forward=1 > /dev/null')

def configure_routers(net, topo):
    """
    Configure routers with IP addresses, enable IP forwarding, and set up routing tables.
    
    Args:
        net: Mininet network instance
        topo: GlobalWANTopo instance with links_info
    """
    print("\nConfiguring routers...")
    
    # Track which routers we've already configured IP forwarding for
    routers_configured = set()
    
    print("  Configuring links (IP forwarding, IP addresses, and routes)...")
    
    # Single iteration over all links
    for link_info in topo.links_info:
        city1 = link_info['city1']
        city2 = link_info['city2']
        link_id = link_info['link_id']
        intf1 = link_info['intf1']
        intf2 = link_info['intf2']
        
        # Get routers
        router1 = net.get(f'r_{city1}')
        router2 = net.get(f'r_{city2}')
        
        # Enable IP forwarding on routers, and drop autoconfigured routing rules (only once per router)
        if city1 not in routers_configured:
            router_systemctl_config(router1)
            routers_configured.add(city1)
        
        if city2 not in routers_configured:
            router_systemctl_config(router2)
            routers_configured.add(city2)
        
        # Assign IP addresses to point-to-point interfaces
        # Point-to-point /30 subnet: 10.{link_id}.0.{1,2}/30
        ip1 = f'10.{link_id}.0.1'
        ip2 = f'10.{link_id}.0.2'

        subnet_mask = f'255.255.255.3/30'
        
        router1.cmd(f'ifconfig {intf1} {ip1} netmask {subnet_mask}')
        router2.cmd(f'ifconfig {intf2} {ip2} netmask {subnet_mask}')
        
        # Add routes: each router adds a route to reach the other router's IP
        router1.cmd(f'ip route add {ip2} dev {intf1}')
        router2.cmd(f'ip route add {ip1} dev {intf2}')
        
        print(f'    Link {link_id}: {city1} ({ip1}) <-> {city2} ({ip2})')
    
    print(f'\n  Configuration complete: {len(routers_configured)} routers, {len(topo.links_info)} links')


def validate_network(net, topo):
    """
    Validate network configuration and test connectivity.
    
    Args:
        net: Mininet network instance
        topo: GlobalWANTopo instance
    """
    print("\n" + "=" * 70)
    print("Network Validation")
    print("=" * 70)
    
    # Sample a few routers to validate
    sample_cities = CITY_ABBRS[:3] if len(CITY_ABBRS) >= 3 else CITY_ABBRS
    
    print("\nSample Router Interface Configuration:")
    print("-" * 70)
    for city_abbr in sample_cities:
        router = net.get(f'r_{city_abbr}')
        city_name = CITY_NAMES[city_abbr]
        print(f"\n{city_name} ({city_abbr}):")
        print(router.cmd('ip addr show | grep -E "^[0-9]+:|inet "'))
    
    print("\nSample Router Routing Tables:")
    print("-" * 70)
    for city_abbr in sample_cities:
        router = net.get(f'r_{city_abbr}')
        city_name = CITY_NAMES[city_abbr]
        print(f"\n{city_name} ({city_abbr}):")
        print(router.cmd('ip route | head -10'))
    
    # Test connectivity between a few city pairs
    print("\nConnectivity Tests (Sample):")
    print("-" * 70)
    if len(CITY_ABBRS) >= 2:
        # Test first to second city
        city1 = CITY_ABBRS[0]
        city2 = CITY_ABBRS[1]
        
        router1 = net.get(f'r_{city1}')
        
        # Find the IP of router2's interface connected to router1
        link_info = None
        for link in topo.links_info:
            if (link['city1'] == city1 and link['city2'] == city2) or \
               (link['city1'] == city2 and link['city2'] == city1):
                link_info = link
                break
        
        if link_info:
            link_id = link_info['link_id']
            # Determine which IP belongs to router2
            if link_info['city1'] == city1:
                target_ip = f'10.{link_id}.0.2'
            else:
                target_ip = f'10.{link_id}.0.1'
            
            print(f"\nPing test: {CITY_NAMES[city1]} -> {CITY_NAMES[city2]}")
            print(f"Target IP: {target_ip}")
            result = router1.cmd(f'ping -c 3 {target_ip}')
            print(result)
    
    print("=" * 70)


def run_simulation():
    """Main function to set up and run the simulation."""
    
    print("=" * 70)
    print("Global WAN Simulation - 19 City Router Mesh")
    print("=" * 70)
    
    # Set log level
    setLogLevel('output')
    
    # Create topology
    print("\nBuilding topology...")
    topo = GlobalWANTopo()
    
    # Create network with TC link support for delay/bandwidth
    print("\nStarting network...")
    net = Mininet(
        topo=topo,
        link=TCLink,
        waitConnected=True,
        autoSetMacs=True,
        autoStaticArp=False
    )
    
    # Start network
    net.start()
    
    # Configure routers (IP addresses, forwarding, routing tables)
    configure_routers(net, topo)
    
    # Validate network configuration
    # validate_network(net, topo)
    
    # Print network info
    print("\n" + "=" * 70)
    print("\nAvailable routers:")
    for city_abbr in sorted(CITY_ABBRS):
        router_name = f'r_{city_abbr}'
        city_name = CITY_NAMES[city_abbr]
        print(f'  {router_name} - {city_name}')
    
    print("=" * 70)
    
    # Start CLI
    CLI(net)
    
    # Cleanup
    print("\nStopping network...")
    net.stop()
    print("Done.")


# ------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------

if __name__ == '__main__':
    try:
        run_simulation()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
