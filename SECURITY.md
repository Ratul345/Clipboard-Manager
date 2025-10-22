# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Clipboard Manager seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

1. **DO NOT** open a public issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting feature
3. Include detailed information about the vulnerability:
   - Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
   - Full paths of source file(s) related to the manifestation of the issue
   - The location of the affected source code (tag/branch/commit or direct URL)
   - Any special configuration required to reproduce the issue
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours
- **Updates**: We will send you regular updates about our progress
- **Timeline**: We aim to patch critical vulnerabilities within 7 days
- **Credit**: If you wish, we will publicly credit you for the discovery once the issue is resolved

## Security Best Practices for Users

### Data Privacy

- **Local Storage Only**: All clipboard data is stored locally on your computer in `~/.clipboard-manager/`
- **No Cloud Sync**: Your data never leaves your computer
- **No Telemetry**: We don't collect any usage data or analytics

### Sensitive Data

⚠️ **Important**: Clipboard Manager stores everything you copy, including:
- Passwords
- Credit card numbers
- Private keys
- Personal information

**Recommendations:**
1. Use the "Clear All" feature regularly if you copy sensitive data
2. Consider pausing the application when copying highly sensitive information
3. Be aware that clipboard data is stored unencrypted in the local database

### Windows SmartScreen Warning

When running the Windows executable, you may see a SmartScreen warning. This is because:
- The application is not code-signed with a commercial certificate
- It's a new application without established reputation

**This is normal for open source applications.** You can verify the safety by:
1. Checking the source code on GitHub
2. Building from source yourself
3. Scanning the executable with your antivirus

## Known Security Considerations

### Local Database

- Clipboard data is stored in an SQLite database at `~/.clipboard-manager/clipboard.db`
- The database is **not encrypted** by default
- Anyone with access to your user account can read this data
- Images are stored as files in `~/.clipboard-manager/images/`

### Permissions

**Windows:**
- Requires clipboard access (standard Windows API)
- Requires file system access for local storage
- System tray integration

**Linux:**
- Requires clipboard access (via xclip, xsel, or wl-clipboard)
- Requires file system access for local storage
- May require X11 or Wayland permissions

### Network Access

- **No network access required** - The application works completely offline
- No data is sent to external servers
- No automatic updates or telemetry

## Security Updates

Security updates will be released as new versions. Users should:
1. Watch the repository for security announcements
2. Update to the latest version when security patches are released
3. Check the [Releases](https://github.com/Ratul345/Clipboard-Manager/releases) page regularly

## Disclosure Policy

- We follow responsible disclosure practices
- Security issues will be disclosed publicly only after a patch is available
- We will credit researchers who report vulnerabilities (unless they prefer to remain anonymous)

## Contact

For security concerns, please open an issue on GitHub or contact the maintainer through GitHub.

---

**Note**: This is an open source project maintained by volunteers. While we take security seriously, we cannot guarantee immediate responses or fixes. Use at your own risk.
