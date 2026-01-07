# Incident Response Plan

> Security incident response procedures for FormaSup BI Platform according to ISO 27001 (A.16) and RGPD Article 33-34.

---

## 1. Incident Classification

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **P1 - Critical** | Data breach, system compromise | Immediate (< 1h) | Ransomware, data exfiltration |
| **P2 - High** | Service outage, unauthorized access attempt | < 4h | DDoS, brute force attack |
| **P3 - Medium** | Security misconfiguration, vulnerability | < 24h | Exposed credentials, CVE |
| **P4 - Low** | Policy violation, minor issues | < 72h | Weak password, unused account |

---

## 2. Incident Response Team

| Role | Responsibility | Contact |
|------|----------------|---------|
| **Incident Manager** | Coordination, communication | IT Manager |
| **Security Analyst** | Investigation, containment | Marie Challet |
| **System Admin** | Technical remediation | IT Team |
| **DPO** | RGPD compliance, CNIL notification | Data Protection Officer |
| **Management** | Decision authority, resources | Direction |

---

## 3. Response Phases

### Phase 1: Detection and Reporting

1. Identify the incident (monitoring, user report, alert)
2. Document initial observations
3. Notify Incident Manager immediately for P1/P2
4. Create incident ticket with timestamp

### Phase 2: Containment

**Immediate Actions (P1/P2)**:

```bash
# Isolate affected container
docker stop superset-fsa

# Block suspicious IP (if applicable)
iptables -A INPUT -s <IP> -j DROP

# Preserve logs before any changes
docker logs superset-fsa > /backup/incident_logs_$(date +%Y%m%d).txt
```

**Short-term Containment**:

- Disable compromised accounts
- Revoke exposed credentials
- Segment network if needed

### Phase 3: Investigation

- Collect and preserve evidence
- Analyze logs (Superset, PostgreSQL, system)
- Determine root cause
- Identify affected data and users

**Log Locations**:

| Component | Log Location |
|-----------|--------------|
| Superset | `docker logs superset-fsa` |
| PostgreSQL | `/var/lib/postgresql/data/log/` |
| Nginx | `/var/log/nginx/access.log` |
| System | `/var/log/syslog` |

### Phase 4: Eradication

- Remove malware/unauthorized access
- Patch vulnerabilities
- Reset compromised credentials
- Update security configurations

### Phase 5: Recovery

1. Restore from clean backup if needed
2. Verify system integrity
3. Monitor for recurrence
4. Gradual service restoration

### Phase 6: Post-Incident

- Complete incident report
- Lessons learned meeting
- Update security controls
- Update this procedure if needed

---

## 4. RGPD Breach Notification

### CNIL Notification (Article 33)

**Deadline**: 72 hours after becoming aware of breach

**Required Information**:

- Nature of the breach
- Categories and number of data subjects affected
- Categories and number of records affected
- Contact details of DPO
- Likely consequences
- Measures taken or proposed

**Template**: Use CNIL online notification form

### Data Subject Notification (Article 34)

Required when breach is likely to result in high risk to rights and freedoms.

**Content**:

- Clear description of breach
- Contact details of DPO
- Likely consequences
- Measures taken to address breach

---

## 5. Evidence Preservation

### Chain of Custody

1. Document who collected evidence and when
2. Store evidence in read-only format
3. Calculate and record hash values
4. Maintain access log for evidence

### Evidence Checklist

- [ ] Container logs
- [ ] Database query logs
- [ ] Network traffic captures
- [ ] System logs
- [ ] Screenshots of anomalies
- [ ] Timeline of events

---

## 6. Communication Plan

| Audience | When | Who Communicates | Channel |
|----------|------|------------------|---------|
| IT Team | Immediately | Incident Manager | Teams/Phone |
| Management | Within 2h (P1/P2) | Incident Manager | Email/Meeting |
| DPO | If personal data involved | Security Analyst | Email |
| CNIL | Within 72h (if breach) | DPO | Official form |
| Users | After containment | Management | Email |

---

## 7. References

- ISO 27001:2022 - A.16 Information security incident management
- RGPD - Articles 33, 34
- ANSSI - Incident Response Guidelines

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
