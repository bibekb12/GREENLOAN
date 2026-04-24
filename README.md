# 🌱 GreenLoan System

A modern web-based **Loan Management System** built using **Python Django**, designed to digitize and simplify the complete loan lifecycle for users and financial institutions.

🔗 **Owner Website:** https://bibekbhandari.com.np

---

# 📌 Project Overview

GreenLoan is a secure and user-friendly platform where customers can:

- Register using Email or Google Login
- Verify email account
- Complete KYC verification
- Apply for different loan products
- Upload required documents
- Track loan application status
- Make loan repayments online
- Receive notifications and updates

At the same time, Admins and Loan Officers can efficiently manage users, verify KYC, review applications, approve/reject loans, and monitor repayments.

---

# 🎯 Main Objectives

The primary objective of GreenLoan is to replace traditional manual loan processing systems with a digital solution that offers:

- Faster loan processing
- Secure document handling
- Better transparency
- Improved customer experience
- Reduced paperwork
- Easy monitoring and reporting

---

# 👥 User Roles

## 1. Customer

- Register/Login
- Verify email
- Complete KYC
- Apply for loan
- Upload documents
- Track application status
- Make repayments

## 2. Loan Officer

- Review assigned applications
- Verify submitted documents
- Recommend approval/rejection

## 3. Admin

- Manage users
- Verify KYC
- Approve or reject loans
- Monitor repayments
- View reports

---

# ⚙️ Features

## 🔐 Authentication System

- Email Registration
- Email Verification
- Secure Login
- Google OAuth Login
- Role-based Access Control

## 🪪 KYC Verification

- Personal Information Submission
- Citizenship Upload
- Passport Photo Upload
- Address & Income Details
- Admin Approval / Rejection

## 💰 Loan Management

- Apply for Loan
- Multiple Loan Types
- Eligibility Validation
- Status Tracking
- Approval Workflow

## 📄 Document Management

- Upload Required Documents
- Verification by Officers
- Secure File Storage

## 💳 Payment & Repayment

- Installment Tracking
- eSewa Integration
- Payment History
- Due Amount Monitoring

## 📊 Dashboard & Reports

- Pending Applications
- Approved Loans
- User Summary
- Payment Records

---

# 🛠️ Technology Stack

## Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript

## Backend

- Python
- Django Framework

## Database

- SQLite (Development)
- PostgreSQL (Production Ready)

## Authentication

- Django Allauth
- Google Login OAuth

## Deployment

- PythonAnywhere / Linux Server

---

# 🧱 Project Structure

```bash
greenloan/
│── accounts/        # User authentication & KYC
│── loans/           # Loan application system
│── payments/        # Repayment & eSewa integration
│── core/            # Shared modules
│── templates/       # HTML templates
│── static/          # CSS / JS / Images
│── media/           # Uploaded files
│── greenloan/       # Main settings
