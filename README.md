# ServerAlert

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Systemd](https://img.shields.io/badge/systemd-service-3b3b3b)
![License](https://img.shields.io/badge/License-MIT-green)

## Overview
ServerAlert is a lightweight monitoring daemon that sends Discord alerts for system resource thresholds, service status changes, log events, file changes, and scheduled database backups.

## Features
- CPU, memory, disk, process count, connection count, load average checks
- Critical service health + restart attempt
- Service start/stop change detection
- SSH login and security log alerts
- File change monitoring across directories
- Optional health HTTP endpoint
- Database backup uploads (mysqldump)
- Per-category Discord webhooks

## Requirements
- Python 3.11+
- systemd (service management)
- `mysqldump` if database backups are enabled

## Quick Start
```bash
cp .env.example .env
/var/www/serveralert/start.sh install
systemctl start serveralert
```

## Service Management
```bash
systemctl start serveralert
systemctl stop serveralert
systemctl restart serveralert
systemctl status serveralert
journalctl -u serveralert -f
```

## Install / Uninstall
```bash
/var/www/serveralert/start.sh install
/var/www/serveralert/start.sh uninstall
```

## Configuration
All settings live in `.env` (see `.env.example`).

Key groups:
- Thresholds: `CPU_THRESHOLD`, `MEMORY_THRESHOLD`, `DISK_THRESHOLD`, `LOAD_AVG_THRESHOLD`
- Scheduling: `CHECK_INTERVAL_SECONDS`, `ALERT_MIN_INTERVAL`
- Detection toggles: `DETECT_*`
- Webhooks: `WEBHOOK_*`
- Embed styling: `EMBED_*`

## Files
- `serveralert.py` entrypoint
- `modules/` detection modules and helpers
- `serveralert.service` systemd unit template
- `start.sh` install/run helper

## License
MIT. See `LICENSE`.
