# aa-captrack

AllianceAuth plugin for tracking and alerting on capital ship activity

Version: **v1.0.0**  
Status: **Stable Baseline**

## Overview

`aa-captrack` is an AllianceAuth plugin designed to monitor capital ship activity across characters and accounts, providing:

- Real-time dashboard visibility
- Threshold-based alerting
- Discord notifications
- Per-pilot snoozing
- Clear separation between tracked, alerting, and informational states

The plugin prioritises operational clarity and avoids unnecessary alert noise.

## Capital Tracking Logic

| Ship Class | Behavior |
|-----------|---------|
| Titans | Always alerting |
| Supercarriers | Always alerting |
| Dreadnoughts | Alert when ≥ threshold (default: 5) under same main |
| Lancer Dreads | Alert when ≥ threshold |
| Carriers | Alert when ≥ threshold |
| Force Auxiliaries | Alert when ≥ threshold |
| Capital Industrials | Tracked only (no alerts) |

Threshold logic is applied consistently across:
- Dashboard
- Discord alerts
- Background tasks

## Dashboard

- Collapsible cards with rotating chevrons
- Clear separation of:
  - Critical
  - Alerting
  - Informational
- Optional display of unclassified ships
- Configurable refresh interval
- Optional remembered collapse state per user

## Discord Integration

- Discord alerts include **only alerting ships**
- Separate webhooks for:
  - Critical alerts
  - Standard alerts
- Configurable ping behavior (roles / policy)
- Optional inclusion of:
  - System
  - Region
  - Dashboard link

  ## Snoozing

- Snoozing is **per pilot** (by design)
- Supports multiple durations (e.g. 1h / 6h / 24h)
- Snoozed pilots are excluded from:
  - Dashboard alerts
  - Discord notifications

  ## Permissions

| Permission | Description |
|----------|-------------|
| `captrack.basic_access` | View dashboard |
| `captrack.admin_access` | Configure settings |

## Installation

1. Install the plugin:

pip install aa-captrack

2. Add to `INSTALLED_APPS`:

1. INSTALLED_APPS += ["captrack"]

3. Run migrations:

python manage.py migrate captrack

4. Collect static files:

5. Restart AllianceAuth services.

## Configuration

Configuration is managed via the AllianceAuth Admin Panel:

Admin → Captrack → CapTrack Settings

Only **one settings row** is expected.

### Configurable Options Include

- Enabled / disabled state
- Tracked group IDs
- Industrial group IDs
- Alert thresholds per ship class
- Discord webhook URLs
- Discord ping policy
- Dashboard behavior options
- Snooze durations
- Display preferences

## Data Model Notes

- Capital activity is grouped by **main character**
- Industrials are tracked but do not generate alerts
- Alert logic is centralized in:
  - `services.py`
  - `views.py`
  - `tasks.py`

  ## Compatibility

- AllianceAuth: 4.x
- Django: 4.2
- Database:
  - MySQL / MariaDB (recommended)
  - SQLite (development only)

## Versioning Policy

- **v1.0.0**: Stable baseline
- Future versions will:
  - Avoid destructive migrations
  - Prefer additive schema changes
  - Be tested against existing installs

## Screenshots

> Screenshots are placeholders and may change as the UI evolves.

### Dashboard — Overview

![Dashboard Overview](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/images/overview.jpg)

Displays all tracked capital activity grouped by main character, with clear visual separation between critical, alerting, and informational states.

---

### Dashboard — Collapsed / Expanded States

![Dashboard Collapsed](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/images/collapsed.jpg)

Cards can be collapsed to reduce noise. Collapse state can optionally be remembered per user.

---

### Dashboard — Snoozed Pilots

![Dashboard Snoozed](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/images/snoozed.jpg)

Pilots can be snoozed individually to suppress alerts and notifications for a configurable duration.

---

### Admin — CapTrack Settings

![Admin Settings](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/images/admin-settings.jpg)

All configuration is managed through a single settings entry in the AllianceAuth admin panel.

---

### Discord — Critical Alert Example

![Discord Critical Alert](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/images/discord-critical.jpg)

Critical alerts (Titans, Supercarriers) are always sent immediately.


## License

MIT License
