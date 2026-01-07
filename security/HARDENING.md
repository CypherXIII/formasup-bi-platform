# Production Hardening Guidelines

This document provides a checklist of security hardening steps that should be taken before deploying the FormaSup BI Platform to a production environment.

## 1. Network Security

- [ ] **Firewall**: Configure a firewall on the host machine to only allow traffic on necessary ports (e.g., 80, 443).
- [ ] **Reverse Proxy**: Deploy the application behind a reverse proxy (like Nginx or Traefik) to handle SSL/TLS termination and provide an additional layer of security. An example Nginx configuration is provided in the `deploy` directory.
- [ ] **Remove Public Port Mappings**: In the `docker-compose.yml` file, remove the `ports` section from the `postgres` and `superset-db` services to prevent them from being exposed to the public internet.

## 2. Application Security (Superset)

- [ ] **Change Default Credentials**: Immediately change the default `admin` user's password.
- [ ] **Generate New Secret Key**: Generate a new, strong `SUPERSET_SECRET_KEY` and set it in your `.env` file. Do not use the default key from the example file.
- [ ] **Authentication**: For production use, integrate Superset with a robust authentication backend like LDAP or OAuth.
- [ ] **Review `superset_config.py`**: Carefully review all settings in `superset/config/superset_config.py`, especially those related to security. Disable any features that are not needed.
- [ ] **Content Security Policy (CSP)**: Configure a strict Content Security Policy in your reverse proxy to mitigate XSS and other injection attacks.

## 3. Database Security

- [ ] **Strong Passwords**: Use strong, unique passwords for the `postgres` and `superset-db` databases. Set these in your `.env` file.
- [ ] **Principle of Least Privilege**: Ensure that the database users for the Superset and migration services have only the permissions they need.
- [ ] **Backups**: Regularly back up both the business data and Superset metadata databases.

## 4. Host Environment Security

- [ ] **Keep System Updated**: Regularly update the host operating system and all installed packages.
- [ ] **Docker Security**: Follow Docker's security best practices. Keep Docker Engine and Docker Compose up-to-date.
- [ ] **Limit User Access**: Limit access to the host machine to only authorized personnel. Use SSH keys for authentication instead of passwords.
- [ ] **File Permissions**: Ensure that the `.env` file and other sensitive configuration files have strict file permissions (e.g., `600`).
- [ ] **Monitoring and Logging**: Configure system-level monitoring and logging to detect and respond to suspicious activity.

## 5. Regular Maintenance

- [ ] **Security Scans**: Regularly scan the application and its dependencies for vulnerabilities.
- [ ] **Review Logs**: Regularly review application and system logs for signs of an attack.
- [ ] **Update Superset**: Keep the Superset instance and its dependencies up-to-date with the latest security patches.
