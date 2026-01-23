# SSL Certificates Directory

Place your SSL certificates here for production deployment:

## Required files

- `fullchain.pem` - Your SSL certificate + intermediate certificates
- `privkey.pem` - Your private key

## Using Let's Encrypt (recommended)

```bash
# Install certbot
sudo apt install certbot

# Generate certificate (standalone mode)
sudo certbot certonly --standalone -d bi.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/bi.yourdomain.com/fullchain.pem ./deploy/nginx/ssl/
sudo cp /etc/letsencrypt/live/bi.yourdomain.com/privkey.pem ./deploy/nginx/ssl/

# Set permissions
chmod 600 ./deploy/nginx/ssl/*.pem
```

## Using self-signed certificate (testing only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/CN=localhost"
```

## Important

- Never commit private keys to git
- The `ssl/` directory is in `.gitignore`
- Renew Let's Encrypt certificates every 90 days
