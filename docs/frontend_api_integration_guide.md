# KinCash Backend – Front-End API Integration Guide (v1)

Prepared for: **Mr. Suhail Malik (Front-End Developer)**  
Date: 26 Jun 2025

---

## 1. Overview
The KinCash REST API is built with Django + DRF and uses JWT **Bearer tokens** for authentication. This guide explains how to consume every v1 endpoint from a web / mobile client.

* Base URL (local dev): `http://localhost:8000`  
* All routes are **prefixed** by `/api/` and return JSON in the following format:

```json
{
  "status": "success",          // or "error"
  "message": "Human readable message",
  "data": { ... }                // present on success
  "errors": { ... }              // present on error
}
```

---

## 2. Authentication Flow
| Step | Endpoint | Method | Purpose |
|------|----------|--------|---------|
| 1 | `/user/signup/` | POST | Create user account. |
| 2 | `/user/login/` | POST | Obtain **access** (15 min) & **refresh** (7 days) tokens. |
| 3 | Every request | — | Attach header `Authorization: Bearer <access>` |
| 4 | `/user/token/refresh/` | POST | Exchange **refresh** → new access token when expired. |
| 5 | `/user/logout/` | POST | Revoke token on server side. |

> Front-end tip: Store the **refresh token** securely (e.g. `httpOnly` cookie) and the **access token** in memory / short-lived storage. Auto-refresh on `401`.

### Sample Login
```ts
import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:8000/api' });

export async function login(email: string, password: string) {
  const res = await api.post('/user/login/', { email, password });
  const { access, refresh } = res.data.data;
  api.defaults.headers.common.Authorization = `Bearer ${access}`;
  // persist refresh, etc.
}
```

---

## 3. Endpoints Reference
Only the most common fields are shown – review `docs/kincash_api_collection_v2.json` for full schemas & examples.

### 3.1 Users
| Name | Method & Route | Auth | Payload |
|------|----------------|------|---------|
| Sign-up | `POST /user/signup/` | No | `email, password, phone_number?, first_name?, last_name?` |
| Login | `POST /user/login/` | No | `email/phone_number, password` |
| Logout | `POST /user/logout/` | Yes | — |
| Get profile | `GET /user/get-user/` | Yes | — |
| Update profile | `PUT /user/update_profile/` | Yes | `first_name?, last_name?, avatar?` |
| Google Auth | `POST /user/google-auth/` | No | `id_token` (Google) |
| Password reset request | `POST /user/password-reset/request/` | No | `email` |
| Verify OTP | `POST /user/verify-otp/` | No | `email, otp` |
| Password reset confirm | `POST /user/password-reset/confirm/` | No | `token, password` |

### 3.2 Loans
| Name | Method & Route | Auth |
|------|----------------|------|
| Create loan | `POST /loan/create_loan/` | Yes |
| List my loans | `GET /loan/get_loans/` | Yes |
| Loan schedule by ID | `GET /loan/get_loans_by_id/?loan_id=<id>` | Yes |
| Transaction log | `GET /loan/get_transactions_done/` | Yes |
| Pay EMI | `POST /loan/pay_emi/` | Yes |
| Accept loan | `POST /loan/accept_loan/` | Yes |
| Get user payments | `GET /loan/get_user_payments/` | Yes |

### 3.3 Payments (ModelViewSet)
Prefix: `/payments/`
| Action | Route | Method | Auth |
|--------|-------|--------|------|
| List | `/` | GET | Yes |
| Create | `/` | POST | Yes |
| Retrieve | `/:id/` | GET | Yes |
| Update | `/:id/` | PUT | Yes |
| Partial update | `/:id/` | PATCH | Yes |
| Delete | `/:id/` | DELETE | Yes |

### 3.4 Notifications
Prefix: `/notifications/`
| Action | Route | Method | Auth |
|--------|-------|--------|------|
| List | `/list/` | GET | Yes |
| Unread list | `/unread/` | GET | Yes |
| Create | `/create/` | POST | Yes |
| Mark read | `/mark_read/` | POST | Yes |
| Mark **all** read | `/mark_all_read/` | POST | Yes |

---

## 4. Common Status Codes
| Code | When |
|------|------|
| `200 OK` | Successful GET / UPDATE |
| `201 Created` | Successful POST (object created) |
| `204 No Content` | Successful DELETE |
| `400 Bad Request` | Validation failure |
| `401 Unauthorized` | Missing / invalid token |
| `403 Forbidden` | Authenticated but not permitted |
| `404 Not Found` | Resource doesn’t exist |

---

## 5. Error Handling Example
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "email": ["This field must be unique."]
  }
}
```
Front-end should display `message` and map field-level `errors` onto forms.

---

## 6. Postman Collection
File: `docs/kincash_api_collection_v2.json`  
Import → Environment variables:  
* `base_url` – API host  
* `auth_token` – JWT access token (auto-filled after login test)

---

## 7. Contact
Backend: *backend-team@kincash.dev*  
Front-end Dev: *suhail.malik@kincash.dev*

Happy coding 🚀
