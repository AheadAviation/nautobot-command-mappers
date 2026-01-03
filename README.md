# Nautobot Device Onboarding Command Mappers

This repository contains YAML override files for the Nautobot Device Onboarding plugin. These files define how to extract device and network data from various network platforms.

## Repository Structure

```
.
├── README.md
└── onboarding_command_mappers
    └── <network_driver>.yml
```

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
- When using `parser: "raw"`, always use `jpath: "raw"` (not `jpath: "@"`)
- The `"raw"` jpath correctly returns the raw string output for post-processing
- Using `jpath: "@"` with raw parser output may cause parsing failures

**Documentation:**
- See `SCHEMA_REFERENCE.md` for detailed schema documentation
- See project root for troubleshooting guides and validation reports

### F5 BIG-IP (`bigip_f5.yml`)

**Status:** ⚠️ Needs Testing  
**Note:** File present but not validated

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

### 3. Sync Repository

1. After creating the repository, click **Sync** to pull the files
2. Verify the files appear in: **Extensibility → Git Repositories → [Your Repo] → Files**
3. The plugin will automatically use these overrides instead of default command mappers

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
        jpath: "raw"
        post_processor: |
          {%- set lines = obj.replace('\r', '').split('\n') -%}
          {%- for line in lines -%}
            {%- if 'hostname:' in line.lower() -%}
              {{ line.split(':', 1)[1].strip() }}
            {%- endif -%}
          {%- endfor -%}

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
- **`jpath`** - JMESPath expression to extract data (use `"raw"` with `parser: raw` to get the raw string output)
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
  - ✅ Fixed `jpath` from `"@"` to `"raw"` for VRFs, VLANs, cables, serial, and software_version sections
  - ✅ Ensured consistent `jpath: "raw"` usage across all `sync_network_data` sections
  - ✅ Fixed VRF and VLAN extraction by correcting jpath configuration
  - ✅ All sections now consistently use `jpath: "raw"` with `parser: "raw"` for proper data extraction

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

[Specify your license here]

## Support

For issues or questions:
1. Check `SCHEMA_REFERENCE.md` for schema details
2. Review troubleshooting guides in project root
3. Check Nautobot job logs for specific errors
4. Consult [Nautobot Device Onboarding Documentation](https://docs.nautobot.com/projects/device-onboarding/en/latest/)

---

**Last Updated:** January 2, 2026

