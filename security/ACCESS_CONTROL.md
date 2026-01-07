# Access Control Policy

> Access control policy for FormaSup BI Platform according to ISO 27001 (A.9) requirements.

---

## 1. Access Control Principles

- **Least Privilege**: Users receive only the minimum permissions required
- **Separation of Duties**: Critical operations require multiple actors
- **Need-to-Know**: Access granted based on business need
- **Defense in Depth**: Multiple layers of access control

---

## 2. User Roles and Permissions

### Superset Roles

| Role | Permissions | Assigned To |
|------|-------------|-------------|
| **Admin** | Full system access, user management | IT Administrators |
| **Alpha** | Create/edit dashboards, SQL Lab access | Data Analysts |
| **Gamma** | View dashboards, limited data access | Business Users |
| **Public** | View public dashboards only | External partners |

### Database Roles

| Role | Database | Permissions |
|------|----------|-------------|
| `superset_app` | superset | CRUD on metadata tables |
| `superset_readonly` | business_data | SELECT only |
| `migration_user` | business_data | INSERT, UPDATE, DELETE (batch jobs) |
| `postgres` | all | Superuser (emergency only) |

---

## 3. Authentication Requirements

### Password Policy

| Requirement | Value |
|-------------|-------|
| Minimum length | 12 characters |
| Complexity | Uppercase, lowercase, number, special |
| Expiration | 90 days |
| History | Cannot reuse last 5 passwords |
| Lockout | 5 failed attempts = 15 min lockout |

### Multi-Factor Authentication (MFA)

- **Required for**: Admin role, SQL Lab access
- **Recommended for**: All users accessing personal data
- **Implementation**: TOTP via authenticator app

---

## 4. Network Access Control

### Docker Network Isolation

```text
Internet
    |
[Nginx Reverse Proxy] (port 443)
    |
[fsa-net Docker network]
    |
    +-- [Superset] (port 8088 internal)
    |
    +-- [PostgreSQL Business] (port 5432 internal)
    |
    +-- [PostgreSQL Superset] (port 5442 internal)
```

### Firewall Rules

| Source | Destination | Port | Action |
|--------|-------------|------|--------|
| Internet | Nginx | 443 | ALLOW |
| Internet | Nginx | 80 | REDIRECT to 443 |
| Nginx | Superset | 8088 | ALLOW |
| Superset | PostgreSQL | 5432, 5442 | ALLOW |
| Internet | PostgreSQL | * | DENY |

---

## 5. Access Review Process

### Quarterly Review

- [ ] Review all user accounts and roles
- [ ] Remove inactive accounts (> 90 days)
- [ ] Verify role assignments match job functions
- [ ] Update access matrix documentation

### Annual Audit

- [ ] Complete access rights audit
- [ ] Penetration testing of access controls
- [ ] Review and update this policy

---

## 6. Privileged Access Management

### Admin Account Controls

- Separate admin accounts from daily-use accounts
- Log all admin actions
- Require approval for privilege escalation
- Time-limited admin sessions

### Emergency Access

- Break-glass procedure for emergency access
- Dual authorization required
- Full audit trail
- Post-incident review mandatory

---

## 7. References

- ISO 27001:2022 - A.9 Access Control
- RGPD - Article 32 (Security of processing)
- ANSSI - Secure Administration Guidelines

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
