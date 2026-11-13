# 🚀 Edufix LMS — Production Deployment & Infrastructure Guide

This guide is the single source of truth for **human developers** and **AI agents** managing, updating, and deploying the **Edufix Learning LMS** platform on Namecheap cPanel hosting.

---

## 📌 Architecture Overview

| Component | Technology / Path | Details |
| :--- | :--- | :--- |
| **Framework** | Django 4.2+ (Python 3.12) | Local apps: `core`, `courses`, `users`, `dashboard`, `management` |
| **Web Server / WSGI** | LiteSpeed / CloudLinux + Phusion Passenger | Configured via `passenger_wsgi.py` and `.htaccess` |
| **Application Root** | `/home/afthab/edufixlearning.com` | Root project directory on the live server |
| **Virtual Environment**| `/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python` | CloudLinux cPanel Python Selector venv |
| **Live Database** | `db.sqlite3` (8.1 MB) | Active SQLite production database |
| **Repository** | `https://github.com/brandlumeo/edufixlearning` | Default branch: `main` |
| **CI/CD** | GitHub Actions (`.github/workflows/deploy.yml`) | Automated deployment on push to `main` |

---

## 🚨 CRITICAL DATA SAFETY RULES (READ BEFORE DEPLOYING)

> [!CAUTION]
> **DO NOT overwrite `db.sqlite3` or import `afthab_edufix.sql`!**
> 
> - **The live database is `db.sqlite3`**: It contains **3,082 active students**, **2,003 course enrollments**, **2,003 issued certificates**, and real payment records.
> - **`afthab_edufix.sql` is an old test dump**: It contains only 19 test records from early development. Importing it into production will **permanently erase 3,063 real students and their certificates**!
> - The live database file `db.sqlite3`, uploaded media `media/`, environment file `.env`, and server configuration `.htaccess` are strictly protected in `.gitignore`. **They must NEVER be committed to Git or deleted on the server.**

```
PERSISTENT ON SERVER ONLY (Never commit to Git, never delete during deploy):
├── db.sqlite3            # Real database with 3,000+ student accounts
├── .env                  # Live database credentials & API keys
├── .htaccess             # LiteSpeed environment variables & Passenger root
└── media/                # User uploaded certificates, proofs, and avatars
```

---

## 🔄 Deployment Flow

```mermaid
flowchart TD
    A["Developer / Agent commits to 'main'"] --> B["git push origin main"]
    B --> C["GitHub Actions Triggered (.github/workflows/deploy.yml)"]
    C --> D["Secure SSH Connection to Namecheap (Port 21098)"]
    D --> E["git fetch & git reset --hard to latest commit"]
    E --> F["pip install -r requirements.txt (Dependencies update)"]
    E --> G["python manage.py migrate --noinput (Safe, non-destructive schema update)"]
    E --> H["python manage.py collectstatic --noinput (Static asset compile)"]
    E --> I["touch tmp/restart.txt (Passenger zero-downtime app reload)"]
    I --> J["🎉 Production Site Updated Live!"]
```

---

## 🛠️ Automated CI/CD Setup (GitHub Actions via SSH)

The automated deployment pipeline is pre-configured in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

### 1. Required GitHub Repository Secrets

Navigate to: **GitHub Repo > Settings > Secrets and variables > Actions** and ensure these 4 secrets are configured:

| Secret Name | Required | Example Value | Purpose |
| :--- | :--- | :--- | :--- |
| `CPANEL_SSH_HOST` | **Yes** | `premium293.web-hosting.com` | Server hostname / IP |
| `CPANEL_SSH_USER` | **Yes** | `afthab` | cPanel account username |
| `CPANEL_SSH_PORT` | **Yes** | `21098` | Namecheap SSH port *(Default: 21098)* |
| `CPANEL_SSH_PRIVATE_KEY`| **Yes** | `-----BEGIN OPENSSH PRIVATE KEY----- ...` | Dedicated unencrypted private SSH deploy key |

> [!IMPORTANT]
> **Use an unencrypted deploy key without a passphrase.**
> GitHub Actions runners use `appleboy/ssh-action` (written in Go), which cannot decrypt cPanel's OpenSSL 3.x PBKDF2/AES encrypted private keys. Do **NOT** use a passphrase on the deploy key; leave it unencrypted so the CI runner can authenticate automatically.

### 2. Generating & Authorizing the Key (The Recommended Method)

> [!WARNING]
> **Avoid cPanel's Web "Import Key" form**:
> cPanel's web SSH interface frequently fails with *"Failed to import public key... Invalid key"* if there are spaces in the user's local path/comment. Furthermore, cPanel's web "Generate Key" tool forces a passphrase.
>
> Follow this foolproof 3-step method instead:

#### Step A: Generate an unencrypted key pair on your local machine
In PowerShell / Terminal:
```bash
ssh-keygen -t rsa -b 4096 -f "$HOME/.ssh/id_rsa_edufix_deploy" -N "" -C "edufix-deploy"
```
*(Press Enter. This creates `id_rsa_edufix_deploy` and `id_rsa_edufix_deploy.pub` without a passphrase).*

#### Step B: Authorize the public key on the server
1. Open **cPanel > File Manager** (ensure *Show Hidden Files (dotfiles)* is checked in Settings).
2. Navigate to `/home/afthab/.ssh/`.
3. Open `authorized_keys` in the cPanel code editor.
4. Open your local `id_rsa_edufix_deploy.pub`, copy the entire single line of text, and paste it on a new line at the bottom of `authorized_keys`.
5. Click **Save Changes**.

#### Step C: Add the private key to GitHub Secrets
1. Open your local `id_rsa_edufix_deploy` private key file in Notepad.
2. Copy the entire contents (from `-----BEGIN ...-----` to `-----END ...-----`).
3. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
4. Create or update the repository secret named `CPANEL_SSH_PRIVATE_KEY` with this content.

---

## 📄 Deployment Workflow Script Reference

The workflow executes the following script inside `/home/afthab/edufixlearning.com`:

```bash
# 1. Fetch latest commit using short-lived GitHub workflow token
git fetch https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/brandlumeo/edufixlearning.git main

# 2. Synchronize files (Protected files in .gitignore remain 100% untouched)
git checkout -B main FETCH_HEAD
git reset --hard FETCH_HEAD

# 3. Update dependencies inside cPanel virtual environment
# (Using 'python -m pip' avoids shebang issues from past cPanel account migrations)
/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python -m pip install -r requirements.txt

# 4. Apply new migrations safely
/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python manage.py migrate --noinput

# 5. Compile static assets
/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python manage.py collectstatic --noinput

# 6. Zero-downtime Passenger reload
mkdir -p tmp
touch tmp/restart.txt
```

---

## 📑 Alternative: Native cPanel Git™ Version Control Setup

If SSH is ever temporarily disabled, the project includes [`.cpanel.yml`](.cpanel.yml) for native cPanel deployments:

1. In cPanel, go to **Files** > **Git™ Version Control**.
2. Create or manage the repository linked to `https://github.com/brandlumeo/edufixlearning.git`.
3. In the **Pull or Deploy** tab, copy the **Webhook URL**.
4. In GitHub, go to **Settings > Webhooks > Add webhook**, paste the cPanel webhook URL, set content type to `application/json`, and save.
5. Every push will trigger cPanel to execute the tasks defined in `.cpanel.yml`.

---

## 🤖 Instructions for AI Agents (Antigravity, Cursor, Copilot, Claude)

When working on this repository, all AI agents **MUST** adhere to the following rules:

1. **Database Preservation**:
   - Never run `flush`, `sqlflush`, or `migrate --run-syncdb` on production.
   - Never replace `DATABASES['default']` with an unverified external connection.
   - Always run `python manage.py showmigrations` before applying new schema changes.
2. **Shared Hosting Limitations & GCC**:
   - Namecheap shared hosting blocks compiler execution (`[Errno 13] Permission denied: 'gcc'`).
   - Do **NOT** add packages that require C compilation from source without prebuilt manylinux wheels.
   - Do **NOT** add `mysqlclient` to `requirements.txt`. The production database engine is SQLite3 (`db.sqlite3`).
3. **File Encodings**:
   - Maintain `requirements.txt` in standard **UTF-8 (without BOM)**. Do NOT use PowerShell redirection (`>`) that produces UTF-16 LE.
4. **Secrets Hygiene**:
   - Never hardcode API keys, Razorpay secrets, or email credentials in template or python files.
   - Always read from environment variables via `os.getenv(...)` or `get_env(...)`.
5. **Zero-Downtime Reload**:
   - Whenever code changes are made directly on the server, always run `mkdir -p tmp && touch tmp/restart.txt` to trigger Phusion Passenger reload.
6. **Virtual Environment Executable**:
   - Always invoke pip as `/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python -m pip` to prevent shebang interpreter errors.

---

## 🔍 Troubleshooting & Verification

### 1. Verifying Live App Status
To check if the site reloaded with the newest code without errors:
- Visit: `https://edufixlearning.com/courses/ping/` (Returns HTTP 200 PONG if the latest Django views are running).
- Inspect Passenger error logs on the server:
  ```bash
  tail -n 50 /home/afthab/edufixlearning.com/stderr.log
  ```

### 2. Manual Emergency App Restart
If the web app hangs or does not pick up file changes:
```bash
touch /home/afthab/edufixlearning.com/tmp/restart.txt
```
Or in cPanel: **Setup Python App** > Find `edufixlearning.com` > Click **Restart**.

### 3. Safe Database Backup (Recommended before large migrations)
To back up the live SQLite database at any time:
```bash
cp /home/afthab/edufixlearning.com/db.sqlite3 /home/afthab/edufixlearning.com/db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

