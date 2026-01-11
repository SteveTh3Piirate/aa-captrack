# CapTrack – Developer Notes

This document captures the **exact workflow used to develop CapTrack**, generate migrations safely, and deploy changes using Docker. It is intentionally practical and opinionated so future-you doesn’t have to rediscover this again.

---

## 1. Repository Layout (Important)

```
aa-captrack/
├─ captrack/                 # The actual AllianceAuth plugin
│  ├─ models.py
│  ├─ admin.py
│  ├─ tasks.py
│  ├─ hooks.py
│  ├─ services.py
│  ├─ templates/
│  └─ migrations/
│
├─ testproj/                 # Local test Django project (DO NOT SHIP)
│  ├─ manage.py
│  ├─ testproj/
│  │  ├─ settings.py
│  │  ├─ urls.py
│  │  └─ wsgi.py
│  └─ mockdeps/              # Mock apps used to avoid installing AllianceAuth
│     ├─ authentication/
│     └─ eveuniverse/
│
├─ manage.py                 # Root manage.py (points at testproj)
├─ setup.py
├─ MANIFEST.in
└─ DEV_NOTES.md
```

Key idea:

* `captrack/` is production code
* `testproj/` is **development-only scaffolding**

---

## 2. Why mockdeps exists

AllianceAuth is heavy and not designed to be pip-installed casually.

To allow **local development and migration generation**, we use:

* a **minimal Django test project**
* **mock apps** that imitate required AA models by app label

This allows:

* correct migrations
* correct foreign keys
* zero AllianceAuth install locally

---

## 3. Critical rule for models

### ✅ ALWAYS reference AllianceAuth models by **string**, not import

**Correct (production-safe):**

```python
models.OneToOneField(
    "authentication.CharacterOwnership",
    on_delete=models.CASCADE,
)
```

**DO NOT do this in models.py:**

```python
from allianceauth.authentication.models import CharacterOwnership
```

Why:

* breaks mockdeps
* breaks import-time loading
* unnecessary for migrations

The string reference works in:

* mock test project
* real AllianceAuth deployment

---

## 4. Mock Authentication App (for migrations)

To satisfy Django when generating migrations, we created a **minimal mock app**:

```
testproj/mockdeps/authentication/
├─ __init__.py
├─ apps.py
├─ models.py
└─ migrations/__init__.py
```

### `apps.py`

```python
from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    name = "authentication"
    label = "authentication"
```

### `models.py`

```python
from django.db import models

class Character(models.Model):
    character_id = models.BigIntegerField(unique=True)
    character_name = models.CharField(max_length=255)

class CharacterOwnership(models.Model):
    character = models.OneToOneField(Character, on_delete=models.CASCADE)
```

This mirrors the **app label and model name** used by AllianceAuth.

---

## 5. testproj settings (mock mode)

Key points in `testproj/testproj/settings.py`:

* Use `Path`, not strings, for `BASE_DIR`
* Add `mockdeps` to `sys.path`
* **DO NOT include real AllianceAuth apps**

```python
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "mockdeps"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "authentication",              # mock
    "eveuniverse.apps.EveUniverseConfig",
    "captrack",
]

ROOT_URLCONF = "testproj.testproj.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

---

## 6. Migration workflow (THE IMPORTANT BIT)

When adding or changing models:

### Step-by-step

```bash
# Activate venv
.venv\Scripts\activate

# Apply base Django migrations
python manage.py migrate

# Generate plugin migrations
python manage.py makemigrations captrack

# Apply plugin migrations
python manage.py migrate
```

Result:

* `captrack/migrations/XXXX_*.py` generated
* migrations reference `authentication.CharacterOwnership`
* safe for production deployment

---

## 7. After migrations are created

Before deploying:

* Restore **production models.py** if you temporarily changed anything
* Ensure mockdeps code is NOT imported by plugin code
* Commit migrations

Mock code stays in `testproj/` only.

---

## 8. Docker deployment checklist

On a real AllianceAuth instance:

```bash
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
docker compose restart web worker beat
```

Verify:

* plugin loads
* menu item visible
* migrations applied

---

## 9. Golden rules (print these)

* ✔ Never import AllianceAuth models in plugin models.py
* ✔ Always use app-label string references
* ✔ Generate migrations in mock mode
* ✔ Test project is disposable; migrations are not
* ✔ If migrations work here, they will work in real AA

---

End of file. You earned this 😄
