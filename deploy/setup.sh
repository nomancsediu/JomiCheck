#!/usr/bin/env bash
# Installs or updates JomiCheck on an Ubuntu server.
# Run from /opt/jomicheck as the ubuntu user:  bash deploy/setup.sh <public-ip-or-domain> [email]
# With a domain and an email, a free Let's Encrypt certificate is set up and HTTP redirects to HTTPS.
# backend/.env must already contain the LLM_* settings; production settings are added here.
set -euo pipefail

HOST="${1:?usage: bash deploy/setup.sh <public-ip-or-domain> [email]}"
EMAIL="${2:-}"
if [ -n "$EMAIL" ] && [[ ! "$HOST" =~ ^[0-9.]+$ ]]; then
  URL="https://$HOST"
else
  URL="http://$HOST"
fi
APP=/opt/jomicheck
cd "$APP"

echo "== System packages"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip nginx curl
if ! command -v node >/dev/null || [ "$(node -p 'process.versions.node.split(".")[0]')" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

if ! swapon --show | grep -q .; then
  echo "== Adding 1 GB swap"
  sudo fallocate -l 1G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "== Backend"
ENV=backend/.env
touch "$ENV"
chmod 600 "$ENV"
set_env() {
  sed -i "/^$1=/d" "$ENV"
  echo "$1=$2" >>"$ENV"
}
grep -q '^DJANGO_SECRET_KEY=' "$ENV" || set_env DJANGO_SECRET_KEY "$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
set_env DJANGO_DEBUG 0
# The frontend calls /api on its own origin through nginx, and QR links use the request host,
# so the site keeps working when the EC2 public IP changes.
set_env DJANGO_ALLOWED_HOSTS "*"
set_env CORS_ALLOWED_ORIGINS "$URL"
set_env CSRF_TRUSTED_ORIGINS "$URL"
set_env FRONTEND_URL ""

[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r backend/requirements.txt gunicorn

(
  cd backend
  ../.venv/bin/python manage.py migrate --noinput
  if [ "$(../.venv/bin/python manage.py shell -c 'from land.models import Mouza; print(Mouza.objects.count())')" = 0 ]; then
    ../.venv/bin/python manage.py seed_demo
  fi
  ../.venv/bin/python manage.py train_anomaly
  ../.venv/bin/python manage.py collectstatic --noinput
)

echo "== Frontend"
(
  cd frontend
  npm ci --no-audit --no-fund
  NEXT_PUBLIC_API_URL="/api" npm run build
)

echo "== Services"
sudo cp deploy/jomicheck-api.service deploy/jomicheck-web.service /etc/systemd/system/
sed "s/server_name _;/server_name $HOST;/" deploy/nginx.conf | sudo tee /etc/nginx/sites-available/jomicheck >/dev/null
sudo ln -sf /etc/nginx/sites-available/jomicheck /etc/nginx/sites-enabled/jomicheck
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now jomicheck-api jomicheck-web
sudo systemctl restart jomicheck-api jomicheck-web nginx

if [[ "$URL" == https://* ]]; then
  echo "== HTTPS certificate"
  sudo apt-get install -y certbot python3-certbot-nginx
  # The nginx config was just replaced, so this also re-installs an existing certificate into it.
  sudo certbot --nginx -d "$HOST" -m "$EMAIL" --agree-tos --non-interactive --redirect --keep-until-expiring
fi

echo "== Done: $URL"
