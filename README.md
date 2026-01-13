# Nautobot Device Onboarding Command Mappers

This repository contains YAML override files for the Nautobot Device Onboarding plugin. These files define how to extract device and network data from various network platforms.

## Repository Structure

```
.
├── README.md
├── SCHEMA_REFERENCE.md
├── patches/
│   ├── command_getter.py      # Plugin patch for F5 platform support
│   └── inventory_creator.py    # Plugin patch for F5 platform support
└── onboarding_command_mappers/
    ├── bigip_f5.yml           # F5 BIG-IP (network_driver: bigip_f5)
    ├── f5_tmsh.yml            # F5 BIG-IP (Netmiko device_type: f5_tmsh)
    ├── paloalto_panos.yml     # Palo Alto Networks PAN-OS
    └── linux.yml              # Linux devices
```

## Quick Start: Installing These Overrides

### Option 1: Docker Compose (Development/Testing) - Recommended

This is the easiest method for local development and testing. Files are mounted directly from your local filesystem.

#### Step 1: Clone or Copy Files

Ensure you have the `onboarding_override` directory with the following structure:
```
onboarding_override/
├── onboarding_command_mappers/
│   ├── bigip_f5.yml
│   ├── f5_tmsh.yml
│   ├── paloalto_panos.yml
│   └── linux.yml
└── patches/
    ├── command_getter.py
    └── inventory_creator.py
```

#### Step 2: Update docker-compose.yml

Add volume mounts to your `docker-compose.yml` for both `nautobot` and `celery_worker` services:

```yaml
services:
  nautobot:
    volumes:
      # Device Onboarding YAML Overrides
      - "./onboarding_override/onboarding_command_mappers:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/command_mappers/:ro"
      # Device Onboarding Plugin Patches (REQUIRED for F5)
      - "./onboarding_override/patches/command_getter.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/command_getter.py:ro"
      - "./onboarding_override/patches/inventory_creator.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/inventory_creator.py:ro"
  
  celery_worker:
    volumes:
      # Device Onboarding YAML Overrides
      - "./onboarding_override/onboarding_command_mappers:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/command_mappers/:ro"
      # Device Onboarding Plugin Patches (REQUIRED for F5)
      - "./onboarding_override/patches/command_getter.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/command_getter.py:ro"
      - "./onboarding_override/patches/inventory_creator.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/inventory_creator.py:ro"
```

**Note:** Adjust the Python version path (`python3.11`) to match your Nautobot container's Python version.

#### Step 3: Configure nautobot_config.py

Add the following configuration to your `nautobot_config.py`:

```python
# NETWORK_DRIVERS - Required for F5 BIG-IP
NETWORK_DRIVERS = {
    "netmiko": {
        "bigip_f5": "f5_tmsh",  # Override: bigip_f5 -> f5_tmsh for Netmiko
    },
}

# Connection options for F5 and other devices
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "connection_options": {
            "netmiko": {
                "extras": {
                    "timeout": 90,
                    "banner_timeout": 60,
                    "global_delay_factor": 3,
                    "fast_cli": False,
                    "allow_agent": False,
                }
            }
        }
    },
}
```

#### Step 4: Restart Services

```bash
docker-compose restart nautobot celery_worker
```

#### Step 5: Verify Installation

1. Check that files are mounted:
   ```bash
   docker-compose exec nautobot ls -la /usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/command_mappers/
   ```
   You should see: `bigip_f5.yml`, `f5_tmsh.yml`, `paloalto_panos.yml`, `linux.yml`

2. Test onboarding:
   - Navigate to **Jobs → Sync Devices From Network**
   - Enter a device IP address
   - Select the appropriate platform
   - Run the job

### Option 2: Git Repository (Production/Standard Nautobot)

For production deployments or standard Nautobot installations, use a Git repository.

#### Step 1: Push Files to Git Repository

1. Create a Git repository (GitHub, GitLab, etc.)
2. Push the `onboarding_override` directory structure to your repository
3. Ensure the structure is:
   ```
   your-repo/
   └── onboarding_command_mappers/
       ├── bigip_f5.yml
       ├── f5_tmsh.yml
       ├── paloalto_panos.yml
       └── linux.yml
   ```

**Important:** The `patches/` directory is only needed for Docker Compose volume mounts. For Git repositories, you'll need to apply patches differently (see F5 BIG-IP section below).

#### Step 2: Configure Nautobot Platform

1. Navigate to: **Devices → Platforms**
2. Create or edit platforms:
   - **F5 BIG-IP:**
     - Name: `F5 BIG-IP` or `bigip_f5`
     - Network Driver: `bigip_f5` (IMPORTANT: Do NOT change to `f5_tmsh`)
   - **Palo Alto:**
     - Name: `paloalto_panos`
     - Network Driver: `paloalto_panos`

#### Step 3: Add NETWORK_DRIVERS Configuration

Edit your `nautobot_config.py`:

```python
NETWORK_DRIVERS = {
    "netmiko": {
        "bigip_f5": "f5_tmsh",  # Required for F5
    },
}
```

#### Step 4: Create Git Repository in Nautobot

1. Navigate to: **Extensibility → Git Repositories**
2. Click **Add** to create a new repository
3. Configure:
   - **Name:** `Device Onboarding Command Mappers`
   - **Remote URL:** Your Git repository URL
   - **Branch:** `main` (or your default branch)
   - **Provides:** ✅ **Network Sync Job Command Mappers** (CRITICAL)
   - **Username/Token:** If repository is private
4. Click **Save**
5. Click **Sync** to pull the files

#### Step 5: Apply Plugin Patches (F5 Only - Required)

**⚠️ CRITICAL:** F5 BIG-IP requires plugin patches. Choose one method:

**Method A: Custom Docker Image (Recommended for Production)**
```dockerfile
FROM ghcr.io/nautobot/nautobot:latest
COPY patches/command_getter.py /usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/
COPY patches/inventory_creator.py /usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/
```

**Method B: Fork Plugin and Apply Patches**
- Fork `nautobot-app-device-onboarding`
- Apply patches from `patches/` directory
- Install: `pip install git+https://github.com/your-username/nautobot-app-device-onboarding.git`

**Method C: Volume Mounts (if using Docker)**
- Add volume mounts as shown in Option 1 above

#### Step 6: Restart Services

```bash
# Docker Compose
docker-compose restart nautobot celery_worker

# Systemd
sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
```

### What's Included

#### F5 BIG-IP Support (`bigip_f5.yml` / `f5_tmsh.yml`)

**Sync Devices (Initial Onboarding):**
- ✅ Manufacturer, Model, Device Type
- ✅ Serial Number
- ✅ Hostname
- ✅ Software Version
- ✅ Management IP and Interface

**Sync Network Data (Advanced Sync):**
- ✅ **Interfaces** - Physical and logical interfaces with MAC, MTU, descriptions
- ✅ **VLANs** - VLAN name and tag extraction
- ✅ **VRFs (Route Domains)** - Route domain ID and description
- ✅ **VIPs (Virtual Servers)** - LTM virtual IPs with destination, pool, port
- ✅ **Self-IPs** - IP addresses assigned to VLANs
- ✅ **Pools** - LTM load balancer pools with members and monitors
- ✅ **Nodes** - Backend server definitions
- ✅ **SNAT Pools** - Source NAT pools
- ✅ **Trunks (LAGs)** - Link aggregation groups
- ✅ **Cables** - LLDP neighbor discovery
- ✅ **Software Version** - Version synchronization

#### Palo Alto PAN-OS Support (`paloalto_panos.yml`)

**Sync Devices:**
- ✅ Manufacturer, Model, Serial, Hostname, Version

**Sync Network Data:**
- ✅ **Interfaces** - Physical, logical, sub-interfaces with IPs and VLANs
- ✅ **VRFs** - Virtual routers with interface mapping
- ✅ **VLANs** - VLAN tags from interface configurations
- ✅ **Cables** - LLDP neighbor discovery
- ✅ **Software Version** - PAN-OS version synchronization

### Troubleshooting Installation

**Issue: Files not found after mounting**
- Verify the paths in `docker-compose.yml` match your directory structure
- Check Python version in path (`python3.11` vs `python3.10`, etc.)
- Ensure files have correct permissions (readable)

**Issue: "has missing definitions in command_mapper YAML file"**
- Verify YAML files are in the correct directory
- For Git repositories: Ensure "Provides" is set to "Network Sync Job Command Mappers"
- Check that Git repository is synced: **Extensibility → Git Repositories → [Your Repo] → Sync**

**Issue: F5 device shows "unsupported platform set"**
- **REQUIRED:** Apply plugin patches (see Step 5 in Option 2)
- Verify `NETWORK_DRIVERS` override is in `nautobot_config.py`
- Restart services after configuration changes

**Issue: Commands execute but data not extracted**
- Check job logs for parsing errors
- Verify YAML syntax is correct
- Test post-processors locally (see Testing section)

### Next Steps

- See platform-specific sections below for detailed configuration
- Review `SCHEMA_REFERENCE.md` for YAML schema details
- Test with a device using "Sync Devices From Network" job
- Run "Sync Network Data From Network" for advanced data extraction

## Understanding Network Driver Mappings (CRITICAL)

### How Device Onboarding Connects to Devices

The Nautobot Device Onboarding plugin uses a multi-step process to connect to devices and execute commands:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Device Onboarding Flow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Platform Selection (Nautobot UI)                                        │
│     └─> Platform has `network_driver` field (e.g., "bigip_f5")              │
│                                                                              │
│  2. YAML File Loading                                                        │
│     └─> Plugin loads: `<network_driver>.yml` (e.g., "bigip_f5.yml")         │
│                                                                              │
│  3. Netmiko Driver Resolution                                                │
│     └─> Plugin looks up: network_driver_mappings["netmiko"]                 │
│     └─> Default comes from `netutils` library                               │
│     └─> Can be OVERRIDDEN in `nautobot_config.py` via NETWORK_DRIVERS       │
│                                                                              │
│  4. SSH Connection via Netmiko                                               │
│     └─> Netmiko.ConnectHandler(device_type=<resolved_driver>)               │
│                                                                              │
│  5. Command Execution                                                        │
│     └─> Commands from YAML file are sent to device                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Problem: Netmiko Driver Mismatch

The `netutils` library provides default mappings from Nautobot's `network_driver` to various automation libraries. However, **these defaults don't always match what Netmiko actually expects**.

**Example - F5 BIG-IP:**
| Component | Value | Notes |
|-----------|-------|-------|
| Nautobot Platform `network_driver` | `bigip_f5` | Standard netutils name |
| YAML Override File | `bigip_f5.yml` | Named after `network_driver` |
| Default `netutils` netmiko mapping | `bigip_f5` | From netutils library |
| **What Netmiko actually expects** | `f5_tmsh` | ⚠️ MISMATCH! |

When Netmiko receives `device_type="bigip_f5"`, it throws:
```
Unsupported 'device_type' currently supported platforms are: ... f5_linux f5_ltm f5_tmsh ...
```

### The Solution: NETWORK_DRIVERS Override in nautobot_config.py

**DO NOT** change the platform's `network_driver` field in Nautobot's UI or API. This would break the YAML file loading (which relies on `network_driver` for the filename).

**INSTEAD**, override the Netmiko driver mapping in `nautobot_config.py`:

```python
# nautobot_config.py

# NETWORK_DRIVERS - Override network driver mappings for specific libraries
# This tells Nautobot: "When the platform's network_driver is 'bigip_f5',
# use 'f5_tmsh' as the Netmiko device_type instead of the netutils default."
NETWORK_DRIVERS = {
    "netmiko": {
        "bigip_f5": "f5_tmsh",  # F5 BIG-IP: Netmiko requires f5_tmsh
        # Add more overrides here as needed:
        # "some_platform": "netmiko_device_type",
    },
}
```

### Why This Architecture?

1. **YAML File Naming**: Files are named after `network_driver` (e.g., `bigip_f5.yml`)
   - This keeps naming consistent with Nautobot's platform model
   - Multiple platforms can share the same `network_driver` and use the same YAML

2. **Library-Specific Drivers**: Different libraries have different driver names
   - Netmiko: `f5_tmsh`, `cisco_ios`, `arista_eos`
   - NAPALM: `f5`, `ios`, `eos`
   - Ansible: `f5networks.f5_bigip.bigip`, `cisco.ios.ios`

3. **Override Flexibility**: `NETWORK_DRIVERS` allows per-library customization
   - Override just Netmiko without affecting NAPALM or Ansible
   - Add new platform mappings without modifying plugin code

### Common Netmiko Driver Mappings

| Nautobot `network_driver` | Netmiko `device_type` | Override Needed? |
|---------------------------|----------------------|------------------|
| `cisco_ios` | `cisco_ios` | No |
| `cisco_nxos` | `cisco_nxos` | No |
| `arista_eos` | `arista_eos` | No |
| `juniper_junos` | `juniper_junos` | No |
| `paloalto_panos` | `paloalto_panos` | No |
| `bigip_f5` | `f5_tmsh` | **YES** |
| `linux` | `linux` | No |

### Finding Valid Netmiko Device Types

To see all valid Netmiko device types:

```python
from netmiko import ConnectHandler
from netmiko.ssh_dispatcher import CLASS_MAPPER_BASE
print(sorted(CLASS_MAPPER_BASE.keys()))
```

Or check the [Netmiko Platforms Documentation](https://github.com/ktbyers/netmiko/blob/develop/PLATFORMS.md).

### Troubleshooting Driver Issues

**Error:** `Unsupported 'device_type' currently supported platforms are: ...`

**Cause:** The resolved Netmiko driver is not a valid Netmiko device type.

**Fix:**
1. Check what driver Netmiko expects for your device
2. Add override to `nautobot_config.py`:
   ```python
   NETWORK_DRIVERS = {
       "netmiko": {
           "<your_network_driver>": "<valid_netmiko_device_type>",
       },
   }
   ```
3. Restart Nautobot services: `docker-compose restart nautobot celery_worker`

**Reference:** [Nautobot NETWORK_DRIVERS Documentation](https://docs.nautobot.com/projects/core/en/stable/user-guide/administration/configuration/settings/#network_drivers)

### Plugin Bug: Netmiko Device Type vs Network Driver Mismatch

**Version Affected:** nautobot-device-onboarding 4.4.1 (and likely earlier versions)

**⚠️ CRITICAL:** This bug **MUST** be fixed with patches for F5 BIG-IP to work. The YAML file alone is not sufficient.

**The Bug:**

There is a bug in the Device Onboarding plugin where:
1. `inventory_creator.py` sets `task.host.platform` to the resolved **Netmiko device_type** (e.g., `f5_tmsh`)
2. `command_getter.py` validates `task.host.platform` against Nautobot's **network_driver list** (e.g., `bigip_f5`)

These don't match for platforms like F5, causing "unsupported platform set" errors.

**The Fix: Plugin Patches (REQUIRED)**

This repository includes patched versions of the affected files in `patches/`:

```
onboarding_override/
├── patches/
│   ├── command_getter.py    # Validates using original_network_driver
│   └── inventory_creator.py  # Stores original_network_driver in host.data
└── onboarding_command_mappers/
    ├── f5_tmsh.yml
    ├── paloalto_panos.yml
    └── ...
```

**How to Apply Patches:**

**For Development/Testing (Docker Compose):**
```yaml
volumes:
  # Plugin patches for F5 and other platforms
  - "./onboarding_override/patches/command_getter.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/command_getter.py:ro"
  - "./onboarding_override/patches/inventory_creator.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/inventory_creator.py:ro"
```

**For Production (Standard Nautobot):**
- See "Quick Start: Setting Up F5 in Standard Nautobot" section above for options
- Recommended: Create a custom Docker image with patches included
- Alternative: Fork the plugin and apply patches, then install your fork

**How the Patches Work:**

1. `inventory_creator.py` now stores `original_network_driver` (e.g., `bigip_f5`) in `host.data['original_network_driver']`
2. `command_getter.py` validates using `original_network_driver` instead of `task.host.platform`
3. YAML lookups and Netmiko connections still use the correct device type (`f5_tmsh`)

**Note:** These patches should be submitted upstream as a PR to fix the bug in the plugin. Until then, they are required for F5 BIG-IP onboarding to work.

---

## Supported Platforms

### Palo Alto PAN-OS (`paloalto_panos.yml`)

**Status:** ✅ Production Ready  
**Version:** v2.4  
**Tested:** PAN-OS 8.0+ (tested on PAN-OS 10.x)

#### Requirements

**Nautobot Configuration:**

This override requires specific Nautobot configuration for proper operation. Add the following to your `nautobot_config.py`:

```python
PLUGINS_CONFIG = {
    # Note: nautobot_device_onboarding uses nautobot_plugin_nornir connection options
    # Configure Netmiko options in nautobot_plugin_nornir, not in nautobot_device_onboarding
    "nautobot_plugin_nornir": {
        "connection_options": {
            "netmiko": {
                "extras": {
                    # Netmiko connection options for slow devices (like Palo Alto)
                    "read_timeout": 60,  # Increase from default 20s for slow devices
                    "timeout": 90,  # Connection timeout
                    "banner_timeout": 60,  # Banner timeout
                    "global_delay_factor": 3,  # Slow down command execution
                    "fast_cli": False,  # Disable fast CLI mode for better compatibility
                }
            }
        }
    }
}
```

**Important:** Do not use `read_timeout_override` - it is not a valid Netmiko parameter and will cause connection errors.

After updating the configuration, restart Nautobot services:
```bash
docker-compose restart nautobot celery_worker
```

**Required Device Access:**
- SSH access to the Palo Alto device
- Read access to execute: `show system info`, `show config running`, `show lldp neighbors all`
- Device must have proper SSH credentials configured in Nautobot Secrets Groups

**Nautobot Jobs:**
- **Initial Onboarding:** "Sync Devices From Network" job (UUID: `fd72f5d7-622e-4e4b-98e4-b7216b732082`)
- **Advanced Sync:** "Sync Network Data From Network" job (UUID: `8b7047c3-f311-44e6-8404-54ea5b95d9e9`)

#### Features

**Sync Devices (Initial Onboarding):**
- ✅ Manufacturer extraction (Palo Alto Networks)
- ✅ Model extraction from `show system info`
- ✅ Serial number extraction
- ✅ Hostname extraction
- ✅ Software version extraction

**Sync Network Data (Advanced Sync):**
- ✅ **Interfaces:**
  - Physical interfaces (ethernet1/1, ethernet1/10, etc.)
  - Logical/sub-interfaces (ethernet1/12.10, ethernet1/12.11, etc.)
  - Management interface (`mgmt`)
  - Loopback and tunnel interfaces
  - Interface descriptions
  - IP address extraction with CIDR notation
  - VLAN tag extraction for sub-interfaces
  - 802.1Q mode detection (access/tagged)
  - Tagged VLAN assignments for trunk interfaces
  - Untagged VLAN assignments for access interfaces
  
- ✅ **Virtual Routers (VRFs):**
  - Extraction of all virtual routers from running config
  - VRF-to-interface mapping
  - Automatic assignment of interfaces to VRFs
  
- ✅ **VLANs:**
  - Extraction of VLAN tags from interface configurations
  - Automatic VLAN creation with naming convention (VLAN{tag})
  
- ✅ **Software Version:**
  - Extraction of PAN-OS version from `show system info`
  - Creates Software Version objects in Nautobot
  
- ✅ **Cables:**
  - LLDP neighbor discovery via `show lldp neighbors all`
  - Automatic cable creation between interfaces
  - Remote device and interface identification

**Interface Type Detection:**
- Physical interfaces: `1000base-t`
- Logical interfaces (sub-interfaces, loopbacks, tunnels, mgmt): `virtual`

#### Known Limitations

- ⚠️ **MAC Addresses:** Not available from running config, defaults to empty string
- ⚠️ **Link Status:** Defaults to `true` (not available in running config, requires operational state)
- ⚠️ **MTU:** Defaults to `1500` (not parsed from config, can be customized if needed)
- ⚠️ **Software Version:** Returns `unknown` if `sw-version` line is not found in `show system info` output

#### Technical Implementation Details

**Single Command Limitation Workaround:**
Due to a limitation in the `nautobot-device-onboarding` plugin where it does not properly merge outputs from multiple commands with different `jpath` values, this override uses a single comprehensive command (`show config running`) and parses all interface, VRF, and VLAN data using complex Jinja2 post-processors.

**Jinja2 Parsing Strategy:**
- Uses brace-level tracking to parse nested PAN-OS configuration structure
- Maintains state using Jinja2 `namespace()` for complex multi-pass parsing
- Handles parent/sub-interface relationships by analyzing interface names
- Maps VRFs to interfaces by tracking virtual-router sections

**Important: jpath Configuration:**

The `jpath` field behaves differently depending on the section:

- **For `sync_devices`:** Use `jpath: "@"` with `parser: "raw"`. The plugin may pass `obj` as either a string or a dictionary (`{"raw": "..."}`), so your post-processor must handle both cases using: `{%- set raw_obj = obj.get('raw', obj) if obj is mapping else obj -%}`

- **For `sync_network_data`:** Use `jpath: "raw"` with `parser: "raw"`. This ensures you get the raw string output directly, and `obj` will always be a string.

**Example:**
```yaml
# sync_devices - handles both formats
sync_devices:
  hostname:
    commands:
      - command: "show system info"
        parser: "raw"
        jpath: "@"  # Works - handles both string and dict
        post_processor: |
          {%- set raw_obj = obj.get('raw', obj) if obj is mapping else obj -%}
          {%- set lines = raw_obj.replace('\r', '').split('\n') -%}
          ...

# sync_network_data - direct string access
sync_network_data:
  serial:
    commands:
      - command: "show system info"
        parser: "raw"
        jpath: "raw"  # Required - gets raw string directly
        post_processor: |
          {%- set lines = obj.replace('\r', '').split('\n') -%}
          ...
```

**Documentation:**
- See `SCHEMA_REFERENCE.md` for detailed schema documentation
- See project root for troubleshooting guides and validation reports

### F5 BIG-IP (`f5_tmsh.yml`)

**Status:** ✅ Production Ready  
**Version:** v1.0  
**Tested:** BIG-IP 12.x - 17.x (TMOS), tested on 17.5.1.3

#### Quick Start: Setting Up F5 in Standard Nautobot (Git Repository)

**For standard Nautobot installations using Git repositories (out of the box setup):**

1. **Add YAML Override File to Git Repository**
   - Ensure `f5_tmsh.yml` is in your Git repository under `onboarding_command_mappers/`
   - **CRITICAL:** The file MUST be named `f5_tmsh.yml` (not `bigip_f5.yml`) due to a plugin bug
   - See "Plugin Bug" section below for details

2. **Configure Nautobot Platform**
   - Navigate to: **Devices → Platforms**
   - Create or edit platform:
     - **Name:** `F5 BIG-IP` or `bigip_f5`
     - **Network Driver:** `bigip_f5` (IMPORTANT: Do NOT change to `f5_tmsh`)
     - **Manufacturer:** Create "F5" manufacturer first if it doesn't exist

3. **Add NETWORK_DRIVERS Configuration**
   - Edit your `nautobot_config.py` file
   - Add the following configuration:
   ```python
   # NETWORK_DRIVERS - Required for F5 BIG-IP onboarding
   NETWORK_DRIVERS = {
       "netmiko": {
           "bigip_f5": "f5_tmsh",  # Override: bigip_f5 -> f5_tmsh for Netmiko
       },
   }
   ```

4. **Apply Plugin Patches (REQUIRED)**
   
   Due to a bug in nautobot-device-onboarding v4.4.1, you must apply patches to make F5 work.
   Choose one of these options:

   **Option A: Custom Docker Image (Recommended for Production)**
   - Create a custom Docker image based on the Nautobot image
   - Copy the patched files from `patches/` directory into the image:
     ```dockerfile
     FROM ghcr.io/nautobot/nautobot:latest
     COPY patches/command_getter.py /usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/
     COPY patches/inventory_creator.py /usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/
     ```
   - Build and use your custom image

   **Option B: Volume Mounts (Development/Testing)**
   - If using Docker Compose, add volume mounts to your `docker-compose.yml`:
     ```yaml
     volumes:
       - "./onboarding_override/patches/command_getter.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/command_getter.py:ro"
       - "./onboarding_override/patches/inventory_creator.py:/usr/local/lib/python3.11/site-packages/nautobot_device_onboarding/nornir_plays/inventory_creator.py:ro"
     ```

   **Option C: Fork Plugin and Apply Patches**
   - Fork the `nautobot-app-device-onboarding` repository
   - Apply the patches from `patches/` directory
   - Install your forked version: `pip install git+https://github.com/your-username/nautobot-app-device-onboarding.git`

5. **Configure Git Repository in Nautobot**
   - Navigate to: **Extensibility → Git Repositories**
   - Create new repository:
     - **Name:** `Device Onboarding Command Mappers`
     - **Remote URL:** Your Git repository URL
     - **Branch:** `main` (or your default branch)
     - **Provides:** ✅ **Network Sync Job Command Mappers** (CRITICAL)
   - Click **Sync** to pull the files

6. **Restart Nautobot Services**
   ```bash
   # Docker Compose
   docker-compose restart nautobot celery_worker
   
   # Systemd
   sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
   ```

7. **Test F5 Onboarding**
   - Navigate to: **Jobs → Sync Devices From Network**
   - Enter F5 device IP address
   - Select the `bigip_f5` platform
   - Select appropriate Secrets Group with F5 credentials
   - Run the job

#### Requirements

**CRITICAL: Netmiko Driver Override Required**

F5 BIG-IP requires special handling because:
- Nautobot `network_driver`: `bigip_f5` (standard netutils name)
- Netmiko expects: `f5_tmsh` (NOT `bigip_f5`)
- **YAML file name: `f5_tmsh.yml`** (matches Netmiko device_type, not network_driver)

**Important:** Due to a bug in the Device Onboarding plugin, the YAML file must be named
after the Netmiko device_type (`f5_tmsh.yml`), not the network_driver (`bigip_f5.yml`).
See the "Plugin Bug" section above for the required patches.

Add this to your `nautobot_config.py`:

```python
# NETWORK_DRIVERS - Required for F5 BIG-IP onboarding
NETWORK_DRIVERS = {
    "netmiko": {
        "bigip_f5": "f5_tmsh",  # Override: bigip_f5 -> f5_tmsh for Netmiko
    },
}
```

**Connection Timeout Configuration:**

F5 devices may require increased timeouts. Add to `PLUGINS_CONFIG`:

```python
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "connection_options": {
            "netmiko": {
                "extras": {
                    "timeout": 90,
                    "banner_timeout": 60,
                    "global_delay_factor": 3,
                    "fast_cli": False,
                    "allow_agent": False,  # F5 may require this
                }
            }
        }
    },
}
```

**After updating configuration:**
```bash
docker-compose restart nautobot celery_worker
```

**Platform Setup in Nautobot:**

1. Navigate to: **Devices → Platforms**
2. Create or edit platform with:
   - **Name:** `bigip_f5` or `F5 BIG-IP`
   - **Network Driver:** `bigip_f5` (IMPORTANT: Do NOT change to f5_tmsh)
   - **Manufacturer:** Create "F5" or "Bigip" manufacturer first

**Required Device Access:**
- SSH access to F5 BIG-IP device (TMSH shell)
- Read access to execute: `show sys version`, `show sys hardware`, `list sys global-settings hostname`, `list sys management-ip`, `list net interface all-properties`
- Credentials configured in Nautobot Secrets Groups

#### Features

**Sync Devices (Initial Onboarding):**
- ✅ Manufacturer extraction (F5)
- ✅ Model extraction from `show sys hardware` (e.g., "BIG-IP Virtual Edition")
- ✅ Device Type creation (e.g., "F5 BIG-IP Virtual Edition")
- ✅ Serial number extraction (Chassis Serial)
- ✅ Hostname extraction from `list sys global-settings hostname`
- ✅ Software version extraction (e.g., "17.5.1.3")
- ✅ Management IP and mask extraction
- ✅ Platform assignment (`bigip_f5`)

**Sync Network Data (Advanced Sync):**
- ✅ **Interfaces:**
  - Physical interfaces (1.0, 1.1, etc.)
  - Management interface (`mgmt`)
  - MAC address extraction
  - MTU extraction
  - Link status detection
  - Interface descriptions

- ✅ **VLANs:**
  - VLAN name and tag extraction
  - VLAN status

- ✅ **Route Domains (VRFs):**
  - Route domain ID and name extraction
  - Default route domain handling
  - Maps to Nautobot VRFs

- ✅ **VIPs (Virtual Servers):**
  - LTM virtual server extraction
  - Destination IP:port
  - Pool assignment
  - Description and enabled state
  - Maps to Nautobot IP Addresses (type: vip)

- ✅ **Self-IPs:**
  - IP addresses assigned to VLANs
  - Traffic group assignment
  - Allow service configuration
  - Maps to Nautobot IP Addresses

- ✅ **Pools:**
  - LTM load balancer pools
  - Pool members (backend servers)
  - Health monitor configuration
  - Load balancing method

- ✅ **Nodes:**
  - Backend server definitions
  - Node addresses
  - Monitor configuration
  - Descriptions

- ✅ **SNAT Pools:**
  - Source NAT pools
  - Member addresses

- ✅ **Trunks (LAGs):**
  - Link aggregation groups
  - Interface members
  - LACP mode configuration

- ✅ **Cables:**
  - LLDP neighbor discovery

- ✅ **Software Version:**
  - Version extraction for Nautobot Software Version objects

#### Commands Used

| Field | Command | Output Format |
|-------|---------|---------------|
| Model/Serial | `show sys hardware` | Space-separated key-value |
| Version | `show sys version` | Space-separated key-value |
| Hostname | `list sys global-settings hostname` | Curly-brace config block |
| Management IP | `list sys management-ip` | Curly-brace config block |
| Interfaces | `list net interface all-properties` | Curly-brace config blocks |
| VLANs | `list net vlan` | Curly-brace config blocks |
| Route Domains | `list net route-domain` | Curly-brace config blocks |
| VIPs | `list ltm virtual` | Curly-brace config blocks |
| Self-IPs | `list net self` | Curly-brace config blocks |
| Pools | `list ltm pool` | Curly-brace config blocks |
| Nodes | `list ltm node` | Curly-brace config blocks |
| SNAT Pools | `list ltm snatpool` | Curly-brace config blocks |
| Trunks | `list net trunk` | Curly-brace config blocks |
| LLDP Neighbors | `show net lldp-neighbors` | Tabular/key-value |

#### Known Limitations

- ⚠️ **VLAN Interface Assignments:** Not linked to interfaces (VLANs are extracted but not mapped to specific interfaces)
- ⚠️ **HA Status:** Not extracted (high availability status not currently supported)
- ⚠️ **Pool Member Details:** Pool members are extracted as addresses but detailed member configuration (port, priority) not parsed
- ⚠️ **Virtual Server Profiles:** Virtual server profiles (SSL, HTTP, etc.) not extracted

#### Troubleshooting

**Error: "Unsupported 'device_type' currently supported platforms are: ..." or "has a unsupported platform set"**
- **Cause 1:** Plugin patches not applied (REQUIRED for F5)
  - **Fix:** Apply the patches from `patches/` directory (see "Plugin Bug" section above)
  - Use custom Docker image, volume mounts, or forked plugin
- **Cause 2:** Missing `NETWORK_DRIVERS` override in `nautobot_config.py`
  - **Fix:** Add `NETWORK_DRIVERS = {"netmiko": {"bigip_f5": "f5_tmsh"}}`
- **Restart:** `docker-compose restart nautobot celery_worker` (or restart systemd services)

**Error: "Serial [] is not of type 'string'"**
- **Cause:** Command execution failed (connection issue or plugin bug)
- **Fix:** 
  1. Verify plugin patches are applied (see above)
  2. Check SSH connectivity, credentials, and timeout settings
  3. Verify YAML file is named `f5_tmsh.yml` (not `bigip_f5.yml`)

**Error: "Unable to load Manufacturer due to a missing key"**
- **Cause:** Commands didn't execute (driver mismatch or plugin bug)
- **Fix:** 
  1. Verify plugin patches are applied
  2. Verify `NETWORK_DRIVERS` override is in `nautobot_config.py`
  3. Check that YAML file `f5_tmsh.yml` exists in Git repository and is synced

**Error: "has missing definitions in command_mapper YAML file"**
- **Cause:** YAML file not found or wrong filename
- **Fix:** 
  1. Ensure file is named `f5_tmsh.yml` (not `bigip_f5.yml`)
  2. Verify Git repository is synced in Nautobot
  3. Check that "Provides" field is set to "Network Sync Job Command Mappers"

### Linux (`linux.yml`)

**Status:** ⚠️ Needs Testing  
**Note:** File present but not validated

## Git Repository Setup in Nautobot

### 1. Create Git Repository

1. Navigate to: **Extensibility → Git Repositories**
2. Click **Add** to create a new repository
3. Configure:
   - **Name:** `Device Onboarding Command Mappers` (or your preferred name)
   - **Slug:** `device-onboarding-mappers` (auto-generated)
   - **Remote URL:** Your Git repository URL
   - **Branch:** `main` (or your default branch)
   - **Provides:** ✅ **Network Sync Job Command Mappers** (CRITICAL)
   - **Username/Token:** If repository is private

### 2. Verify Repository Structure

The repository must have:
- Root directory: `onboarding_command_mappers/`
- YAML files: `<network_driver>.yml` inside `onboarding_command_mappers/`

**⚠️ Special Note for F5 BIG-IP:**
- The YAML file MUST be named `f5_tmsh.yml` (not `bigip_f5.yml`) due to a plugin bug
- See the F5 BIG-IP section for complete setup instructions including required plugin patches

### 3. Sync Repository

1. After creating the repository, click **Sync** to pull the files
2. Verify the files appear in: **Extensibility → Git Repositories → [Your Repo] → Files**
3. The plugin will automatically use these overrides instead of default command mappers

**⚠️ Important for F5:** After syncing the Git repository, you must also apply the plugin patches (see F5 BIG-IP section). The YAML file alone is not sufficient.

## File Naming Convention

YAML files must be named: `<network_driver>.yml`

Where `network_driver` must match a network driver in Nautobot's netutils mapping.

To check available network drivers:
```python
from nautobot.dcim.utils import get_all_network_driver_mappings
sorted(list(get_all_network_driver_mappings().keys()))
```

## YAML File Format

Each YAML file defines commands and post-processors for extracting device data:

```yaml
---
sync_devices:
  hostname:
    commands:
      - command: "show system info"
        parser: "raw"
        jpath: "@"  # Use "@" for sync_devices
        post_processor: |
          {%- set raw_obj = obj.get('raw', obj) if obj is mapping else obj -%}
          {%- set lines = raw_obj.replace('\r', '').split('\n') -%}
          {%- set ns = namespace(result='') -%}
          {%- for line in lines -%}
            {%- if 'hostname:' in line.lower() and not ns.result -%}
              {%- set parts = line.split(':', 1) -%}
              {%- if parts | length > 1 -%}
                {%- set ns.result = parts[1].strip() -%}
              {%- endif -%}
            {%- endif -%}
          {%- endfor -%}
          {{ ns.result }}

sync_network_data:
  interfaces:
    commands:
      - command: "show config running"
        parser: "raw"
        jpath: "raw"
        post_processor: |
          {# Jinja2 template to parse and transform data #}
          {{ interfaces | tojson }}
```

### Key Components

- **`sync_devices`** - Basic device information (manufacturer, model, serial, hostname, version)
- **`sync_network_data`** - Detailed network data (interfaces, IPs, VLANs, VRFs)
- **`commands`** - List of CLI commands to execute
- **`parser`** - Parser type (`textfsm`, `pyats`, `ttp`, `raw`, `none`)
- **`jpath`** - JMESPath expression to extract data:
  - For `sync_devices`: Use `"@"` with `parser: "raw"` (handles both string and dict outputs)
  - For `sync_network_data`: Use `"raw"` with `parser: "raw"` (gets raw string directly)
- **`post_processor`** - Jinja2 template to transform extracted data

## Important Notes

### Partial Merging Not Supported

⚠️ **Warning:** The plugin does NOT support partial YAML file merging. You cannot override only `sync_devices` and inherit `sync_network_data` from defaults. You must provide complete definitions for each section you want to customize.

### File Priority

The plugin will **always prefer** platform-specific YAML files loaded from the Git repository over default command mappers in the plugin source code.

## Testing

### Local Testing

Use the test script in the project root to validate YAML files:

```bash
python test_palo_parser.py
```

This will:
- Load the YAML override file
- Execute the Jinja2 post-processor
- Validate output against expected schema
- Generate a detailed report

### Nautobot Testing

1. Sync the Git repository in Nautobot
2. Run "Sync Devices From Network" or "Sync Network Data From Network" job
3. Check job logs for any errors
4. Verify device and interfaces are created correctly

## Contributing

### Adding a New Platform

1. Create `<network_driver>.yml` in `onboarding_command_mappers/`
2. Follow the schema defined in `SCHEMA_REFERENCE.md`
3. Test locally using the test script
4. Document platform-specific notes in this README
5. Commit and push to the repository

### Updating Existing Platform

1. Edit the `<network_driver>.yml` file
2. Test locally
3. Update version number in file header
4. Update this README with changes
5. Commit and push to the repository

## Documentation

- **Schema Reference:** `SCHEMA_REFERENCE.md` - Detailed schema documentation
- **Troubleshooting:** See project root for troubleshooting guides
- **Official Docs:** [Nautobot Device Onboarding Documentation](https://docs.nautobot.com/projects/device-onboarding/en/latest/user/app_yaml_overrides/)

## Version History

### Palo Alto PAN-OS (paloalto_panos.yml)

- **v2.4** (2026-01-02) - jpath and VRF/VLAN Fixes
  - ✅ Fixed `jpath` from `"@"` to `"raw"` for VRFs, VLANs, cables, serial, and software_version sections in `sync_network_data`
  - ✅ Ensured consistent `jpath: "raw"` usage across all `sync_network_data` sections
  - ✅ Maintained `jpath: "@"` for `sync_devices` sections (works correctly with proper output handling)
  - ✅ Fixed VRF and VLAN extraction by correcting jpath configuration
  - ✅ Documented correct jpath usage patterns for both sections

- **v2.3** (2026-01-02) - Configuration and sync_devices Fixes
  - ✅ Fixed `sync_devices` post-processors to use `namespace()` for consistent value returns
  - ✅ Changed management interface name to `"mgmt"` for compatibility
  - ✅ Updated configuration to use only `nautobot_plugin_nornir` connection options
  - ✅ Removed invalid `read_timeout_override` parameter
  - ✅ Enhanced Jinja2 templates to handle both string and dict-wrapped outputs
  - ✅ Production tested and validated on fresh Nautobot installations

- **v2.2** (2026-01-01) - Advanced Network Data Sync
  - ✅ Added comprehensive `sync_network_data` section
  - ✅ Software version extraction and synchronization
  - ✅ VRF extraction and interface-to-VRF mapping
  - ✅ VLAN extraction with automatic VLAN creation
  - ✅ LLDP-based cable discovery
  - ✅ Enhanced interface parsing with sub-interface support
  - ✅ Management interface (`mgmt`) handling
  - ✅ Improved 802.1Q mode detection (access/tagged)
  - ✅ Tagged and untagged VLAN assignments
  - ✅ Fixed YAML indentation for proper plugin loading
  - ✅ Production tested and validated

- **v2.1** (2025-12-31) - Production ready
  - Added trunk interface detection
  - VRF parsing (disabled for plugin compatibility)
  - Full interface type support
  - Schema validation passed

- **v2.0** (2025-12-30) - Initial production version
  - Basic device onboarding
  - Interface parsing
  - IP address extraction
  - VLAN tag extraction

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
1. Check `SCHEMA_REFERENCE.md` for schema details
2. Review troubleshooting guides in project root
3. Check Nautobot job logs for specific errors
4. Consult [Nautobot Device Onboarding Documentation](https://docs.nautobot.com/projects/device-onboarding/en/latest/)

### F5 BIG-IP (f5_tmsh.yml)

- **v1.1** (2026-01-08) - Enhanced Network Data Sync
  - ✅ Added VIPs (Virtual Servers) extraction - LTM virtual IPs with destination, pool, port
  - ✅ Added Self-IPs extraction - IP addresses on VLANs with traffic groups
  - ✅ Added Pools extraction - LTM load balancer pools with members and monitors
  - ✅ Added Nodes extraction - Backend server definitions
  - ✅ Added SNAT Pools extraction - Source NAT pools
  - ✅ Added Trunks extraction - Link aggregation groups (LAGs)
  - ✅ Created `bigip_f5.yml` copy for platform compatibility
  - ✅ Comprehensive F5 LTM data synchronization

- **v1.0** (2026-01-08) - Initial Production Release
  - ✅ Full `sync_devices` support (manufacturer, model, device_type, serial, hostname, version)
  - ✅ Management IP and mask extraction
  - ✅ `sync_network_data` for interfaces, VLANs, route domains, cables
  - ✅ Created plugin patches to fix Netmiko device_type vs network_driver bug
  - ✅ YAML file named `f5_tmsh.yml` (matches Netmiko device_type)
  - ✅ Tested on BIG-IP 17.5.1.3 Virtual Edition

---

**Last Updated:** January 8, 2026  
**Current Version:** Palo Alto v2.4, F5 BIG-IP v1.1

