# AgentDaemon Lens

A dependency-free, read-only Codex package inventory and background-process clue counter. See how many release directories exist in the known `app-server-daemon` and `standalone` package families, their logical file bytes, and matching managed daemon/updater commands—without exposing paths, release names, PIDs or raw command arguments.

## Run / install

Requires Python 3.9+; macOS and Linux. No pip installation needed.

```sh
git clone https://github.com/00xmorty/agentdaemon-lens.git
cd agentdaemon-lens
python3 agentdaemon-lens
python3 agentdaemon-lens --json
```

Or download the `agentdaemon-lens` release asset and run `python3 agentdaemon-lens`. Review code before running downloaded tools.

By default reads the two known release layouts under `~/.codex/packages` and queries `ps -ax -o command=`. It does not execute Codex. Missing directories are `NOT_OBSERVED`, not an error.

```sh
python3 agentdaemon-lens --packages-root ./sample-packages --no-processes --json
python3 agentdaemon-lens --packages-root ./sample-packages --process-file ./saved-commands.txt --json --check
```

`--process-file` replaces the live process probe (strict offline process mode); `--no-processes` disables it even if a file was supplied. A saved process file must contain the command column only, without PID/header columns. Offline mode still inventories the supplied package directory.

`--check`: 0 = no selected clue observed; 1 = multiple release directories or a matching daemon/updater; 2 = an incomplete/failed query (`UNKNOWN`, takes precedence). Without `--check`, diagnostics exit 0; invalid CLI arguments exit 2.

## Example (synthetic fixture)

Two three-byte package files in separate release directories yield `release_directories=2`, `logical_bytes=6`. This is not proof of duplicate content or reclaimable disk space. Unit tests create and exercise this example.

## Safety and limitations

- Read-only: no network requests, telemetry, sudo, deletion, preference edits, launchctl changes, process termination or daemon stop/start commands.
- Reports contain fixed family labels, aggregate counts and states; never directory names, usernames, serials, command lines or PIDs. Raw process arguments are read transiently and are not emitted or saved.
- Narrow MVP: Codex only. No Claude/Gemini/Ollama discovery or launchd attribution. Custom layouts and renamed executables may be missed.
- Process matching is lexical and cannot prove vendor identity, actual updater activity, orphan status, parent/session relationships, causation or successful operation. A zero count is not proof of absence.
- Only regular-file logical bytes count; hardlinks are counted once per family. APFS clones/compression/sparse files and filesystem allocation may differ. Release-directory counts do not identify old or inactive releases. Nothing is labeled safe to delete.
- Symlink paths are refused and symlink entries skipped. Permission failures and bounded scans are `UNKNOWN`; partial counts remain lower bounds. Scans share a 50,000-entry / 5-second budget. Process queries timeout after 3 seconds; saved input is capped at 2 MB.
- Directory replacement races and slow/network filesystems can escape the best-effort time budget. Do not run against hostile concurrently modified trees or as root. This is not a security boundary.
- Output aggregates can still reveal installed-tool presence. Review before sharing; never share the raw saved process file. No user outcome has been measured.

## Test

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile agentdaemon-lens
```

MIT licensed. Use the product repository's private vulnerability reporting facility for sensitive reports; do not post secrets in public issues.
