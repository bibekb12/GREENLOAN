# 🔌 Application Endpoints & Routing Documentation (API)

This document contains a comprehensive catalog of all URL routes, views, HTTP methods, access permissions, and input/output workflows within the **GreenLoan** system. 

GreenLoan is built primarily using **Django Class-Based Views (CBVs)**. The server handles authentication state, verification logic, and updates model states, rendering templates with context or performing redirects based on actions.

---

## 🗺️ Master Route Namespace Directory

The project maps application-specific namespaces in `greenloan/urls.py`:

| Base Path | App Namespace | Description |
| :--- | :--- | :--- |
| `/` | `core` | Public pages, Admin settings, Audit log dashboards. |
| `/app/` | `accounts` | Authentication, registrations, KYC queues, user profiles. |
| `/app/` | `loans` | Applications, uploads, reviews, status updates, repayments. |
| `/payments/` | `payments` | Gateway gateways (eSewa, Khalti) and payment validation callback handles. |
| `/selfverify/` | `kyc` | Automated liveness and facial-matching selfie interfaces. |
| `/accounts/` | `allauth` | Social authentication provider endpoints (Google OAuth). |

---

## 🔑 1. Accounts & Authentication (`accounts` namespace)

### Register User
*   **Path:** `/app/signup/`
*   **View:** `SignupView`
*   **Method:** `GET`, `POST`
*   **Permission:** Open to all.
*   **Workflow:**
    *   `GET`: Renders signup form.
    *   `POST`: Submits user fields (`email`, `password`, `first_name`, `last_name`, `phone`).
    *   **Action:** Sets role to `customer`, saves user, generates verification token, sends verification email, and logs user in. Redirects to `/app/dashboard/`.

### Login User
*   **Path:** `/app/login/`
*   **View:** `CustomLoginView`
*   **Method:** `GET`, `POST`
*   **Permission:** Open to all.
*   **Workflow:**
    *   `GET`: Renders login form. Redirects authenticated users automatically.
    *   `POST`: Authenticates credentials. If `email_verified` is False, stops flow and renders email verification warning. On success, redirects to `/app/landing` (Staff) or `/app/dashboard/` (Customer).

### Logout User
*   **Path:** `/app/logout/`
*   **View:** `CustomLogoutView`
*   **Method:** `POST`
*   **Permission:** Logged-in users.
*   **Workflow:** Terminate authentication session. Redirects to `/` (Home).

### Verify Email
*   **Path:** `/app/email-verify/<uidb64>/<token>`
*   **View:** `EmailAddrVerify`
*   **Method:** `GET`
*   **Permission:** Open to all.
*   **Workflow:** Decodes base64 user ID and validates the token. If valid, updates user's `email_verified` to `True` and `is_active` to `True`. Redirects to `/app/login/` with success message.

### Resend Email Verification
*   **Path:** `/app/email-reverify/`
*   **View:** `ResendEmailAddrVerify`
*   **Method:** `GET`
*   **Permission:** Open to all.
*   **Query Parameter:** `email` (string)
*   **Workflow:** Queries user by email. If already verified, notifies user. If unverified, sends a new email token. Redirects to login page.

### Password Change
*   **Path:** `/app/password/change/`
*   **View:** `ChangePasswordView`
*   **Method:** `GET`, `POST`
*   **Permission:** Logged-in users.
*   **Workflow:** Validates previous password and saves new password. Redirects to `/app/dashboard/`.

### User Dashboard
*   **Path:** `/app/dashboard/`
*   **View:** `DashboardView`
*   **Method:** `GET`
*   **Permission:** Logged-in users.
*   **Workflow:**
    *   **Customer:** Renders dashboard with their own loan applications.
    *   **Admin/Officer:** Renders dashboard listing the top 10 applications, top 10 users, and summary stats (totals, pending applications, pending reviews).

### User Profile and KYC Uploads
*   **Path:** `/app/profile/`
*   **View:** `ProfileView`
*   **Method:** `GET`, `POST`
*   **Permission:** Logged-in users.
*   **Workflow:**
    *   `GET`: Renders profile update forms and KYC file upload fields.
    *   `POST`: Submits either profile details or file attachments. Matches name of request submit action:
        *   `update_profile`: Updates name, phone, permanent/temporary address, occupation, employer, and monthly income fields.
        *   `update_kyc`: Uploads files (`citizenship_front`, `citizenship_back`, `passport_photo`). Validates files exist, transitions `kyc_status` to `submitted`, and resets verification logs. Redirects to `/app/profile/`.

### KYC Queue (Staff View)
*   **Path:** `/app/kyc/`
*   **View:** `KYCListView`
*   **Method:** `GET`
*   **Permission:** Staff members (Admin, Loan Officer, Senior Officer).
*   **Query Parameter:** `status` (string, default: `pending`)
*   **Workflow:** Filters and displays list of users whose KYC profiles match the query status.

### Manual KYC Verification
*   **Path:** `/app/kyc/verify/<pk>/`
*   **View:** `VerifyKYCView`
*   **Method:** `POST`
*   **Permission:** Staff members.
*   **Workflow:** Evaluates POST action key:
    *   `verify`: Transitions target user KYC status to `verified`, stamps current timestamp, and logs the current staff member as the validator.
    *   `reject`: Transitions KYC status to `rejected`.
    *   `reverify`: Transitions status back to `submitted`.
    *   Redirects back to `/app/kyc/?status=submitted`.

---

## 💰 2. Loans & Repayments (`loans` namespace)

### Admin/Officer Landing Overview
*   **Path:** `/app/landing`
*   **View:** `LandingPageView`
*   **Method:** `GET`
*   **Permission:** Staff members.
*   **Query Parameters:**
    *   `range`: Range window type (`today`, `month`, `custom`).
    *   `start`: Starting date string (`YYYY-MM-DD`, if range is `custom`).
    *   `end`: Ending date string (`YYYY-MM-DD`, if range is `custom`).
*   **Workflow:** Renders KPI summaries, including active users, total applications in the range, approved loans, revenue totals, application status charts, KYC metrics, and daily revenue lists.

### Apply for Loan
*   **Path:** `/app/apply_loan`
*   **View:** `ApplyLoanView`
*   **Method:** `GET`, `POST`
*   **Permission:** Customers with `kyc_status` verified.
*   **Workflow:**
    *   `GET`: Renders application form.
    *   `POST`: Submits loan request parameters (`loan_type`, `amount`, `duration_months`, `purpose`, `monthly_income`, `address`, `citizenship_number`). Checks that amount is below the limit defined by `LoanTypes`. Saves application, logs "submitted" history event, and redirects to `/app/application/<pk>/documents/`.

### Loan Details Dashboard
*   **Path:** `/app/application/<int:pk>/`
*   **View:** `ApplicationDetailView`
*   **Method:** `GET`
*   **Permission:** Applicant customer, assigned officer, or general staff.
*   **Workflow:** Details parameters of the application, lists uploaded files, additional requested documents, and exposes action forms to staff based on status workflows.

### Upload Application Documents
*   **Path:** `/app/application/<int:pk>/documents/`
*   **View:** `UploadDocumentsView`
*   **Method:** `GET`, `POST`
*   **Permission:** Applicant customer only.
*   **Workflow:**
    *   `GET`: Lists files that are required by `LoanTypes` but not yet uploaded, alongside a list of additional file requests.
    *   `POST`: Accepts file uploads. Saves files to disk. If application status was `info_requested`, changes it to `info_provided` and logs the action. Redirects to application details page.

### Verify Application Document
*   **Path:** `/app/application/<int:pk>/documents/approvereject`
*   **View:** `DocumentApproveReject`
*   **Method:** `POST`
*   **Permission:** Loan Officer or Senior Officer.
*   **Parameters:** `document_id` (int), `action` (string: `approve` or `reject`).
*   **Workflow:** Updates verification status of the document to `verified` or `rejected`. Logs the audit history. Redirects to application details page.

### Update Application Workflow Status
*   **Path:** `/app/application/<int:pk>/status-update/`
*   **View:** `ApplicationStatusUpdateView`
*   **Method:** `POST`
*   **Permission:** Loan Officer or Senior Officer.
*   **Parameters:** `action` (string: `approve`, `reject`, `verify`, `request_info`, `info_provided`, `final_review`).
*   **Special Actions:**
    *   `request_info`: Reads `additional_docs` array from POST, creates blank `Document` placeholder records with `is_additional=True`, and changes status to `info_requested`.
    *   `approve`: Transitions status to `approved`. Creates `ApprovedLoans` record, generates monthly `Repayment` schedule objects, and fires the `loan_approved_signal`.
    *   `reject`: Transitions status to `rejected` and fires the `loan_reject_signal`.
    *   Redirects back to referrer URL or dashboard.

### Installment Repayment Schedule
*   **Path:** `/app/repayments/`
*   **View:** `RepaymentListView`
*   **Method:** `GET`
*   **Permission:** Logged-in customer.
*   **Query Parameter:** `loan_id` (int)
*   **Workflow:** Shows all approved loans. If a `loan_id` is supplied, fetches and sorts corresponding repayments by state (`pending`, `late`, then `paid`) and due date.

### Bulk Repayment Pre-Payment
*   **Path:** `/app/repayment/bulk-pay/`
*   **View:** `BulkRepaymentPayView`
*   **Method:** `POST`
*   **Permission:** Logged-in customer.
*   **Parameters:** `repayment_ids` (list of ints), `amount` (decimal).
*   **Workflow:** Saves selection list and sum value to session variables (`selected_repayments` and `selected_amount`). Redirects to `/app/repayments/confirm/`.

### Confirm Bulk Repayments
*   **Path:** `/app/repayments/confirm/`
*   **View:** `BulkRepaymentConfirmView`
*   **Method:** `GET`, `POST`
*   **Permission:** Logged-in customer.
*   **Workflow:**
    *   `GET`: Displays the selected repayments and total amount due.
    *   `POST`: Reads payment method (`esewa`, `khalti`, or others). Saves to session `payment_method`. Redirects to:
        *   `esewa`: `/payments/esewa-pay/`
        *   `khalti`: `/payments/khalti/pay`
        *   demo: `/payments/process/`

---

## 💳 3. Payments Integration (`payments` namespace)

### Process Demo Payment
*   **Path:** `/payments/process/`
*   **View:** `PaymentMethodView`
*   **Method:** `POST`
*   **Permission:** Logged-in customer.
*   **Workflow:** Reads the selected repayments and amount from the session. Iterates through the repayments, applying the payment amount to the oldest unpaid installment first. Updates amount paid, paid date, status, logs `Payment` record, updates credit score, and clears session. Redirects to `/app/repayments/`.

### Initiate eSewa Gateway Transaction
*   **Path:** `/payments/esewa-pay/`
*   **View:** `EsewaPaymentView`
*   **Method:** `GET`
*   **Permission:** Logged-in customer.
*   **Workflow:** 
    *   Calculates payment total, generates unique `transaction_uuid`, and logs a `PENDING` `EsewaPayment` attempt record.
    *   Signs the payload values using HMAC-SHA256 with the merchant secret key.
    *   Renders a form (`payments/esewa_form.html`) containing parameters (`amount`, `tax_amount`, `product_service_charge`, `product_delivery_charge`, `product_code`, `transaction_uuid`, `signed_field_names`, `signature`, `success_url`, `failure_url`) which submits to the eSewa endpoint.

### eSewa Success Callback handler
*   **Path:** `/payments/esewa-success/`
*   **View:** `EsewaSuccessView`
*   **Method:** `GET`
*   **Permission:** Logged-in customer.
*   **Query Parameter:** `data` (base64 encoded JSON string from eSewa)
*   **Workflow:**
    *   Decodes the callback string to extract transaction ID, amount, and reference code.
    *   Retrieves session repayments list and processes them.
    *   Creates a `Payment` object referencing the eSewa transaction code.
    *   Recalculates credit score based on repayment punctuality, clears active session variables, and redirects to repayments page.

### eSewa Failure Callback handler
*   **Path:** `/payments/esewa-failure/`
*   **View:** `EsewaFailureView`
*   **Method:** `GET`
*   **Query Parameter:** `transaction_uuid`, `product_code`, `total_amount`
*   **Workflow:** Looks up the `EsewaPayment` log and updates its status to `FAILURE`. Clears active sessions and redirects back to repayments.

### Initiate Khalti Payment Gateway
*   **Path:** `/payments/khalti/pay`
*   **View:** `KhaltiPaymentView`
*   **Method:** `GET`
*   **Permission:** Logged-in customer.
*   **Workflow:** Formulates initiate request with JSON body (`return_url`, `website_url`, `amount` in paisa, `purchase_order_id`, `purchase_order_name`, `customer_info`). Posts request to Khalti sandbox API, reads redirect url, and redirects user to checkout gateway.

---

## 🪪 4. KYC Face Verification (`kyc` namespace)

### Submit Camera Capture
*   **Path:** `/selfverify/kycselfverify/`
*   **View:** `KYCVerificationView`
*   **Method:** `GET`, `POST`
*   **Permission:** Logged-in customer.
*   **Workflow:**
    *   `GET`: Displays the webcam live capture page. Assures passport photo exists on profile.
    *   `POST`: Receives base64-encoded webcam photo.
        *   Converts base64 to image file and stores in `/media/kyc/selfie/`.
        *   Logs attempt database object `KYCVerification`.
        *   Calls `DeepFace.verify` with OpenCV backend, matching camera selfie to profile passport photo.
        *   Computes match confidence (`(1 - distance) * 100`).
        *   If matches, sets user `kyc_status` to `verified`, saves verification details, updates session auth hashes, and redirects to results page.
        *   If match fails, sets `kyc_status` to `rejected` and redirects.

### Verification Results Page
*   **Path:** `/selfverify/result/`
*   **View:** `KYCResultView`
*   **Method:** `GET`
*   **Permission:** Logged-in customer.
*   **Workflow:** Displays the selfie verification results, match status, confidence score, and images.

---

## ⚙️ 5. Public, settings & Audit Logs (`core` namespace)

### System Settings Panel
*   **Path:** `/settings/`
*   **View:** `SystemSettingsListView`
*   **Method:** `GET`
*   **Permission:** Admin only.
*   **Workflow:** Renders links to settings panels.

### View Customers Directory
*   **Path:** `/settings/users/`
*   **View:** `UserListView`
*   **Method:** `GET`
*   **Permission:** Admin only.
*   **Workflow:** Paginated list of all users with role `customer`.

### View Staff Directory
*   **Path:** `/settings/admins/`
*   **View:** `AdminListView`
*   **Method:** `GET`
*   **Permission:** Admin only.
*   **Workflow:** Paginated list of users with role other than `customer`.

### Create User Accounts manually
*   **Paths:** `/settings/users/create/` (Customers), `/settings/admin/create/` (Staff)
*   **Views:** `UserCreateView` and `AdminCreateView`
*   **Method:** `GET`, `POST`
*   **Permission:** Admin only.
*   **Workflow:** Creates account with role set manually via POST variables. Redirects to directories.

### Site Global Configuration
*   **Path:** `/settings/sitesetting`
*   **View:** `SitePageSettingsView`
*   **Method:** `GET`, `POST`
*   **Permission:** Admin only.
*   **Workflow:**
    *   `GET`: Shows current allowed monthly repayment income percentage, and active loan product rules.
    *   `POST`: Evaluates submission form action:
        *   `allowed_percent_save`: Modifies the allowed income percentage threshold in database.
        *   `loan_types_save`: Validates name uniqueness, maps JSON required documents list, and updates or inserts new product rule specifications.

### Audit Log Dashboard
*   **Path:** `/auditlog/`
*   **View:** `AuditModelListView`
*   **Method:** `GET`
*   **Permission:** Logged-in admin.
*   **Workflow:** Lists models tracked by `django-simple-history` (currently `Application`, `User`).

### Audit Log Records
*   **Path:** `/auditlog/<str:model>/`
*   **View:** `AuditLogView`
*   **Method:** `GET`
*   **Permission:** Admin only.
*   **Workflow:** Fetches all historical model rows, compares field values between subsequent records, and lists modified values alongside target dates and users.

### Historical Rollback Action
*   **Path:** `/rollback/<str:model>/<int:history_id>/`
*   **View:** `RollbackView`
*   **Method:** `POST`
*   **Permission:** Admin only.
*   **Workflow:** Fetches the historical record by ID. Re-saves the instance, restoring it to the historical state. Redirects to caller URL.

---

## 🛠️ 6. Migration Utility

### Run Migrations & Seed Data
*   **Path:** `/run-migration/`
*   **View:** `migrate_view`
*   **Method:** `GET`
*   **Permission:** Open to all.
*   **Workflow:** Executes Django commands programmatically:
    1.  `call_command('migrate', interactive=False)`
    2.  `call_command('collectstatic', interactive=False, clear=True)`
    3.  `call_command('loaddata', 'loan_types')`
    *   Returns confirmation response on success or error details on failure.
