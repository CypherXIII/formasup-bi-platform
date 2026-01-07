# Data Classification Policy

> Classification of data processed by FormaSup BI Platform according to ISO 27001 (A.8.2) and RGPD requirements.

---

## 1. Classification Levels

| Level | Label | Description | Examples |
|-------|-------|-------------|----------|
| **C4** | Highly Confidential | Personal data requiring special protection | Student health data, disciplinary records |
| **C3** | Confidential | Personal data subject to RGPD | Names, emails, SIRET, apprentice contracts |
| **C2** | Internal | Business data not for public disclosure | Statistics, internal reports, configurations |
| **C1** | Public | Data intended for public access | Published dashboards, anonymized statistics |

---

## 2. Data Inventory

### Business Database (PostgreSQL)

| Table | Classification | RGPD Category | Retention |
|-------|---------------|---------------|-----------|
| `apprentis` | C3 - Confidential | Personal data | 5 years after contract end |
| `entreprises` | C2 - Internal | Business data | Indefinite |
| `contrats` | C3 - Confidential | Personal data | 10 years |
| `formations` | C2 - Internal | Business data | Indefinite |
| `statistiques` | C1 - Public | Anonymized | Indefinite |

### Superset Metadata Database

| Data Type | Classification | Description |
|-----------|---------------|-------------|
| User credentials | C4 - Highly Confidential | Hashed passwords, session tokens |
| Dashboard definitions | C2 - Internal | Chart and dashboard configurations |
| Query history | C3 - Confidential | May contain personal data references |
| Access logs | C2 - Internal | User activity logs |

---

## 3. Handling Requirements

### C4 - Highly Confidential

- Encryption at rest required
- Access limited to authorized personnel only
- Audit logging mandatory
- No export without approval

### C3 - Confidential (RGPD Personal Data)

- Encryption in transit (HTTPS)
- Access control via Superset RBAC
- Data subject rights must be respected
- Retention periods enforced

### C2 - Internal

- Standard access controls
- No public exposure
- Backup and recovery procedures

### C1 - Public

- May be shared externally
- No special handling required

---

## 4. RGPD Data Subject Rights

The system must support:

| Right | Implementation |
|-------|----------------|
| Right of access (Art. 15) | SQL queries to extract individual data |
| Right to rectification (Art. 16) | Database update procedures |
| Right to erasure (Art. 17) | Deletion scripts with cascade handling |
| Right to portability (Art. 20) | Export to CSV/JSON format |

---

## 5. References

- ISO 27001:2022 - A.8.2 Information classification
- RGPD - Articles 5, 9, 17, 30
- CNIL Guidelines for educational institutions

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
