---
trigger: always_on
---

# Django + DRF Local Rules (Windsurf)

## 🔧 General Guidelines

* Use **Python 3.10+** syntax and typing everywhere.
* Stick to **Django 4.x** and **Django REST Framework** latest stable version.
* All apps should be placed inside the `apps/` directory.
* Each Django app must be modular and serve a single responsibility:

  * `users/`, `loans/`, `payments/`, `notifications/`, etc.

---

## 📃 Project Structure

```
project/
│
├── apps/
│   ├── users/
│   ├── loans/
│   ├── payments/
│   └── notifications/
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
├── manage.py
├── requirements.txt
├── docker-compose.yml
└── windsurf-rules.md
```

---

## 📊 Models

* Use **snake\_case** for all field names.
* Use `models.TextChoices` for enums.
* Always define `__str__()` methods.
* Default `Meta` options:

  * `ordering`, `verbose_name`, `verbose_name_plural`.

**Example:**

```python
class LoanStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"

class Loan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 🧬 Serializers

* Use `ModelSerializer` unless a custom field/logic is required.
* Validate data using `validate_<field>` or `validate()` methods.
* Don’t mix write-only and read-only logic in the same serializer.

---

## 🪰 Views

* Prefer `GenericAPIView` or `ViewSet` for standard CRUD.
* Avoid `APIView` unless custom flow is necessary.
* Each view should only handle one concern.

**Example:**

```python
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
```

---

## 📌 URLs

* All URLs must be **namespaced per app**.
* Use `DefaultRouter` for ViewSets.
* Keep API paths versioned: `/api/v1/loans/`, `/api/v1/users/`

---

## 🔐 Auth & Permissions

* Use `djangorestframework-simplejwt` for JWT auth.
* Token expiry:

  * Access token: 15 mins
  * Refresh token: 7 days
* Permissions:

  * Use `IsAuthenticated` by default.
  * Define custom permissions in `permissions.py` file inside app.

---

## 🔁 Background Tasks

* Use Celery with Redis for periodic or heavy tasks.
* Define tasks in `tasks.py` file.
* Ensure idempotency using `idempotency_key` table for payments.

---

## 💾 Database & Migrations

* Use **PostgreSQL**
* Enforce:

  * snake\_case column names
  * plural table names
* Use `makemigrations` + `migrate`, commit all migration files.
* All `ForeignKey` fields must define `related_name`.

---

## 🥪 Testing

* Use `pytest` + `pytest-django` + `factory_boy`
* Folder structure:

  * `tests/` per app
  * `factories.py` for all factories
* Test types:

  * Model logic (e.g., schedule generation)
  * API integration tests
  * Edge cases like idempotency

---

## ⚙️ CI & Formatting

* Use `black`, `isort`, and `flake8` for formatting and linting.
* Setup GitHub Actions to run:

  * `black . --check`
  * `flake8 .`
  * `pytest --cov`

---

## 📤 API Response Format

* All responses must follow this structure:

```json
{
  "status": "success",
  "message": "Loan created successfully.",
  "data": {
    ...
  }
}
```

* On error:

```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "field": ["error msg"]
  }
}
```

Use a global exception handler and response middleware to enforce this.

---

## 📚 Documentation

* Generate OpenAPI docs using `drf-spectacular`.
* Route docs to `/api/schema/`, Swagger at `/api/docs/`.
* Update docs when APIs change.

---

## 🔖 Versioning

* Use versioned API URLs (`/api/v1/...`).
* Breaking changes must go into `/api/v2/...`.
* Document version history in `CHANGELOG.md`.
