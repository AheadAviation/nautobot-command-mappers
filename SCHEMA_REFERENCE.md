# Nautobot Device Onboarding YAML Schema (Golden Reference - Updated)

**Status:** Verified Working (Dec 30, 2025)  
**Platform Context:** Palo Alto PAN-OS (applies generally to v4.0+ SSoT)

This reference documents the schema used in a successful override. Unlike previous versions, this confirms that **`sync_network_data`** can process multiple CLI commands independently as sibling keys.

Use this for:
- **Sync Devices From Network** (basic onboarding)
- **Sync Network Data From Network** (enhanced SSoT job)

## Top-Level Structure

```yaml
---
sync_devices:        # Phase 1: Basic Device Creation
  manufacturer: ...  # Returns String
  model: ...         # Returns String
  hostname: ...      # Returns String
  serial: ...        # Returns String (CRITICAL)
  version: ...       # Returns String
  mgmt_ip: ...       # Returns String (Optional)

sync_network_data:   # Phase 2: SSoT / Detailed Sync
  serial:            # Returns String (Redundant validation for SSoT)
    commands: ...    
    post_processor: "string"

  interfaces:        # Returns JSON Dictionary (See Schema Below)
    commands: ...
    post_processor: "json_dict"
```

**Key Insight:** `sync_network_data` supports **multiple independent keys** (`serial`, `interfaces`, etc.). Each key is processed separately. You do **not** need to combine serial and interfaces into one command output.

## 1. `sync_devices` (Device Creation)

These keys populate the basic **Device** model. The post_processor must return a simple **String** (or empty string).

| YAML Key | Nautobot Field | Required? | Notes |
| --- | --- | --- | --- |
| **manufacturer** | `manufacturer.name` | Yes | e.g. "Palo Alto Networks" |
| **model** | `device_type.model` | Yes | Used with manufacturer to auto-create DeviceType |
| **hostname** | `device.name` | Yes | The device name |
| **serial** | `device.serial` | Strongly Recommended | **MUST use `serial`** — `serial_number` is ignored |
| **version** | Software version | Optional | e.g. "10.2.3" or "10.1.6-h6" |
| **mgmt_ip** | `device.primary_ip` | Optional | Plugin attempts to assign |
| **role** | `device.device_role` | Optional | Best set via job/config |
| **platform** | `device.platform` | Optional | Usually set via job selection |

**Jinja Pattern (String Extraction):**

```jinja
{%- set lines = obj.replace('\r', '').split('\n') -%}
{%- set result = '' -%}
{%- for line in lines -%}
  {%- if 'target:' in line.lower() -%}
    {%- set parts = line.split(':', 1) -%}
    {%- if parts | length > 1 -%}
      {%- set result = parts[1].strip() -%}
    {%- endif -%}
  {%- endif -%}
{%- endfor -%}
{{ result }}
```

**Important:** Always return a string (even an empty one) to prevent `NoneType` errors in subsequent processing.

## 2. `sync_network_data` (SSoT/Detail Sync)

This section allows **multiple independent keys**. Each key is processed separately by the plugin.

### A. Key: `serial`

**Purpose:** Provides device serial number for SSoT validation.

**Output:** A **String** (same extraction logic as `sync_devices.serial`)

**Example:**
```yaml
serial:
  commands:
    - command: "show system info"
      parser: "raw"
      jpath: "raw"
      post_processor: |
        {%- set lines = obj.replace('\r', '').split('\n') -%}
        {%- for line in lines -%}
          {%- if 'serial:' in line.lower() and ':' in line -%}
            {{ line.split(':', 1)[1].strip() }}
          {%- endif -%}
        {%- endfor -%}
```

### B. Key: `interfaces`

**Purpose:** Provides interface data for synchronization.

**Output Structure:** A **JSON Dictionary** (Hash Map) where the **key is the interface name**.

**Valid Schema:**

```json
{
  "ethernet1/1": {
    "type": "string",                // Required: "1000base-t", "lag", "virtual", "tunnel", "other"
    "mac_address": "string|null",    // Normalized xx:xx:xx:xx:xx:xx or null
    "mtu": "string",                 // "1500" (Strings are accepted)
    "description": "string",         // Empty string "" if none
    "link_status": boolean,          // Required: true/false (NOT "enabled")
    "ip_addresses": [                // List of dicts (empty [] if none)
      {
        "ip_address": "10.0.0.1",    // String
        "prefix_length": 24          // Integer
      }
    ],
    "tagged_vlans": [],              // List of VLAN IDs (must exist in Nautobot)
    "untagged_vlan": null,           // null if not applicable
    "802.1Q_mode": "string",         // "access", "tagged", or "" (NOT "mode")
    "lag": "string",                 // Parent LAG name or empty string ""
    "vrf": null,                     // null if not applicable
    "mgmt_only": boolean             // Optional: true for management interface
  },
  "management": {
    // ... same structure with mgmt_only: true
  }
}
```

**Critical Points:**
- Output is a **dictionary/map** keyed by interface name, NOT a list
- Use `link_status` (boolean), NOT `enabled`
- Use `802.1Q_mode` (string: "access", "tagged", or ""), NOT `mode`
- `mac_address` should be `null` (not empty string) if missing
- `mtu` can be a string (e.g., "1500") or integer
- Interface names should NOT be included in the dict values (the key IS the name)

**Output Pattern:**

```jinja
{%- set interfaces = {} -%}
{%- for name in interface_names -%}
  {%- set _ = interfaces.update({name: {
    'type': iface_type,
    'mac_address': mac_addr,
    'mtu': '1500',
    'description': '',
    'link_status': link_status,
    'ip_addresses': ip_list,
    'tagged_vlans': [],
    'untagged_vlan': none,
    '802.1Q_mode': mode_string,
    'lag': '',
    'vrf': none,
    'mgmt_only': false
  }}) -%}
{%- endfor -%}
{{ interfaces | tojson }}
```

## Validated Jinja Patterns (From Working Code)

### 1. MAC Address Normalization

Handles dots (`.`) removal, colon insertion, and validation of invalid strings:

```jinja
{%- set mac_addr = none -%}
{%- if raw_mac and raw_mac.strip() -%}
  {%- if '.' in raw_mac -%}
    {%- set mac_hex = (raw_mac.split('.') | join('')) | lower -%}
    {%- if mac_hex | length == 12 -%}
      {%- set mac_addr = mac_hex[0:2] ~ ':' ~ mac_hex[2:4] ~ ':' ~ mac_hex[4:6] ~ ':' ~ mac_hex[6:8] ~ ':' ~ mac_hex[8:10] ~ ':' ~ mac_hex[10:12] -%}
      {%- if mac_addr == '00:00:00:00:00:00' -%}
        {%- set mac_addr = none -%}
      {%- endif -%}
    {%- endif -%}
  {%- else -%}
    {%- set mac_addr = raw_mac | lower -%}
    {%- if mac_addr == '00:00:00:00:00:00' -%}
      {%- set mac_addr = none -%}
    {%- endif -%}
  {%- endif -%}
{%- endif -%}
{# Additional validation #}
{%- if mac_addr and mac_addr != none -%}
  {%- if ':' not in mac_addr or mac_addr | length != 17 or mac_addr.lower() in ['ha', 'n/a', 'untrust', 'zone', 'name'] -%}
    {%- set mac_addr = none -%}
  {%- endif -%}
{%- endif -%}
```

### 2. Interface Type Mapping

Determine type based on naming convention:

```jinja
{%- set iface_type = '1000base-t' if 'ethernet' in name.lower() 
    else ('lag' if name.startswith('ae') 
    else ('tunnel' if name.startswith('tunnel') 
    else ('virtual' if '.' in name or 'vlan' in name.lower() or 'loopback' in name.lower() 
    else 'other'))) -%}
```

### 3. Namespace Management

Using `namespace()` is required to maintain state across loops in Jinja:

```jinja
{%- set ns = namespace(
    hardware={}, 
    ips={}, 
    mtus={},
    all_interfaces=[],
    in_hardware=false,
    in_logical=false,
    header_found=false
) -%}
```

### 4. Conditional 802.1Q_mode Setting

For L3 interfaces, omit or use empty string; for L2-capable interfaces, set appropriately:

```jinja
{%- set is_ethernet = 'ethernet' in name.lower() -%}
{%- set is_l2_capable = is_ethernet and not name.startswith('dedicated-ha') and not name.startswith('ae') -%}
{%- set iface_dict = {
    'type': iface_type,
    # ... other fields ...
} -%}
{%- if is_l2_capable -%}
  {%- set _ = iface_dict.update({'802.1Q_mode': 'access'}) -%}
{%- endif -%}
```

### 5. Adding Management Interface

Include the management interface directly in the interfaces dictionary:

```jinja
{%- set _ = interfaces.update({'management': {
    'type': '1000base-t',
    'mac_address': 'e8:98:6d:9e:8a:00',  # Extract from device if possible
    'mtu': '1500',
    'description': 'Out-of-Band Management Interface',
    'link_status': true,
    'ip_addresses': [{'ip_address': '192.168.11.16', 'prefix_length': 24}],
    'tagged_vlans': [],
    'untagged_vlan': none,
    '802.1Q_mode': '',
    'lag': '',
    'vrf': none,
    'mgmt_only': true
}}) -%}
```

## Common Pitfalls & Solutions

1. **Multiple Commands Don't Merge Properly (CRITICAL LIMITATION)**
   - **Issue:** When using multiple commands in a `commands` array with different `jpath` values, the plugin does **NOT** merge the outputs. The `jpath` field is interpreted as a JMESPath expression for parsing, not as a key for merging multiple command outputs.
   - **Error Example:** `Schema validation failed - Error: '\n\n\n...' is not of type 'object'` when attempting to use multiple commands with different `jpath` values.
   - **Solution:** Use a **single command** that returns all needed data, then parse it with Jinja2. For Palo Alto PAN-OS, use `show config running` to get all interface configurations (including management) in one output, then parse the hierarchical config format.
   - **Workaround:** If you need data from multiple commands, you must parse it all from a single command output using Jinja2 post-processing.

2. **"serial is a required property" Error**
   - **Cause:** Missing `serial` key under `sync_network_data`
   - **Solution:** Add `serial` as a sibling key to `interfaces` in `sync_network_data`

3. **"Schema validation failed" - Interface Structure**
   - **Cause:** Returning a list instead of a dictionary, or including `name` field in interface dicts
   - **Solution:** Output `{{ interfaces | tojson }}` where `interfaces` is a dict keyed by interface name

4. **"null value in column 'mode' violates not-null constraint"**
   - **Cause:** Using `mode` instead of `802.1Q_mode`, or setting `802.1Q_mode` to `null`
   - **Solution:** Use `802.1Q_mode` with value `""` (empty string) for L3 interfaces, or omit it entirely for non-L2 interfaces

5. **Management Interface Not Created**
   - **Cause:** Management interface data may be in a different command output, but multiple commands don't merge
   - **Solution:** Include the management interface data in the same single command output and parse it within your Jinja2 template. Include the management interface directly in the main `interfaces` dictionary output with `mgmt_only: true`.

6. **MAC Address Validation Errors**
   - **Cause:** Invalid MAC format or placeholder values like "00:00:00:00:00:00"
   - **Solution:** Set `mac_address: null` for virtual interfaces or invalid MACs

## Checklist for New Overrides

- [ ] **Separate Serial:** Ensure `serial` is defined in *both* `sync_devices` and `sync_network_data`
- [ ] **Structure:** `interfaces` post-processor outputs `{{ interfaces | tojson }}` (a dictionary, not a list)
- [ ] **Interface Names:** Dictionary keys are interface names; do NOT include `name` field in interface dicts
- [ ] **Booleans:** Use `true`/`false` (JSON) for `link_status` and `mgmt_only`
- [ ] **Nulls:** Ensure empty values for MACs or VLANs are actual `null` (None in Jinja), not empty strings
- [ ] **Field Names:** Use `link_status` (not `enabled`) and `802.1Q_mode` (not `mode`)
- [ ] **MTU Type:** Can be string ("1500") or integer (1500) - test with your version
- [ ] **802.1Q_mode:** Use empty string `""` for L3 interfaces, or omit for non-L2-capable interfaces
- [ ] **Management Interface:** Include directly in `interfaces` dict with `mgmt_only: true`
- [ ] **MAC Normalization:** Convert dot notation (e.g., "AAAA.BBBB.CCCC") to colon format (e.g., "aa:bb:cc:dd:ee:ff")
- [ ] **Always Return Strings:** All `sync_devices` post-processors must return strings (even empty ones)

## Best Practices

- **Use Single Command Per Key:** Each key (`serial`, `interfaces`, etc.) should use a single command that returns all needed data. The plugin does not properly merge multiple command outputs when using different `jpath` values.
- **Parse Everything in Jinja2:** Since you're limited to one command per key, use Jinja2 post-processing to extract all needed information from that single command output.
- **Include all interfaces** (with or without IP addresses)
- **Filter meaningless interfaces:** Skip virtual/system interfaces like "vlan", "tunnel", "loopback", "name" if they appear as headers
- **Use namespace for state:** Maintain parsing state (flags, dictionaries, lists) across loops using `namespace()` for complex parsing tasks
- **Validate MAC addresses:** Check format and reject invalid values (set to `null`)
- **Delete test devices** before re-running sync jobs to avoid conflicts
- **Enable debug logging** to inspect parsed output and validate structure
- **Test incrementally:** Start with basic device sync, then add network data sync

---
