# Deployment Handoff

## Current Status
**Live.** App is running and accessible at `http://40.233.127.51`.

---

## VM Details

| | |
|---|---|
| Provider | Oracle Cloud Infrastructure (OCI) — Always Free |
| Shape | VM.Standard.A1.Flex (1 OCPU, 6 GB RAM, ARM) |
| OS | Ubuntu 24.04 |
| Public IP | `40.233.127.51` (Reserved — permanent) |
| SSH user | `ubuntu` |
| App directory | `/opt/cantina/cantina` |

**SSH command:**
```bash
ssh ubuntu@40.233.127.51
```

---

## What Is Running on the VM

| Component | Details |
|---|---|
| App | Django + Gunicorn in Docker, bound to `127.0.0.1:8000` |
| Database | Postgres 17 in Docker, internal only |
| Reverse proxy | Caddy, listening on `0.0.0.0:80`, proxying to `localhost:8000` |

**Useful commands once SSH'd in:**
```bash
cd /opt/cantina/cantina

docker compose ps                        # check container status
docker compose logs -f web               # follow app logs
docker compose restart web               # restart after .env changes
docker compose up -d --build             # rebuild and restart after code changes
docker compose exec web python manage.py createsuperuser  # create admin user
```

---

## Backups

### Daily DB backup (on the VM)
A cron job runs every day at 3am and dumps the Postgres DB to `/opt/cantina/backups/`.
Keeps the last 14 days. Script: `/opt/cantina/backup.sh`.

```bash
# Check backups exist
ls -lh /opt/cantina/backups/

# Restore from a backup
cat /opt/cantina/backups/backup-YYYY-MM-DD.sql | docker exec -i cantina-db psql -U cantina cantina
```

### Weekly local copy (on your Windows machine)
A Windows Task Scheduler job runs every Tuesday at 9am and SCPs the latest backup to:
`C:\Users\joaov\cantina-backups\`

Script: `C:\Users\joaov\cantina-backups\pull-backup.ps1`

To run manually:
```powershell
powershell -File C:\Users\joaov\cantina-backups\pull-backup.ps1
```

---

## Redeploying After Code Changes

```bash
ssh ubuntu@40.233.127.51
cd /opt/cantina/cantina
git pull
docker compose up -d --build
```

If there are new migrations:
```bash
docker compose exec web python manage.py migrate
```

---

## Optional Next Steps (not done yet)

1. **Get a domain/subdomain** (e.g. free via DuckDNS) and point it to `40.233.127.51`
2. **Enable HTTPS**: update `/etc/caddy/Caddyfile` to use the domain instead of `:80`:
   ```
   your-domain.com {
       reverse_proxy localhost:8000
   }
   ```
   Then update `.env`: `ALLOWED_HOSTS=your-domain.com` and `CSRF_TRUSTED_ORIGINS=https://your-domain.com`
   And reload: `sudo systemctl reload caddy && docker compose restart web`
3. **GitHub Actions CD** — auto-deploy on `git push`

---

## Firewall Notes (already configured, for reference)

OCI has two firewall layers — both were configured:
- **OCI Security List**: ingress rules for TCP 22, 80, 443
- **OS iptables**: rules for 80 and 443 inserted *before* the default REJECT rule (important — rules after line 5 get blocked)
