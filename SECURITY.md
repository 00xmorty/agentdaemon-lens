# Security

Supported version: latest published release. This utility reads local package metadata and transient process command columns; it does not execute discovered binaries, mutate system settings, send telemetry or upload reports.

Do not run as root or on hostile concurrently modified directory trees. Directory traversal is best effort, not a sandbox. Reports omit raw paths and arguments; aggregate presence can still be sensitive. Never attach raw process files, serials, tokens or private logs to public issues.

For a sensitive vulnerability, use GitHub's private vulnerability reporting on this repository when available. If unavailable, open a value-free public issue requesting a private reporting route; do not include exploit secrets or private user data.
