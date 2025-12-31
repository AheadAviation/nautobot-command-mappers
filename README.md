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
**Version:** v2.1  
**Tested:** PAN-OS 10.x

**Features:**
- Device information extraction (manufacturer, model, serial, hostname, version)
- Interface discovery (physical, subinterfaces, management)
- IP address extraction with CIDR notation
- VLAN tag extraction for subinterfaces
- Virtual Router (VRF) parsing (manual assignment required)
- Trunk/access mode detection
- Management interface identification

**Known Limitations:**
- VRF assignments must be done manually in Nautobot after onboarding (plugin limitation)
- MAC addresses not available from running config
- Link status defaults to `true` (not available in running config)

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
- **`jpath`** - JMESPath expression to extract data (use `raw` with `parser: raw`)
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

**Last Updated:** December 31, 2025

