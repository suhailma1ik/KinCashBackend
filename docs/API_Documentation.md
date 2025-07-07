# H.E.L.P Backend API Documentation

This document outlines the API endpoints and their expected request/response structures for the `user` and `loan` applications.

## API Conventions

* **Versioning** – All production paths are prefixed with `/api/v1/`. Future breaking changes will bump the prefix (e.g., `/api/v2/`).
* **Headers**  
  * `Authorization: Bearer <access_token>` — required for protected endpoints  
  * `Content-Type: application/json`
* **Response Envelope**

  Successful responses:
  ```json
  {
      "status": 200,
      "message": "OK",
      "data": {}
  }
  ```

  Error responses:
  ```json
  {
      "status": 400,
      "message": "Validation failed",
      "errors": { "field": ["msg"] }
  }
  ```

* **Pagination & Filtering** – List endpoints accept `page`, `page_size`, `ordering`, `start_date`, and `end_date` query parameters. Paginated responses wrap results in the following structure:

  ```json
  {
      "status": 200,
      "message": "OK",
      "data": {
          "results": [],
          "count": 0,
          "next": null,
          "previous": null
      }
  }
  ```

* **Idempotency** – All payment-creation endpoints accept an `Idempotency-Key` header. Re-using the same key returns the previous result instead of creating a duplicate record.

* **Status Codes** –  
  * `200 OK` / `201 Created` for success  
  * `204 No Content` when the body is deliberately empty  
  * `400 Bad Request` for malformed data  
  * `401 Unauthorized` / `403 Forbidden` for auth issues  
  * `422 Unprocessable Entity` for validation errors  
  * `5xx` for server errors

* **Web-hooks / Realtime** – The service will publish events over WebSocket at `/ws/notifications/` for changes such as loan acceptance or EMI payment.


## User Application Endpoints

#### 1. `POST /api/user/signup/`
*   **View Function**: `signUp`
*   **Description**: Registers a new user.
*   **Request Body**:
    ```json
    {
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "password": "securepassword",
        "first_name": "John",
        "last_name": "Doe"
    }
    ```
    (Fields like `email`, `phone_number`, `password` are expected, and `first_name`, `last_name` are optional based on `RegistrationSerializer`.)
*   **Successful Response (HTTP 201 Created)**:
    ```json
    {
        "token": {
            "refresh": "refresh_token_string",
            "access": "access_token_string"
        },
        "data": {
            "id": "user_id",
            "email": "user@example.com",
            "phone_number": "+1234567890",
            "first_name": "John",
            "last_name": "Doe"
            // ... other user fields from RegistrationSerializer, excluding password
        },
        "msg": "Registration successful with your phone number!" // or "Registration successful with your email address!" or "Registration successful!"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Email/Phone already registered)**:
    ```json
    {
        "msg": "Email is already registered.", // or "Phone number is already registered."
        "status": 400
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Validation failed)**:
    ```json
    {
        "data": {
            "field_name": ["error_message"] // e.g., "email": ["Enter a valid email address."]
        },
        "status": 400,
        "msg": "Validation failed"
    }
    ```
*   **Error Response (HTTP 500 Internal Server Error - Unexpected error)**:
    ```json
    {
        "msg": "An unexpected error occurred. Please try again later.",
        "status": 500
    }
    ```

#### 2. `POST /api/user/login/`
*   **View Function**: `login`
*   **Description**: Authenticates a user and returns JWT tokens.
*   **Request Body**:
    ```json
    {
        "phone_number": "+1234567890", // Can also be email
        "password": "securepassword"
    }
    ```
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "token": {
            "refresh": "refresh_token_string",
            "access": "access_token_string"
        },
        "user": {
            "id": "user_id",
            "email": "user@example.com",
            "phone_number": "+1234567890",
            "first_name": "John",
            "last_name": "Doe"
            // ... other user fields from RegistrationSerializer
        }
    }
    ```
*   **Error Response (HTTP 404 Not Found - User not found)**:
    ```json
    {
        "error": "User not found"
    }
    ```
*   **Error Response (HTTP 401 Unauthorized - Incorrect password)**:
    ```json
    {
        "error": "Password is incorrect"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Validation failed)**:
    ```json
    {
        "error": {
            "field_name": ["error_message"] // e.g., "phone_number": ["This field is required."]
        }
    }
    ```

#### 3. `GET /api/user/get-user/`
*   **View Function**: `get_user_details_by_phone_email_or_id`
*   **Description**: Retrieves user details by phone number, email, or ID. Requires authentication.
*   **Query Parameters**:
    *   `phone_number` (optional)
    *   `email` (optional)
    *   `id` (optional)
    (At least one of `phone_number` or `email` or `id` is required)
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "id": "user_id",
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "first_name": "John",
        "last_name": "Doe"
        // ... other user fields from UserSerializer
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Missing parameters)**:
    ```json
    {
        "error": "At least one of phone number or email is required"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Invalid data)**:
    ```json
    {
        "error": "Invalid data provided"
    }
    ```
*   **Error Response (HTTP 404 Not Found - User not found)**:
    ```json
    {
        "detail": "Not found." // Default Django REST Framework message for get_object_or_404
    }
    ```

#### 4. `POST /api/user/logout/`
*   **View Function**: `logout`
*   **Description**: Blacklists the current access token, effectively logging out the user.
*   **Request Headers**: `Authorization: Bearer <access_token>`
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "status": 200,
        "msg": "Logout successfully!"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Logout failed)**:
    ```json
    {
        "status": 400,
        "msg": "Logout failed!"
    }
    ```

#### 5. `POST /api/user/refresh-token/`
*   **View Function**: `refresh_token`
*   **Description**: Refreshes an expired access token using a refresh token.
*   **Request Body**:
    ```json
    {
        "refresh": "your_refresh_token"
    }
    ```
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "access": "new_access_token",
        "refresh": "your_refresh_token" // The same refresh token is returned
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Missing refresh token)**:
    ```json
    {
        "error": "Refresh token is required"
    }
    ```
*   **Error Response (HTTP 401 Unauthorized - Invalid/Expired refresh token)**:
    ```json
    {
        "error": "Invalid or expired refresh token"
    }
    ```

#### 6. `POST /api/user/google-auth/`
*   **View Function**: `google_auth`
*   **Description**: Handles Google authentication, creating a new user or logging in an existing one.
*   **Request Body**:
    ```json
    {
        "email": "google_user@gmail.com",
        "name": "Google User",
        "given_name": "Google",
        "family_name": "User"
        // ... other user info from Google
    }
    ```
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "email": "google_user@gmail.com",
        "first_name": "Google",
        "phone_number": "generated_uuid_phone_number",
        "id": "user_id",
        "is_new": true, // or false if user already existed
        "token": {
            "refresh": "refresh_token_string",
            "access": "access_token_string"
        }
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Email not found)**:
    ```json
    {
        "error": "Invalid Google token, email not found"
    }
    ```
*   **Error Response (HTTP 500 Internal Server Error - Unexpected error)**:
    ```json
    {
        "msg": "An unexpected error occurred during registration.",
        "error": "error_message_details",
        "status": 500
    }
    ```

#### 7. `PATCH /api/user/update_profile/`
*   **View Function**: `update_profile`
*   **Description**: Updates the authenticated user's profile information (phone number, email). Requires authentication.
*   **Request Body**:
    ```json
    {
        "phone_number": "+1987654321", // Optional
        "email": "new_email@example.com" // Optional
    }
    ```
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "message": "User updated successfully",
        "user": {
            "email": "updated_email@example.com",
            "phone_number": "+1987654321"
        }
    }
    ```

#### 8. `GET /api/user/ping/`
*   **View Function**: `ping`
*   **Description**: A simple health check endpoint.
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "message": "pong"
    }
    ```

## Loan Application Endpoints

#### 1. `POST /api/loan/create_loan/`
*   **View Function**: `create_loan` (from `loan.views.loan_views`)
*   **Description**: Creates a new loan and generates its payment schedule.
*   **Request Body**:
    ```json
    {
        "amount": 1000.00,
        "interest_rate": 5.0,
        "loan_term": 12, // in months or weeks depending on emi_cycle
        "emi_cycle": "monthly", // or "weekly"
        "due_date": 15, // Day of the month for EMI due date (1-31)
        "lender": "lender_user_id",
        "borrower": "borrower_user_id",
        "is_lender": false // true if the current user is the lender, false if borrower
    }
    ```
*   **Successful Response (HTTP 201 Created)**:
    ```json
    {
        "id": "loan_id",
        "amount": 1000.00,
        "interest_rate": 5.0,
        "loan_term": 12,
        "emi_cycle": "monthly",
        "lender": "lender_user_id",
        "borrower": "borrower_user_id",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "status": "PENDING_BORROWER" // or "PENDING_LENDER"
        // ... other fields from LoanSerializer
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Validation errors)**:
    ```json
    {
        "field_name": ["error_message"] // e.g., "amount": ["A valid number is required."]
    }
    ```

#### 2. `GET /api/loan/<int:loan_id>/schedule/`
*   **View Function**: `get_emi_schedule` (from `loan.views.payments_views`)
*   **Description**: Retrieves the full EMI schedule for a specific loan. Requires authentication.
*   **Path Parameters**: `loan_id` (integer)
*   **Successful Response (HTTP 200 OK)**:
    ```json
    [
        {
            "id": "schedule_id_1",
            "loan": "loan_id",
            "due_date": "YYYY-MM-DD",
            "principal_due": 100.00,
            "interest_due": 5.00,
            "total_due": 105.00,
            "payment_status": "unpaid",
            "lender": "lender_user_id",
            "borrower": "borrower_user_id"
        },
        // ... more schedule entries
    ]
    ```
*   **Error Response (HTTP 404 Not Found - No schedules found)**:
    ```json
    {
        "detail": "No schedules found for this loan"
    }
    ```
*   **Error Response (HTTP 404 Not Found - Loan not found)**:
    ```json
    {
        "detail": "Loan not found"
    }
    ```

#### 3. `GET /api/loan/<int:loan_id>/<int:emi_id>/schedule/`
*   **View Function**: `get_emi` (from `loan.views.payments_views`)
*   **Description**: Retrieves details for a specific EMI within a loan. Requires authentication.
*   **Path Parameters**: `loan_id` (integer), `emi_id` (integer)
*   **Successful Response (HTTP 200 OK)**:
    ```json
    [
        {
            "id": "emi_id",
            "loan": "loan_id",
            "due_date": "YYYY-MM-DD",
            "principal_due": 100.00,
            "interest_due": 5.00,
            "total_due": 105.00,
            "payment_status": "unpaid",
            "lender": "lender_user_id",
            "borrower": "borrower_user_id"
        }
    ]
    ```
*   **Error Response (HTTP 404 Not Found - No EMI found)**:
    ```json
    {
        "detail": "No emi found for this loan"
    }
    ```
*   **Error Response (HTTP 404 Not Found - EMI not found)**:
    ```json
    {
        "detail": "emi not found"
    }
    ```

#### 4. `POST /api/loan/pay_emi/`
*   **View Function**: `pay_emi` (from `loan.views.payments_views`)
*   **Description**: Records a payment for a specific EMI and updates its status. Requires authentication.
*   **Request Body**:
    ```json
    {
        "loan_id": "loan_id",
        "emi_id": "emi_id",
        "amount": 105.00,
        "payment_date": "YYYY-MM-DD",
        "payment_method": "Bank Transfer" // or "Cash", "Online" etc.
    }
    ```
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "payment": {
            "id": "payment_id",
            "loan": "loan_id",
            "emi_id": "emi_id",
            "amount": 105.00,
            "payment_date": "YYYY-MM-DD",
            "payment_method": "Bank Transfer"
        },
        "transaction": {
            "id": "transaction_id",
            "loan": "loan_id",
            "payment": "payment_id",
            "transaction_type": "credit", // or "debit"
            "amount": 105.00,
            "description": "Payment of EMI <emi_id> for loan <loan_id>"
        }
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Missing fields)**:
    ```json
    {
        "detail": "All fields are required"
    }
    ```
*   **Error Response (HTTP 404 Not Found - Loan not found)**:
    ```json
    {
        "detail": "Loan not found"
    }
    ```
*   **Error Response (HTTP 404 Not Found - EMI not found)**:
    ```json
    {
        "detail": "EMI (LoanSchedule) not found"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - EMI already paid)**:
    ```json
    {
        "detail": "EMI already paid"
    }
    ```
*   **Error Response (HTTP 400 Bad Request - Validation errors for payment/transaction)**:
    ```json
    {
        "field_name": ["error_message"] // e.g., "amount": ["A valid number is required."]
    }
    ```

#### 5. `GET /api/loan/get_loans/`
*   **View Function**: `get_loans` (from `loan.views.loan_views`)
*   **Description**: Retrieves all loans associated with the authenticated user (as borrower or lender), along with sums of payments sent and received in the current month. Requires authentication.
*   **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "loans": [
            {
                "id": "loan_id_1",
                "amount": 1000.00,
                "interest_rate": 5.0,
                "loan_term": 12,
                "emi_cycle": "monthly",
                "lender": "lender_user_id",
                "borrower": "borrower_user_id",
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "status": "Active"
                // ... other fields from LoanSerializer
            },
            // ... more loan entries
        ],
        "payments_sent": 500.00, // Sum of payments sent by the user in the current month
        "payments_received": 300.00 // Sum of payments received by the user in the current month
    }
    ```

#### 6. `GET /api/loan/get_loans_by_id/`
*   **View Function**: `get_loan_schedule_by_id` (from `loan.views.loan_views`)
*   **Description**: Retrieves the loan schedule for a specific loan ID. (Note: This endpoint name is slightly misleading as it returns schedules, not loans directly). Requires authentication.
*   **Query Parameters**: `id` (loan ID)
*   **Successful Response (HTTP 200 OK)**:
    ```json
    [
        {
            "id": "schedule_id_1",
            "loan": "loan_id",
            "due_date": "YYYY-MM-DD",
            "principal_due": 100.00,
            "interest_due": 5.00,
            "total_due": 105.00,
            "payment_status": "unpaid",
            "lender": "lender_user_id",
            "borrower": "borrower_user_id"
        },
        // ... more schedule entries
    ]
    ```

#### 7. `GET /api/loan/get_transactions_done/`
*   **View Function**: `get_loans` (from `loan.views.loan_views`)
*   **Description**: This endpoint maps to the same `get_loans` view function as `/api/loan/get_loans/`. It will return the same response structure.
*   **Successful Response (HTTP 200 OK)**: (Same as `/api/loan/get_loans/`)
    ```json
    {
        "loans": [ ... ],
        "payments_sent": ...,
        "payments_received": ...
    }
    ```

#### 8. `GET /api/loan/get_user_payments/`
*   **View Function**: `get_all_payments_related_to_user` (from `loan.views.payments_views`)
*   **Description**: Retrieves all loan schedules (payments) related to the authenticated user, filtered by payment type (received or sent). Requires authentication.
*   **Query Parameters**: `paymentType` (string, 'received' or 'sent')
*   **Successful Response (HTTP 200 OK)**:
    ```json
    [
        {
            "id": "schedule_id_1",
            "loan": "loan_id",
            "due_date": "YYYY-MM-DD",
            "principal_due": 100.00,
            "interest_due": 5.00,
            "total_due": 105.00,
            "payment_status": "unpaid",
            "lender": "lender_user_id",
            "borrower": "borrower_user_id"
        },
        // ... more schedule entries
    ]
    ```

#### 9. `POST /api/loan/accept_loan/`
*   **View Function**: `accept_loan` (from `loan.views.payments_views`)
*   **Description**: Changes the status of a loan to 'Active'. Requires authentication.
*   **Request Body**:
    ```json
    {
        "loan_id": "loan_id"
    }
    ```
*   **Successful Response (HTTP 200 OK)**: (Empty response body, or potentially a success message)
    ```json
    {}
    ```
*   **Error Response (HTTP 404 Not Found - Loan not found)**:
    ```json
    {
        "detail": "Loan not found"
    }
    ```

## Additional User Endpoints

#### `POST /api/v1/user/logout/`
* **Description**: Invalidates the current refresh token and logs the user out.
* **Headers**: `Authorization`
* **Successful Response (HTTP 204 No Content)**  
  Body is empty.

#### `POST /api/v1/user/token/refresh/`
* **Description**: Exchanges a refresh token for a new access token.
* **Request Body**:
    ```json
    { "refresh": "<refresh_token>" }
    ```
* **Successful Response (HTTP 200 OK)**:
    ```json
    {
        "status": 200,
        "message": "OK",
        "data": { "access": "<new_access_token>" }
    }
    ```

#### `POST /api/v1/user/password-reset/request/`
* **Description**: Sends a password-reset OTP to the user's email or phone.
* **Request Body**:
    ```json
    { "phone_number": "+1234567890" }
    ```
* **Successful Response (HTTP 200 OK)**:
    ```json
    { "status": 200, "message": "OTP sent" }
    ```

#### `POST /api/v1/user/verify-otp/`
* **Description**: Verifies an OTP during signup or password reset.
* **Request Body**:
    ```json
    {
        "phone_number": "+1234567890",
        "otp": "123456"
    }
    ```
* **Successful Response (HTTP 200 OK)**:
    ```json
    { "status": 200, "message": "OTP verified" }
    ```

## Data Definitions

| Name | Allowed Values |
|------|----------------|
| **LoanStatus** | `Pending`, `Active`, `Closed`, `Defaulted` |
| **PaymentStatus** | `unpaid`, `paid`, `overdue` |
| **EmiCycle** | `daily`, `weekly`, `monthly` |

