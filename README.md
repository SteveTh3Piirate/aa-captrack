# aa-captrack

AllianceAuth plugin for tracking and alerting on capital ship activity (and other configured ship groups) across characters/accounts, with an operational dashboard, snoozing, and Discord notifications.

Version: **v1.0.9b10**  
Status: **Pre-release (beta)**
**!!!NEW MIGRATIONS!!!**

---

## What’s new in v1.0.9b10 (highlights)
- **Corptools 3.x compatibility (b7+)**
  - Updated watchlist refresh enqueue logic to handle Corptools 3.x task API changes (signature-safe enqueue and b7 single-character asset refresh support).
  - Worker task registration guidance for Corptools `tasks/` package so Celery can resolve Corptools task names reliably.
- **Move Region blacklist to SDE**
  - “Blacklisted Regions” now uses **`eve_sde.Region`** for region selection and matching on SDE-backed installs.
- **SDE-safe type/group lookups**
  - Fixed ItemType group filtering and group-id resolution under SDE schema (prevents dashboard errors and removes “UNKNOWN” alert levels).
- **Dashboard UI parity restored**
  - Restored card header features: **Audit** button, corp/alliance name + logos, and expanded snooze controls (including ∞ + Snooze-all).
- **Migration graph cleanup**
  - Added merge migration to resolve multiple-leaf migration conflicts introduced during the SDE migration work.

---

## Overview

`aa-captrack` monitors capital ship activity (and other configured ship groups) using Corptools asset/audit data, presenting:

- Real-time dashboard visibility grouped by **main**
- Threshold-based alerting (per ship class/group)
- Discord webhook notifications (critical and standard)
- Per-pilot snoozing + **Snooze All**
- Clean separation between **Critical**, **Alerting**, and **Informational** states

The plugin prioritises operational clarity and avoids unnecessary alert noise.

---

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

> Notes:
> - “Capital Industrials” are tracked for visibility but do not generate alerts by default.
> - Group IDs and thresholds are configurable in Admin.

---

## Dashboard

- Collapsible cards with rotating chevrons
- Card header shows:
  - Main (character) name
  - **Corporation** name + logo
  - **Alliance** name + logo (if present)
  - **Audit** button (Corptools audit link)
  - **Snooze All** controls
  - Status badge (Critical/Alerting/Info)
- Clear separation of:
  - Critical
  - Alerting
  - Informational
- Optional display of unclassified ships
- Configurable refresh interval
- Optional remembered collapse state per user

### Audit button format

Audit link for a main character uses Corptools’ route format:

`/audit/r/<main_character_id>/account/overview`

Example:

`/audit/r/2114270226/account/overview`

---

## Snoozing

- Snoozing is **per pilot** (by design)
- Supports multiple durations (e.g. 1h / 6h / 24h)
- **∞ (Infinite)** snooze supported (until cleared)
- **Snooze All** applies a duration to all pilots listed in the card
- Snoozed pilots are excluded from:
  - Dashboard alerts
  - Discord notifications

---

## Discord Integration

- Alerts include **only alerting ships**
- Separate webhooks for:
  - Critical alerts
  - Standard alerts
- Optional mention support:
  - **Role mention:** `<@&ROLE_ID>`
  - **User mention:** `<@USER_ID>`
- Uses `allowed_mentions` to ensure only configured mentions are allowed (prevents accidental @everyone/@here).

---

## Permissions

| Permission | Description |
|----------|-------------|
| `captrack.basic_access` | View dashboard |
| `captrack.admin_access` | Configure settings |

---

## Installation

### Requirements

- AllianceAuth: **4.13+** (v4.x supported; v5 migration path is the motivation for this beta)
- Django: 4.2+
- Corptools: **3.0.0b7** (or compatible 3.x beta)
- Database: MySQL/MariaDB recommended

If you are running Corptools 3.x, you also need the SDE stack working:

- `eve_sde` installed and in `INSTALLED_APPS`
- `modeltranslation` installed and **first** in `INSTALLED_APPS`
- SDE data synced using: `python manage.py esde_load_sde`

### Install the plugin

```bash
pip install aa-captrack==1.0.9b9
```

### Add to `INSTALLED_APPS`

```python
INSTALLED_APPS += [
    "captrack",
]
```

> If you are on Corptools 3.x + eve_sde:
> - Ensure `modeltranslation` is first in `INSTALLED_APPS`
> - Ensure `eve_sde` is present in `INSTALLED_APPS`

### Migrate + collect static

```bash
python manage.py migrate captrack
python manage.py collectstatic --noinput
```

### Restart services

Restart AllianceAuth web and celery services.

---

## Configuration

Configuration is managed via the AllianceAuth Admin Panel:

**Admin → Captrack → CapTrack Settings**

Only **one settings row** is expected.

### Configurable options include

- Enabled / disabled state
- Tracked group IDs
- Industrial group IDs
- Alert thresholds per ship class/group
- Discord webhook URLs (critical + standard)
- Discord mention configuration (role IDs and/or user IDs)
- Dashboard behavior options
- Snooze durations / visibility preferences

---

## Background tasks

CapTrack uses periodic tasks to refresh/watch data and drive alerts.  
In **v1.0.9b9**, watchlist refresh is compatible with Corptools 3.x task changes (celery-once signature validation, task name changes, and b7 single-character asset refresh).  

---

## Compatibility

### AllianceAuth / Corptools

- AllianceAuth: **4.x (4.13+)**
- Corptools: **3.0.0b7** (target), other 3.x betas may work

### SDE / eve_sde

If you use Corptools 3.x (SDE-backed), ensure:

1) `eve_sde` and `modeltranslation` are installed
2) `modeltranslation` is **first** in `INSTALLED_APPS`
3) Run and schedule SDE sync:

```bash
python manage.py esde_load_sde
```

Corptools migrations may refuse to apply if eve_sde data is stale (>24h).

CapTrack’s **Blacklisted Regions** feature also uses `eve_sde.Region`, so SDE data must be present for region search/autocomplete.

---

## Versioning policy

- **v1.0.9b9**: Beta/pre-release focusing on Corptools 3.x task API changes + SDE migration + UI feature parity + migration merge
- Future versions will:
  - Avoid destructive migrations where possible
  - Prefer additive schema changes
  - Be tested against existing installs

---

## Screenshots

> Screenshots are placeholders and may change as the UI evolves.

### Dashboard — Overview

![Dashboard Overview](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/refs/heads/master/images/overview.jpg)

Displays all tracked capital activity grouped by main character, with clear visual separation between critical, alerting, and informational states.

---

### Dashboard — Collapsed / Expanded States

![Dashboard Collapsed](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/refs/heads/master/images/collapsed.jpg)

Cards can be collapsed to reduce noise. Collapse state can optionally be remembered per user.

---

### Dashboard — Snoozed Pilots

![Dashboard Snoozed](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/refs/heads/master/images/snoozed.jpg)

Pilots can be snoozed individually to suppress alerts and notifications for a configurable duration.

---

### Admin — CapTrack Settings

![Admin Settings](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/refs/heads/master/images/admin-settings.jpg)

All configuration is managed through a single settings entry in the AllianceAuth admin panel.

---

### Discord — Critical Alert Example

![Discord Critical Alert](https://raw.githubusercontent.com/SteveTh3Piirate/aa-captrack/refs/heads/master/images/discord-critical.jpg)

Critical alerts (Titans, Supercarriers) are always sent immediately.

---

## License

MIT License
