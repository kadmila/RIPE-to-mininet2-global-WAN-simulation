#!/usr/bin/env python3
# ------------------------------------------------------------------
# Global-Scale WAN Simulation Setup
# Creates a fully-connected mesh of city switchs with realistic latencies
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


# Parse configuration once at module level
CITY_CONFIG = load_city_config()


# ------------------------------------------------------------------
# Topology Class
# ------------------------------------------------------------------

class GlobalWANTopo(Topo):
    """
    Global WAN topology with 19 cities.
    Each city has a switch, fully connected with realistic latencies.
    """

    def build(self):
        """Build the topology with city switchs and inter-city links."""
        
        # Use the pre-loaded global configuration
        city_config = CITY_CONFIG
        
        # Store switchs for later access
        self.switchs = {}
        self.city_names = {}
        
        # Create a switch for each city
        print("Creating city switchs...")
        dpid_counter = 1
        for city_abbr, city_data in city_config.items():
            city_name = city_data['city']
            switch_name = f's_{city_abbr}'
            
            # Add switch node with explicit dpid
            switch = self.addSwitch(
                switch_name,
                dpid=f'{dpid_counter:016x}',
                cls=None,
                failMode='standalone'
            )
            
            self.switchs[city_abbr] = switch
            self.city_names[city_abbr] = city_name
            print(f'  Created switch {switch_name} for {city_name}')
            dpid_counter += 1
        
        # Create fully-connected mesh between all city switchs
        print("\nCreating inter-city links...")
        cities = list(city_config.keys())
        link_count = 0
        
        for i, city1 in enumerate(cities):
            for city2 in cities[i + 1:]:
                # Get network statistics from city1 to city2
                stats = city_config[city1]['network_stats'][city2]
                mean_rtt = stats['mean']
                stddev_rtt = stats['stddev']
                
                # Calculate one-way delay (RTT / 2)
                delay_ms = mean_rtt / 2.0
                
                # Add jitter based on standard deviation
                # Use stddev as jitter to simulate variance
                jitter_ms = stddev_rtt / 2.0
                
                # Create link with delay, jitter, correlation, and normal distribution
                # tc netem format: delay TIME JITTER CORRELATION distribution TYPE
                self.addLink(
                    self.switchs[city1],
                    self.switchs[city2],
                    cls=TCLink,
                    delay=f'{delay_ms:.2f}ms',
                    jitter=f'{jitter_ms:.2f}ms',
                    bw=DEFAULT_BANDWIDTH
                )
                
                link_count += 1
                print(f'  Link {link_count}: {city1} <-> {city2} '
                      f'(delay: {delay_ms:.2f}ms ± {jitter_ms:.2f}ms (stddev) )')
        
        print(f'\nTopology built: {len(self.switchs)} switchs, {link_count} links')


# ------------------------------------------------------------------
# Network Setup and Configuration
# ------------------------------------------------------------------

def configure_switchs(net):
    """
    Configure IP forwarding on all switchs.
    
    Args:
        net: Mininet network instance
    """
    print("\nConfiguring switchs...")
    
    for switch in net.switches:
        # Enable IP forwarding
        switch.cmd('sysctl -w net.ipv4.ip_forward=1')
        print(f'  Enabled IP forwarding on {switch.name}')


def run_simulation():
    """Main function to set up and run the simulation."""
    
    print("=" * 70)
    print("Global WAN Simulation - 19 City switch Mesh")
    print("=" * 70)
    
    # Set log level
    setLogLevel('info')
    
    # Create topology
    print("\nBuilding topology...")
    topo = GlobalWANTopo()
    
    # Create network with TC link support for delay/bandwidth
    print("\nStarting network...")
    net = Mininet(
        topo=topo,
        link=TCLink,
        autoSetMacs=True,
        autoStaticArp=False
    )
    
    # Start network
    net.start()
    
    # Configure switchs
    configure_switchs(net)
    
    # Print network info
    print("\n" + "=" * 70)
    print("Network is ready!")
    print("=" * 70)
    print("\nAvailable switchs:")
    for city_abbr, switch_name in sorted(topo.switchs.items()):
        city_name = topo.city_names[city_abbr]
        print(f'  {switch_name} - {city_name}')
    
    print("\nYou can now:")
    print("  - Test connectivity: pingall")
    print("  - Check specific link: <switch1> ping -c 3 <switch2>")
    print("  - Run commands: <switch> <command>")
    print("  - Exit: quit or exit")
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
