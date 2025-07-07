# Kincash – Backend Data Model (Locked)

Tech stack: Node.js + Express + PostgreSQL (SQL, ACID-safe).

This document captures the **authoritative** v1 schema after USER approval.  Future changes must follow a formal migration process.

---

## 1. `users`
| column | type | constraints |
|--------|------|-------------|
| id | UUID | PK, default gen_random_uuid() |
| full_name | TEXT | NOT NULL |
| email | TEXT | UNIQUE, NOT NULL |
| phone | TEXT | UNIQUE, NOT NULL |
| hashed_password | TEXT | NOT NULL |
| kyc_status | ENUM(`pending`,`verified`,`rejected`) | `pending` default |
| created_at | TIMESTAMP | default now() |
| updated_at | TIMESTAMP | default now() |

### Indexes
* `UNIQUE (email)`
* `UNIQUE (phone)`

---

## 2. `loans`
| column | type | constraints |
|--------|------|-------------|
| id | UUID | PK |
| lender_id | UUID | FK → users.id |
| borrower_id | UUID | FK → users.id |
| principal_amount | NUMERIC(14,2) | NOT NULL |
| interest_rate_pct | NUMERIC(5,2) | annualised rate |
| term_months | INT | total tenure in months |
| frequency | ENUM(`monthly`,`weekly`) | repayment cadence, default `monthly` |
| status | ENUM(`pending`,`active`,`paid`,`defaulted`,`cancelled`) | `pending` default |
| late_fee_pct | NUMERIC(5,2) | percent of overdue amount per period (optional) |
| created_at | TIMESTAMP | default now() |
| approved_at | TIMESTAMP | nullable |
| closed_at | TIMESTAMP | nullable |

### Indexes
* `INDEX (lender_id)`
* `INDEX (borrower_id)`

---

## 3. `repayment_schedules`
Holds every expected instalment (EMI).  Supports both monthly and weekly frequencies.

| column | type | constraints |
|--------|------|-------------|
| id | SERIAL | PK |
| loan_id | UUID | FK → loans.id |
| due_date | DATE | NOT NULL |
| amount_due | NUMERIC(14,2) | NOT NULL |
| amount_paid | NUMERIC(14,2) | default 0 |
| interest_component | NUMERIC(14,2) | portion of `amount_due` that is interest |
| late_fee_accrued | NUMERIC(14,2) | default 0, recalculated on overdue |
| paid_at | TIMESTAMP | nullable |
| status | ENUM(`due`,`paid`,`late`) | `due` default |

### Indexes
* `INDEX (loan_id, due_date)` – fast next-EMI lookup

---

## 4. `payments`
Represents a borrower marking an instalment or partial/early payment.  Cash movement is **manual/out-of-band** for now; gateway integration TBD.

| column | type | constraints |
|--------|------|-------------|
| id | UUID | PK |
| loan_id | UUID | FK → loans.id |
| payer_id | UUID | FK → users.id |
| amount | NUMERIC(14,2) | NOT NULL |
| remarks | TEXT | optional note (e.g. bank ref) |
| paid_at | TIMESTAMP | NOT NULL |

### Indexes
* `INDEX (loan_id)`

---

## 5. `transactions`
Immutable ledger snapshots for audit & statements.

| column | type | constraints |
|--------|------|-------------|
| id | UUID | PK |
| from_user_id | UUID | FK → users.id, nullable (system) |
| to_user_id | UUID | FK → users.id |
| amount | NUMERIC(14,2) | NOT NULL |
| type | ENUM(`loan_disbursement`,`repayment`,`late_fee`,`refund`) |
| related_id | UUID | references loan or payment id |
| created_at | TIMESTAMP | default now() |

### Indexes
* `INDEX (to_user_id, created_at DESC)` – recent statements

---

## 6. `notifications`
System & lender-initiated push/in-app messages.

| column | type | constraints |
|--------|------|-------------|
| id | UUID | PK |
| loan_id | UUID | FK → loans.id, nullable |
| sender_id | UUID | FK → users.id |  // lender id for EMI reminders |
| recipient_id | UUID | FK → users.id |
| title | TEXT | NOT NULL |
| body | TEXT | NOT NULL |
| is_read | BOOLEAN | default false |
| created_at | TIMESTAMP | default now() |

---

## Behavioural Notes
1. **Loan Creation**
   • status=`pending` until borrower accepts.
   • Upon activation, backend generates `repayment_schedules` rows:
     – For `monthly`: due every calendar month over `term_months`.
     – For `weekly`: due every 7 days; `term_months` is still total tenure, or compute `weeks = term_months * 4`.
2. **Late Fees**
   • If a schedule is overdue, `late_fee_pct` is applied on outstanding `amount_due` and added to `late_fee_accrued` each period (daily/weekly as per policy).
   • A `transactions` row of type `late_fee` is created.
3. **Payment Flow**
   • Borrower records a payment via API → `payments` row.
   • Service allocates amount to the earliest `repayment_schedule` rows, updating `amount_paid` & `status` accordingly.
   • When a schedule becomes fully paid, backend may send an automatic **notification** to lender & borrower.
4. **Lender Reminder**
   • A lender can trigger `POST /loans/:id/notify` which inserts a `notifications` row targeting borrower with context of current EMI.
5. **Loan Completion**
   • When every schedule is `paid`, `loans.status` → `paid` & `closed_at` set.

---

## Migration Strategy
Use **Knex.js** migrations (`/migrations/*.js`) to create tables & enums in the order above.

---

*Document version*: 2025-06-24T02:54 IST – **LOCKED**
