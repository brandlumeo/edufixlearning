# Claude Code Project Guidelines — Edufix LMS

## 1. Project Overview & Hosting
- **Stack**: Django 4.2+ (Python 3.12), Phusion Passenger WSGI on Namecheap CloudLinux.
- **Repository**: `https://github.com/brandlumeo/edufixlearning`, default branch `main`.
- **CI/CD**: GitHub Actions (`.github/workflows/deploy.yml`) automatically deploys every push to `main` via SSH to `/home/afthab/edufixlearning.com`.
- **Deployment Reference**: Read `DEPLOYMENT_GUIDE.md` for full infrastructure specs.

## 2. 🚨 Strict Data Safety Rules
- **Live Database**: The live production database is `db.sqlite3`. It holds **3,082 real users and 2,003 student certificates**.
- **DO NOT** run destructive database commands: `flush`, `sqlflush`, `migrate --run-syncdb`.
- **DO NOT** replace `db.sqlite3` with `afthab_edufix.sql` (an old 19-user test dump).
- **Persistent Server Assets**: `db.sqlite3`, `.env`, `.htaccess`, and `media/` are in `.gitignore`. They must **NEVER** be committed or overwritten.

## 3. Local Development Commands
- **Virtualenv**: Use `.\venv\Scripts\python.exe` on Windows or `/home/afthab/virtualenv/edufixlearning.com/3.12/bin/python` on server.
- **System Check**: `python manage.py check --settings=edufix_lms.local_settings`
- **Make Migrations**: `python manage.py makemigrations`
- **Apply Migrations**: `python manage.py migrate --settings=edufix_lms.local_settings`
- **Show Migrations**: `python manage.py showmigrations`

## 4. Code & Git Hygiene
- **Encoding**: Always save `requirements.txt` in UTF-8 without BOM (never UTF-16).
- **Hosting Limitations**: Namecheap shared hosting blocks `gcc` execution. Never add packages requiring C compilation without prebuilt manylinux wheels; do not re-add `mysqlclient` (app runs on `db.sqlite3`).
- **Secrets**: Never hardcode API keys, Razorpay secrets, or email credentials. Use `get_env(...)`.
- **Zero-Downtime Reload**: In production, reload Passenger by touching `tmp/restart.txt`.

