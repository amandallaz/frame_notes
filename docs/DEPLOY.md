# Deploy Frame Notes (DigitalOcean)

Ubuntu 24.04 droplet, nginx + Gunicorn, SQLite, Cloudinary for scans.

## Server layout

- App: `/var/www/frame_notes`
- Socket: `/var/www/frame_notes/run/gunicorn.sock`
- Templates: `deploy/nginx-frame-notes.conf`, `deploy/frame-notes.service`

## 1. Clone

```bash
mkdir -p /var/www
cd /var/www
git clone https://github.com/amandallaz/frame_notes.git
cd frame_notes
```

## 2. Python env

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Environment file

```bash
cp .env.example .env
nano .env
```

Production minimum (subpath at `/framenotes/`):

```env
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<long random string>
DJANGO_SCRIPT_NAME=/framenotes
ALLOWED_HOSTS=amandalaz.com,www.amandalaz.com
CSRF_TRUSTED_ORIGINS=https://amandalaz.com,https://www.amandalaz.com
CLOUDINARY_URL=cloudinary://...
```

If `amandalaz.com` DNS points to **another** droplet (main site), add a `location /framenotes/` block there that `proxy_pass`es to this app server — Frame Notes still needs `DJANGO_SCRIPT_NAME=/framenotes` and nginx serving `/framenotes/` on this box.

Generate a secret key on the server:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4. Django setup

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p run
chown -R www-data:www-data /var/www/frame_notes
```

## 5. Gunicorn (systemd)

```bash
cp deploy/frame-notes.service /etc/systemd/system/frame-notes.service
systemctl daemon-reload
systemctl enable frame-notes
systemctl start frame-notes
systemctl status frame-notes
```

## 6. nginx

Edit `deploy/nginx-frame-notes.conf`: set `server_name` to your IP or domain.

```bash
cp deploy/nginx-frame-notes.conf /etc/nginx/sites-available/frame_notes
ln -sf /etc/nginx/sites-available/frame_notes /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

## 7. HTTPS (when you have a domain)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

Update `.env`: `CSRF_TRUSTED_ORIGINS=https://your-domain.com`

## Updates

```bash
cd /var/www/frame_notes
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart frame-notes
```
