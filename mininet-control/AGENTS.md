# AGENTS.md - Development Guide for AI Coding Agents

This guide provides essential information for AI coding agents working on the RIPE-to-Mininet2 Global WAN Simulation project.

## Project Overview

A Python-based Mininet2 simulation that creates a realistic global WAN network topology using RIPE Atlas measurement data. The simulation builds a fully-connected mesh of 19 city routers with realistic latencies, jitter, and bandwidth characteristics derived from actual network measurements.

**Key Files:**
- `setup.py` - Main simulation script (354 lines)
- `city_config.json` - Network topology and latency configuration
- `run.sh` - Network cleanup and execution wrapper
- `config_gen.ipynb` - Jupyter notebook for configuration generation (not for production)

## Build and Run Commands

### Running the Simulation

```bash
# Full execution with cleanup (recommended)
./run.sh

# Direct execution (requires root for Mininet)
sudo python3 setup.py

# Manual cleanup before running
sudo mn -c
sudo python3 setup.py
```

### System Requirements Setup

```bash
# Increase file descriptor and process limits
ulimit -n 65535
ulimit -u 65535

# Increase kernel limits
sudo sysctl -w fs.file-max=2097152
sudo sysctl -w net.ipv4.ip_local_port_range="1024 65535"
```

### Testing

**Note:** This project does not have a formal test suite. AI coding agents MUST NOT run the code. The simulation is validated through:
- Manual human inspection
- Structural code review

## Code Style Guidelines

### Import Organization

1. **Standard library imports** (alphabetical)
2. **Third-party imports** (mininet modules)
3. **Local imports** (if any)

```python
import json
import math
import os
import sys

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.topo import Topo
```

### Naming Conventions

- **Variables/Functions:** `snake_case` (e.g., `load_city_config`, `link_id_map`)
- **Classes:** `PascalCase` (e.g., `GlobalWANTopo`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `CONFIG_PATH`, `DEFAULT_BANDWIDTH`)

### Documentation

- Use clear docstrings with Args/Returns sections
- Section separators: `# ------------------------------------------------------------------`
- Inline comments explain "why" not "what"
- **Type hints:** Not extensively used - focus on clear variable names and docstrings

### Error Handling

```python
# File operations with specific error messages
try:
    with open(CONFIG_PATH) as f:
        config = json.load(f)
except FileNotFoundError:
    print(f'Error: Configuration file not found: {CONFIG_PATH}')
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f'Error: Invalid JSON in {CONFIG_PATH}: {e}')
    sys.exit(1)

# Top-level exception handling
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
```

## Architecture Patterns

### Configuration Loading

- Configuration loaded **once at module level** into global constants
- Pre-processing (e.g., `preprocess_city_links`) done during module import
- Avoids redundant file I/O and computation

```python
CITY_CONFIG = load_city_config()
LINK_ID_MAP = preprocess_city_links(CITY_CONFIG)
```

### Network Topology

- **Topology class:** Inherits from `mininet.topo.Topo`
- **Router naming:** `r_{city_abbr}` (e.g., `r_tko`, `r_nyc`)
- **Interface naming:** `r-{city1}-{city2}` for point-to-point links
- **IP addressing:** `10.{link_id}.0.{1,2}/30` for point-to-point subnets

### System Commands

- Use `router.cmd()` for executing commands on Mininet nodes
- Suppress verbose output with `> /dev/null` for sysctl commands
- Use `ifconfig` and `ip route` for network configuration

## Common Tasks

### Adding a New City

1. Add city data to `city_config.json` with network_stats for all other cities
2. No code changes needed - topology builds dynamically from config

### Modifying Network Parameters

- **Bandwidth:** Change `DEFAULT_BANDWIDTH` constant (in Mbps)
- **Delay calculation:** Modify formula in topology build (currently RTT/2)
- **Jitter calculation:** Modify jitter formula (currently stddev/2)

### Debugging Network Issues

```python
# Add debug output in configure_routers()
print(router.cmd('ip addr show'))
print(router.cmd('ip route'))

# Enable validate_network() function (uncomment line 318)
validate_network(net, topo)
```

### Extending Functionality

- **Add hosts to cities:** Create hosts and attach to city routers
- **Custom routing:** Modify route configuration in `configure_routers()`
- **Traffic generation:** Add iperf or custom traffic generators in CLI

## Important Notes

- **Root required:** Mininet requires sudo/root access
- **Cleanup:** Always run `sudo mn -c` between runs to avoid conflicts
- **Resource limits:** Large topologies need increased ulimits (see run.sh)
- **Interface IDs:** Link IDs are deterministic based on city pair ordering
- **IP forwarding:** Automatically enabled on all routers via sysctl

## VS Code Configuration

The project includes `.vscode/settings.json` with:
```json
{
    "python.analysis.extraPaths": ["./mininet"]
}
```

This allows proper IntelliSense for mininet modules. Keep this configuration when modifying the project.
