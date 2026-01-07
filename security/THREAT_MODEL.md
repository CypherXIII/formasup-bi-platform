# Threat Model

This document outlines the threat model for the FormaSup BI Platform, based on the STRIDE methodology.

## 1. System Overview

The system consists of the following components:

- **Superset Service**: The main web application for data visualization.
- **PostgreSQL (Business Data)**: The primary data warehouse.
- **PostgreSQL (Superset Metadata)**: The database for Superset's internal state.
- **Migration Service**: A batch job for migrating data from MariaDB to PostgreSQL.
- **Nginx Reverse Proxy**: The entry point for all web traffic (in production).
- **End Users**: Data analysts, administrators.

### Trust Boundaries

- **Internet to Reverse Proxy**: Untrusted
- **Reverse Proxy to Superset Service**: Trusted network
- **Superset Service to Databases**: Trusted network
- **Migration Service to Databases**: Trusted network

## 2. STRIDE Threat Analysis

### Superset Service

| Threat Category         | Threat Scenario                                                                | Mitigation                                                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Spoofing**            | An attacker impersonates a legitimate user.                                    | Superset's built-in authentication and session management. For production, integrate with a robust authentication provider (LDAP, OAuth). |
| **Tampering**           | An attacker modifies data in transit between the user and the server.            | Use of HTTPS (enforced by the reverse proxy in production).                                                                             |
| **Repudiation**         | A user denies performing an action (e.g., deleting a dashboard).                 | Superset's action logs record user activity.                                                                                            |
| **Information Disclosure** | An attacker gains access to sensitive data or configuration.                  | Role-Based Access Control (RBAC) in Superset. No hardcoded secrets; all secrets are managed via environment variables.                  |
| **Denial of Service**   | An attacker floods the service with expensive queries or requests.             | Rate limiting can be implemented in the reverse proxy. Resource limits can be set on the Docker container.                               |
| **Elevation of Privilege** | A user gains access to data or functionality they are not authorized for.     | Superset's RBAC model. Regular security audits of Superset.                                                                             |

### PostgreSQL Databases

| Threat Category         | Threat Scenario                                                                | Mitigation                                                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Spoofing**            | An unauthorized service connects to the database.                              | Strong, unique passwords for each database, managed via environment variables. Network isolation via Docker networks.                   |
| **Tampering**           | An attacker modifies data directly in the database.                            | Access to the database is restricted to the Superset and Migration services within the Docker network.                                  |
| **Repudiation**         | A user denies making a change to the data.                                     | Database-level logging can be enabled if required.                                                                                      |
| **Information Disclosure** | An attacker gains access to the entire database.                              | Restricted access and strong passwords.                                                                                                 |
| **Denial of Service**   | An attacker runs a query that consumes all database resources.                 | Connection pooling and resource limits can be configured.                                                                               |
| **Elevation of Privilege** | A user with limited database access gains full control.                        | The application connects with a user that has the minimum required privileges.                                                          |

### Migration Service

| Threat Category         | Threat Scenario                                                                | Mitigation                                                                                                                              |
| ----------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Spoofing**            | An attacker provides malicious database credentials.                           | Credentials are provided via a secure `.env` file, which should be protected by filesystem permissions.                                 |
| **Tampering**           | An attacker modifies data during the migration process.                        | The migration service runs in a trusted environment.                                                                                    |
| **Information Disclosure** | An attacker intercepts database credentials.                                  | Use of environment variables, not hardcoded secrets.                                                                                    |
| **Denial of Service**   | The migration script consumes all resources on the source or target database.  | The script includes performance-limiting features like batching and query limits.                                                       |

## 3. Security Assumptions

- The host environment (the server running Docker) is secure.
- The `.env` file is properly secured and not accessible to unauthorized users.
- In production, the application is deployed behind a properly configured reverse proxy with HTTPS.
- Superset and its dependencies are kept up-to-date with the latest security patches.
