# Script Utilities

Focused modules for developing CLI tools and ops scripts, all re-exported from `support_python`:
- [terminal.py](../../src/support_python/terminal.py): `configure_utf8_output` for cross-platform console standard stream encoding.
- [version.py](../../src/support_python/version.py): `get_project_version` for resolving the version from Gradle properties or `pyproject.toml`.
- [net.py](../../src/support_python/net.py): `is_port_in_use` for checking TCP socket availability.
- [env.py](../../src/support_python/env.py): `read_env_file` for parsing `.env` or properties files,
  and `user_config_dir`/`user_config_path` for locating user configuration files.
- [crypto.py](../../src/support_python/crypto.py): `get_standard_password_hash` and `decrypt_property_value` for credentials and properties; the caller supplies the salt and AES key.

## Example
```python
from support_python import (
    configure_utf8_output,
    decrypt_property_value,
    get_project_version,
    get_standard_password_hash,
    is_port_in_use,
    read_env_file,
    user_config_path,
)

# Ensure console standard streams encode UTF-8 correctly
configure_utf8_output()

# Resolve version from Gradle properties, build.gradle, or pyproject.toml
version = get_project_version()

# Check port availability
if not is_port_in_use(8080):
    print("Port 8080 is available")

# Parse .env or properties file
env_vars = read_env_file(".env")

# Locate the user config file: $XDG_CONFIG_HOME/my-tool/config.json when XDG_CONFIG_HOME is absolute,
# else %APPDATA%/my-tool/config.json on Windows, else ~/.config/my-tool/config.json (never created)
config_file = user_config_path("my-tool")

# Compute standard password hash
password_hash = get_standard_password_hash("my-password", salt=bytes.fromhex("{{64-hex-digit-salt}}"))

# Decrypt an aes: property with your own key; needs the cryptography package
# (raises ImportError if it is missing and ValueError if the value is malformed)
value = decrypt_property_value("aes:{{base64-ciphertext}}", "{{aes-key-hex}}")
```
