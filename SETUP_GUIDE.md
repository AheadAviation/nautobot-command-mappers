# Git Repository Setup Guide

Quick reference for setting up this repository as a Git datasource in Nautobot.

## Prerequisites

- Nautobot instance with Device Onboarding plugin installed
- Git repository (GitHub, GitLab, Bitbucket, etc.)
- Access to Nautobot admin panel

## Repository Structure

```
onboarding_override/
├── README.md                          # Repository documentation
├── .gitignore                         # Git ignore file
├── SCHEMA_REFERENCE.md                # Schema documentation (optional)
└── onboarding_command_mappers/        # REQUIRED: Command mapper directory
    ├── paloalto_panos.yml             # Palo Alto PAN-OS mapper
    ├── bigip_f5.yml                   # F5 BIG-IP mapper
    └── linux.yml                      # Linux mapper
```

## Step-by-Step Setup

### 1. Push to Git Repository

```bash
cd onboarding_override
git init
git add .
git commit -m "Initial commit: Device onboarding command mappers"
git remote add origin <your-git-repo-url>
git push -u origin main
```

### 2. Configure in Nautobot

1. **Navigate to Git Repositories**
   - Go to: **Extensibility → Git Repositories**
   - Click **Add** (top right)

2. **Configure Repository**
   - **Name:** `Device Onboarding Command Mappers`
   - **Slug:** `device-onboarding-mappers` (auto-generated)
   - **Remote URL:** `https://github.com/your-org/your-repo.git`
   - **Branch:** `main` (or your default branch)
   - **Provides:** ✅ **Network Sync Job Command Mappers** (CRITICAL - must check this)
   - **Username/Token:** If repository is private

3. **Save and Sync**
   - Click **Create**
   - Click **Sync** button to pull files
   - Wait for sync to complete

### 3. Verify Files Loaded

1. Go to: **Extensibility → Git Repositories → [Your Repo]**
2. Click **Files** tab
3. Verify you see:
   - `onboarding_command_mappers/paloalto_panos.yml`
   - `onboarding_command_mappers/bigip_f5.yml`
   - `onboarding_command_mappers/linux.yml`

### 4. Test Onboarding

1. Go to: **Jobs → Jobs**
2. Run: **Sync Devices From Network** or **Sync Network Data From Network**
3. Select platform: `paloalto_panos` (or your platform)
4. Run the job
5. Check logs to verify custom command mapper is being used

## Verification Checklist

- [ ] Repository pushed to Git
- [ ] Git repository created in Nautobot
- [ ] "Network Sync Job Command Mappers" checkbox selected
- [ ] Repository synced successfully
- [ ] Files visible in repository Files tab
- [ ] Test job executed successfully
- [ ] Custom command mapper used (check job logs)

## Troubleshooting

### Files Not Appearing

**Issue:** Files don't show up after sync

**Solutions:**
- Verify repository structure matches exactly:
  - Root must have `onboarding_command_mappers/` directory
  - YAML files must be inside `onboarding_command_mappers/`
- Check Git repository branch name matches
- Verify "Network Sync Job Command Mappers" is checked
- Check Nautobot logs for sync errors

### Default Mapper Still Used

**Issue:** Job still uses default command mapper

**Solutions:**
- Verify YAML file name matches network driver exactly
- Check network driver name: `paloalto_panos` (not `palo-alto` or `panos`)
- Verify file is in `onboarding_command_mappers/` directory
- Check job logs for which mapper file is being used
- Restart Nautobot if needed (some changes require restart)

### YAML Syntax Errors

**Issue:** Job fails with YAML parsing errors

**Solutions:**
- Validate YAML syntax using online YAML validator
- Check for indentation errors (must use spaces, not tabs)
- Verify Jinja2 template syntax in post_processor
- Test locally using `test_palo_parser.py` script

### Authentication Errors

**Issue:** Cannot sync private repository

**Solutions:**
- Verify username/token are correct
- For GitHub: Use Personal Access Token (not password)
- For GitLab: Use Project Access Token or Personal Access Token
- Check repository permissions

## Updating Command Mappers

### Process

1. Edit YAML file locally
2. Test using `test_palo_parser.py`
3. Commit and push to Git:
   ```bash
   git add onboarding_command_mappers/paloalto_panos.yml
   git commit -m "Update Palo Alto parser"
   git push
   ```
4. In Nautobot: Go to repository → Click **Sync**
5. Test with onboarding job

### Best Practices

- Always test locally before pushing
- Use version numbers in YAML file headers
- Document changes in commit messages
- Keep README.md updated
- Test on non-production devices first

## Network Driver Names

To verify network driver names in Nautobot:

```python
from nautobot.dcim.utils import get_all_network_driver_mappings
drivers = sorted(list(get_all_network_driver_mappings().keys()))
print(drivers)
```

Common drivers:
- `paloalto_panos` - Palo Alto PAN-OS
- `cisco_ios` - Cisco IOS
- `cisco_nxos` - Cisco NX-OS
- `juniper_junos` - Juniper JunOS
- `arista_eos` - Arista EOS
- `bigip_f5` - F5 BIG-IP

## References

- [Nautobot Device Onboarding Documentation](https://docs.nautobot.com/projects/device-onboarding/en/latest/user/app_yaml_overrides/)
- [Schema Reference](SCHEMA_REFERENCE.md)
- [Repository README](README.md)

---

**Last Updated:** December 31, 2025

