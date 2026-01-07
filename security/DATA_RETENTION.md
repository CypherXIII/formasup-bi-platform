# Data Retention Policy

> Data retention and deletion procedures for FormaSup BI Platform according to RGPD Article 5 (storage limitation) and ISO 27001.

---

## 1. Retention Principles

- **Purpose Limitation**: Data kept only as long as necessary for stated purpose
- **Storage Limitation**: No indefinite retention of personal data
- **Documented Justification**: Retention periods based on legal or business need
- **Secure Deletion**: Data destroyed securely when retention period expires

---

## 2. Retention Schedule

### Business Data (PostgreSQL)

| Data Category | Retention Period | Legal Basis | Deletion Method |
|---------------|------------------|-------------|-----------------|
| **Apprentice personal data** | 5 years after contract end | Labour Code L3243-4 | Anonymization or deletion |
| **Training contracts** | 10 years | Commercial Code L123-22 | Secure deletion |
| **Company data (SIRET)** | Indefinite | Public data | N/A |
| **Contact information** | Duration of relationship + 3 years | Legitimate interest | Secure deletion |
| **Financial data** | 10 years | Tax Code | Secure deletion |

### Superset Data

| Data Category | Retention Period | Justification | Deletion Method |
|---------------|------------------|---------------|-----------------|
| **User accounts** | Account lifetime + 1 year | Audit trail | Anonymization |
| **Query history** | 1 year | Troubleshooting | Automatic purge |
| **Dashboard definitions** | Indefinite | Business continuity | Manual deletion |
| **Access logs** | 1 year | Security audit | Automatic purge |
| **Session data** | 24 hours | Technical necessity | Automatic expiry |

### System Logs

| Log Type | Retention Period | Justification |
|----------|------------------|---------------|
| Application logs | 90 days | Troubleshooting |
| Security logs | 1 year | Incident investigation |
| Audit logs | 5 years | Compliance |
| Backup logs | 1 year | Recovery verification |

---

## 3. Deletion Procedures

### Automatic Deletion

Configure scheduled jobs for automatic data purge:

```sql
-- Example: Purge query history older than 1 year
DELETE FROM query_history 
WHERE executed_at < NOW() - INTERVAL '1 year';

-- Example: Anonymize old apprentice records
UPDATE apprentis 
SET 
    nom = 'ANONYMIZED',
    prenom = 'ANONYMIZED',
    email = NULL,
    telephone = NULL
WHERE date_fin_contrat < NOW() - INTERVAL '5 years';
```

### Manual Deletion (Data Subject Request)

1. Verify identity of requester
2. Locate all personal data across systems
3. Execute deletion/anonymization
4. Document the action
5. Confirm to data subject within 30 days

### Secure Deletion Standards

| Data Type | Method | Verification |
|-----------|--------|--------------|
| Database records | DELETE + VACUUM | Query confirmation |
| Files | Secure wipe (shred) | File system check |
| Backups | Encrypted, then delete | Backup inventory |
| Logs | Overwrite | Log rotation confirmation |

---

## 4. Backup Retention

| Backup Type | Retention | Storage Location |
|-------------|-----------|------------------|
| Daily incremental | 7 days | Local encrypted storage |
| Weekly full | 4 weeks | Local + offsite |
| Monthly archive | 12 months | Offsite encrypted |
| Annual archive | 7 years | Cold storage |

### Backup Deletion Process

When source data expires, corresponding backups must also be:
1. Identified in backup inventory
2. Scheduled for deletion when backup expires
3. Verified as deleted
4. Documented

---

## 5. Data Subject Rights Implementation

### Right to Erasure (Article 17)

**Process**:
1. Receive and log request
2. Verify identity
3. Check for legal retention requirements
4. Execute deletion or document exception
5. Respond within 30 days

**Exceptions** (data may be retained):
- Legal obligation (tax, labour law)
- Public interest archiving
- Legal claims defense

### Right to Portability (Article 20)

**Export Format**: CSV or JSON
**Scope**: Data provided by the data subject
**Timeline**: 30 days

---

## 6. Annual Review

- [ ] Review retention periods against current regulations
- [ ] Verify automatic deletion jobs are functioning
- [ ] Audit data older than retention period
- [ ] Update retention schedule if needed
- [ ] Document review results

---

## 7. References

- RGPD - Article 5(1)(e) Storage Limitation
- RGPD - Article 17 Right to Erasure
- French Labour Code - L3243-4
- French Commercial Code - L123-22
- CNIL Guidelines on Data Retention

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
