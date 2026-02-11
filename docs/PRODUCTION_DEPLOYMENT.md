# Production deployment guide (Docker + Postgres + GitHub CD)

This guide gets this project live with a containerized app and database, optimized for very small traffic.

## 1) One-time prep in this repo

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with real values:
   - Strong `SECRET_KEY`
   - Real domain(s) in `ALLOWED_HOSTS`
   - HTTPS URLs in `CSRF_TRUSTED_ORIGINS`
   - Strong `POSTGRES_PASSWORD`

## 2) Provision a low-cost server

For lowest cost, use an always-free VM (for example, Oracle Cloud Always Free ARM).

Install on the VM:
```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

Log out/in so docker group is applied.

## 3) Deploy app manually (first deploy)

```bash
sudo mkdir -p /opt/cantina
sudo chown -R $USER:$USER /opt/cantina
cd /opt/cantina
git clone <your-github-repo-url> .
cp .env.example .env
nano .env

docker compose build --pull
docker compose up -d
```

Check status:
```bash
docker compose ps
docker compose logs -f web
```

Create admin user:
```bash
docker compose exec web python manage.py createsuperuser
```

## 4) Put HTTPS in front (production)

Recommended simple setup:
- Put Nginx/Caddy on the VM as reverse proxy from `443 -> localhost:8000`.
- Use Let's Encrypt certificates.

At minimum, keep port `8000` closed publicly and expose only `80/443`.

## 5) Set up GitHub CD pipeline

This repo includes `.github/workflows/deploy.yml`, which deploys on each push to `main`.

In GitHub repo settings, add these **Actions secrets**:
- `SSH_HOST` (VM public IP or hostname)
- `SSH_USER` (VM user)
- `SSH_PRIVATE_KEY` (private key matching VM authorized key)
- `SSH_PORT` (usually `22`)

On the VM, ensure repo is in `/opt/cantina` and branch is `main`.

## 6) Database backup (must-have)

Use cron on VM:
```bash
crontab -e
```

Example daily backup at 02:30:
```cron
30 2 * * * docker exec cantina-db pg_dump -U cantina cantina | gzip > /opt/cantina/backups/cantina_$(date +\%F).sql.gz
```

Also add a retention cleanup job and sync backups to external storage when possible.

## 7) Health checks and operations

- App logs: `docker compose logs -f web`
- DB logs: `docker compose logs -f db`
- Restart after config change: `docker compose up -d --build`
- Migrations run automatically on container startup via entrypoint.

## 8) Rollback approach

If a deploy breaks:
1. SSH into VM
2. `cd /opt/cantina`
3. `git checkout <last-good-commit>`
4. `docker compose up -d --build`

For safer rollbacks, deploy from Git tags/releases.
