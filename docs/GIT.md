# 🐙 Git Branching & Workflow Guidelines

This document outlines the Git branching strategy, commit message standards, code review practices, and release tagging protocols for the **GreenLoan** system development. Adhering to these guidelines ensures a stable codebase, clear revision history, and seamless collaboration.

---

## 🌿 Branching Strategy

We follow a modified **Git Flow** strategy to coordinate development, bug fixes, and production releases.

```
       [main] ──────────────────────────● [v1.0.0]
         ▲                             /
         │ (Release Merge)            / (Hotfix Merge)
         │                           ▼
      [develop] ───●───────────────●───●
                    \             /     \
                     ▼           ▼       ▼
      [features]      ●───●─────●         ● (bugfix/auth-fix)
                      (feat/oauth)
```

### 1. Primary Branches
*   **`main`**: Represents production-ready code. Commits here must only come from completed and approved pull requests from `develop` (or critical hotfixes). The code on `main` must always compile, pass tests, and run smoothly.
*   **`develop`**: The primary integration branch. Developers merge feature branches here. It serves as the baseline for the next release.

### 2. Supporting Branches
*   **`feature/*`**: Used for developing new features.
    *   *Base branch:* `develop`
    *   *Merge target:* `develop`
    *   *Naming:* `feature/feature-name` (e.g. `feature/esewa-integration`, `feature/face-kyc`)
*   **`bugfix/*`**: Used for fixing issues on the develop branch.
    *   *Base branch:* `develop`
    *   *Merge target:* `develop`
    *   *Naming:* `bugfix/issue-description` (e.g. `bugfix/repayment-interest-round`)
*   **`hotfix/*`**: Used for critical patches required immediately in production.
    *   *Base branch:* `main`
    *   *Merge target:* Both `main` and `develop`
    *   *Naming:* `hotfix/vX.Y.Z-description` (e.g. `hotfix/v1.0.1-login-bypass`)

---

## ✍️ Commit Message Guidelines

We use **Conventional Commits** to keep git logs clear and readable. This formatting allows for automated changelog generation and easier debugging.

### Format
```
<type>(<scope>): <short description>

[optional body description]
```

### Types
*   **`feat`**: A new feature (e.g. `feat(payments): integrate khalti payment gateway`)
*   **`fix`**: A bug fix (e.g. `fix(kyc): handle missing selfie capture file`)
*   **`docs`**: Documentation changes only (e.g. `docs(database): write schema tables`)
*   **`style`**: Changes that do not affect the meaning of the code (formatting, missing semi-colons, etc.)
*   **`refactor`**: A code change that neither fixes a bug nor adds a feature (e.g. `refactor(auth): simplify user signup verification check`)
*   **`test`**: Adding missing tests or correcting existing tests.
*   **`chore`**: Updates to build tasks, package manager configs, etc. (e.g. `chore: update django-allauth version`)

---

## 🔄 Pull Request & Code Review Process

All changes destined for `develop` or `main` must go through a Pull Request (PR) and code review.

### PR Checklist for Authors
1.  **Sync with upstream:** Rebase or merge the target branch (`develop`) into your branch before opening the PR.
2.  **Verify local migrations:** Confirm that all database changes are captured in migration files (`python manage.py makemigrations`).
3.  **Run formatting:** Ensure styles adhere to lint requirements.
4.  **Describe changes:** Provide a clear description of what the PR accomplishes, and list any dependencies.

### Reviewer Guidelines
*   Check for database performance concerns (e.g. N+1 queries, missing indexes).
*   Verify role-based authorization constraints are applied correctly to new views (`LoginRequiredMixin`, `UserPassesTestMixin`).
*   Ensure that any schema modifications are compatible with rolling back states using `HistoricalRecords`.

---

## 🏷️ Release and Tagging Guide

When code on the `develop` branch is stable and ready for a release cycle, it is merged into the `main` branch, and a release tag is created.

### Release Workflow Steps

1.  **Checkout the main branch:**
    ```bash
    git checkout main
    git pull origin main
    ```

2.  **Merge the develop branch:**
    ```bash
    git merge --no-ff develop -m "Merge branch 'develop' into main for release v1.0.0"
    ```

3.  **Tag the release version:**
    Create a semantically versioned git tag:
    ```bash
    git tag v1.0.0
    ```

4.  **Push the tag to the remote repository:**
    ```bash
    git push origin v1.0.0
    ```

5.  **Push main branch updates:**
    ```bash
    git push origin main
    ```

6.  **Backport back to develop:**
    Merge `main` back into `develop` to ensure release hashes remain synchronized:
    ```bash
    git checkout develop
    git merge main
    git push origin develop
    ```