# CIS Benchmark Assessment — Palo Alto PAN-OS Firewall
*How to run a CIS Benchmark assessment on Palo Alto Networks next-generation firewalls (NGFW)*

> **Research snapshot: 22 Oct 2026.** The recommendation list below comes from the automated audit
> content for **CIS Palo Alto Firewall 11 Benchmark v1.2.0** (as mirrored by Tenable). Download the
> official PDF from CIS before a real engagement: it has the audit and remediation steps for every item.

## TL;DR
- **Use CIS Palo Alto Firewall 11 Benchmark v1.2.0** (released Nov 2025). It has **79 recommendations in 8 sections**: 69 Level 1 and 10 Level 2.
- **There is no PAN-OS 12 benchmark yet**, even though PAN-OS 12.1 and 12.2 are the current releases. For 12.x firewalls, assess against the PAN-OS 11 benchmark and record that as a documented deviation.
- The **PAN-OS 10 benchmark is final (v1.3.0, Sep 2025)** because PAN-OS 10.2 reached end of life in Aug 2025. Running 10.x is itself a finding.
- **Tooling:**
  - **CIS-CAT Pro** works offline from an exported XML config. It needs a CIS SecureSuite membership and supports v1.1.0 of the PAN-OS 11 benchmark (not v1.2.0 yet).
  - **Tenable Nessus** scans the firewall live over its XML API and already has v1.2.0 audit files.
  - **Palo Alto's own BPA** (Best Practice Assessment) is free, but it maps to the CIS *Controls*, not the CIS *Benchmark*.
- **Avoid two sources:** the `PaloAltoNetworks/cis-benchmarks` skillet (PAN-OS 9 only, unmaintained) and third-party summary sites whose item numbers don't match CIS.

## Threat Model
- **Threat**: A misconfigured perimeter firewall: management exposed to untrusted networks, weak admin authentication, allow rules without threat inspection, traffic that isn't logged, stale threat content.
- **Impact**: Firewall takeover (PAN-OS management-plane CVEs are actively exploited), malware and C2 traffic passing uninspected, no forensic trail, failed audits.
- **Severity**: High. The firewall is the control point for everything behind it.

## Use Case
- Security hardening reviews and baseline audits of PAN-OS firewalls (hardware, VM-Series, CN-Series)
- Compliance evidence where CIS Benchmarks are named or accepted (PCI DSS 2.2 "industry-accepted hardening standards", ISO 27001 A.8.9, SOC 2 CC6/CC7, NIS2, regional regulator baselines)
- Pre- and post-change validation after upgrades or Panorama template changes

## Which Benchmark to Use

| CIS Benchmark | Version | Status | CIS-CAT Pro content | Tenable audit files |
|---|---|---|---|---|
| **Palo Alto Firewall 11** | **1.2.0** (Nov 2025) | **Current** | 1.1.0 only | 1.2.0 L1 / L2 (updated 22 Dec 2025) |
| Palo Alto Firewall 10 | 1.3.0 FINAL (Sep 2025) | Final, no further updates | 1.3.0 | 1.3.0 L1 / L2 (updated 10 Feb 2026) |
| Palo Alto Firewall 6–9 | various | Archived / unsupported | n/a | deprecated |

**No CIS Benchmark exists for:** PAN-OS 12.x, Panorama, Prisma Access, or GlobalProtect as a separate product. GlobalProtect and IPsec items are folded into the firewall benchmark (1.6.3, 1.7.1).

### Map PAN-OS version → benchmark

| PAN-OS | Support status (Oct 2026) | Benchmark to use |
|---|---|---|
| 12.2 | Supported until 30 Jul 2029 | PAN-OS 11 v1.2.0 (closest; document as deviation) |
| 12.1 | Supported until 28 Aug 2028 | PAN-OS 11 v1.2.0 (closest; document as deviation) |
| 11.2 | Supported until 2 May 2027 | **PAN-OS 11 v1.2.0** |
| 11.1 | Supported until 3 May 2027 | **PAN-OS 11 v1.2.0** |
| 11.0 | End of life (Nov 2024) | PAN-OS 11 v1.2.0 + finding: unsupported OS |
| 10.2 and older | End of life | PAN-OS 10 v1.3.0 + finding: unsupported OS |

> Both 11.x branches reach end of life in **May 2027**. Most fleets will move to 12.x during the next
> audit cycle, so check CIS WorkBench for a PAN-OS 12 benchmark draft before each engagement.

## Profile Levels
- **Level 1 (L1)**: Essential settings for every deployment, with low operational impact.
- **Level 2 (L2)**: Defense in depth for high-security environments. These items may need extra subscriptions, PKI or infrastructure. The L2 profile includes all L1 items.

## Recommendation Checklist (79 items)

IDs and titles are CIS's own wording. The **Notes** column is assessor guidance added here, not CIS text.
Abbreviations used in Notes:
- **Ext** means the evidence lives outside the firewall (Active Directory, a server, or a process).
- **If…** means the item only applies when that feature is in use. Otherwise mark it N/A with a reason.
- **Sub:** names the subscription the item probably needs. Confirm against `request license info`.

### 1 — Device Setup (26)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 1.1.1.1 | Syslog logging should be configured | L1 | |
| 1.1.1.2 | SNMPv3 traps should be configured | L2 | |
| 1.1.2 | Ensure 'Login Banner' is set | L1 | Wording often needs legal/HR sign-off |
| 1.1.3 | Ensure 'Enable Log on High DP Load' is enabled | L1 | |
| 1.2.1 | Ensure 'Permitted IP Addresses' is set to those necessary for device management | L1 | ⚠️ Lockout risk: confirm your own source IP first |
| 1.2.2 | Ensure 'Permitted IP Addresses' is set for all management profiles where SSH, HTTPS, or SNMP is enabled | L1 | Check every interface mgmt profile |
| 1.2.3 | Ensure HTTP and Telnet options are disabled for the management interface | L1 | |
| 1.2.4 | Ensure HTTP and Telnet options are disabled for all management profiles | L1 | |
| 1.2.5 | Ensure valid certificate is set for browser-based administrator interface | L2 | Needs internal PKI |
| 1.3.1 | Ensure 'Minimum Password Complexity' is enabled | L1 | Local admins only |
| 1.3.2 | Ensure 'Minimum Length' is greater than or equal to 12 | L1 | |
| 1.3.3 | Ensure 'Minimum Uppercase Letters' is greater than or equal to 1 | L1 | |
| 1.3.4 | Ensure 'Minimum Lowercase Letters' is greater than or equal to 1 | L1 | |
| 1.3.5 | Ensure 'Minimum Numeric Letters' is greater than or equal to 1 | L1 | |
| 1.3.6 | Ensure 'Minimum Special Characters' is greater than or equal to 1 | L1 | |
| 1.3.7 | Ensure 'Required Password Change Period' is less than or equal to 90 days | L1 | May conflict with NIST 800-63B; record as exception if policy differs |
| 1.3.8 | Ensure 'New Password Differs By Characters' is greater than or equal to 3 | L1 | |
| 1.3.9 | Ensure 'Prevent Password Reuse Limit' is set to 24 or more passwords | L1 | |
| 1.3.10 | Ensure 'Password Profiles' do not exist | L1 | Profiles override the global complexity settings |
| 1.4.1 | Ensure 'Idle timeout' is less than or equal to 10 minutes for device management | L1 | |
| 1.4.2 | Ensure 'Failed Attempts' and 'Lockout Time' for Authentication Profile are properly configured | L1 | |
| 1.5.1 | Ensure 'V3' is selected for SNMP polling | L1 | If SNMP is used |
| 1.6.1 | Ensure 'Verify Update Server Identity' is enabled | L1 | |
| 1.6.2 | Ensure redundant NTP servers are configured appropriately | L1 | |
| 1.6.3 | Ensure that the Certificate Securing Remote Access VPNs is Valid | L2 | If GlobalProtect |
| 1.7.1 | Enabling Post-Quantum (PQ) on IKEv2 VPNs | L2 | If IKEv2 site-to-site VPNs; check that the peer supports it |

### 2 — User Identification (8)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 2.1 | Ensure that IP addresses are mapped to usernames | L2 | |
| 2.2 | Ensure that WMI probing is disabled | L2 | |
| 2.3 | Ensure that User-ID is only enabled for internal trusted interfaces | L1 | If User-ID; check the zone settings |
| 2.4 | Ensure that 'Include/Exclude Networks' is used if User-ID is enabled | L1 | If User-ID |
| 2.5 | Ensure that the User-ID Agent has minimal permissions if User-ID is enabled | L1 | Ext: AD group membership of the service account |
| 2.6 | Ensure that the User-ID service account does not have interactive logon rights | L1 | Ext: AD GPO / user rights assignment |
| 2.7 | Ensure remote access capabilities for the User-ID service account are forbidden. | L1 | Ext: AD / RDP / VPN groups |
| 2.8 | Ensure that security policies restrict User-ID Agent traffic from crossing into untrusted zones | L1 | |

### 3 — High Availability (3)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 3.1 | Ensure a fully-synchronized High Availability peer is configured | L1 | A standalone firewall fails this; record a risk acceptance if HA isn't planned |
| 3.2 | Ensure 'High Availability' requires Link Monitoring and/or Path Monitoring | L1 | |
| 3.3 | Ensure 'Passive Link State' and 'Preemptive' are configured appropriately | L1 | |

### 4 — Dynamic Updates (2)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 4.1 | Ensure 'Antivirus Update Schedule' is set to download and install updates hourly | L1 | Sub: Threat Prevention |
| 4.2 | Ensure 'Applications and Threats Update Schedule' is set to download and install updates at daily or shorter intervals | L1 | Use a threshold delay to limit risk from a bad content update |

### 5 — WildFire (8)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 5.1 | Ensure that WildFire file size upload limits are maximized | L1 | Sub: WildFire |
| 5.2 | Ensure a WildFire Analysis profile is enabled for all security policies | L1 | |
| 5.3 | Ensure forwarding of decrypted content to WildFire is enabled | L1 | |
| 5.4 | Ensure all WildFire session information settings are enabled | L1 | |
| 5.5 | Ensure alerts are enabled for malicious files detected by WildFire | L1 | |
| 5.6 | Ensure 'WildFire Update Schedule' is set to download and install updates in real-time | L1 | |
| 5.7 | Choosing Wildfire public cloud region | L2 | Data-residency decision; document the chosen region |
| 5.8 | Ensure that 'Inline Cloud Analysis' on Wildfire profiles is enabled | L1 | Sub: Advanced WildFire |

### 6 — Security Profiles (25)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 6.1 | Ensure that antivirus profiles are set to reset-both on all decoders except 'imap' and 'pop3' | L1 | Sub: Threat Prevention |
| 6.2 | Ensure a secure antivirus profile is applied to all relevant security policies | L1 | Check profile *groups* too |
| 6.3 | Ensure an anti-spyware profile is configured to block on all spyware severity levels, categories, and threats | L1 | |
| 6.4 | Ensure DNS sinkholing is configured on all anti-spyware profiles in use | L1 | |
| 6.5 | Ensure a secure anti-spyware profile is applied to all security policies permitting traffic to the Internet | L1 | |
| 6.6 | Ensure a Vulnerability Protection Profile is set to block attacks against critical and high vulnerabilities, and set to default on medium, low, and informational vulnerabilities | L1 | |
| 6.7 | Ensure a secure Vulnerability Protection Profile is applied to all security rules allowing traffic | L1 | |
| 6.8 | Ensure that PAN-DB URL Filtering is used | L1 | Sub: (Advanced) URL Filtering |
| 6.9 | Ensure that URL Filtering uses the action of 'block' or 'override' on the URL categories | L1 | The PDF lists the exact categories |
| 6.10 | Ensure that access to every URL is logged | L1 | Log volume impact |
| 6.11 | Ensure all HTTP Header Logging options are enabled | L1 | |
| 6.12 | Ensure secure URL filtering is enabled for all security policies allowing traffic to the Internet | L1 | |
| 6.13 | Ensure alerting after a threshold of credit card or Social Security numbers is detected is enabled | L1 | Data Filtering; adapt patterns to local IDs (e.g. national ID numbers) |
| 6.14 | Ensure a secure Data Filtering profile is applied to all security policies allowing traffic to or from the Internet | L1 | |
| 6.15 | Ensure that a Zone Protection Profile with an enabled SYN Flood Action of SYN Cookies is attached to all untrusted zones | L1 | |
| 6.16 | Ensure that a Zone Protection Profile with tuned Flood Protection settings enabled for all flood types is attached to all untrusted zones | L2 | ⚠️ Tune thresholds from measured baseline first or you'll drop legit traffic |
| 6.17 | Ensure that all zones have Zone Protection Profiles with all Reconnaissance Protection settings enabled, tuned, and set to appropriate actions | L1 | Exclude your own vuln scanners |
| 6.18 | Ensure all zones have Zone Protection Profiles that drop specially crafted packets | L1 | |
| 6.19 | Ensure that User Credential Submission uses the action of 'block' or 'continue' on the URL categories | L1 | Needs User-ID / credential detection set up |
| 6.20 | Ensure that 'Wildfire Inline ML Action' on antivirus profiles are set to reset-both on all decoders except 'imap' and 'pop3' | L1 | Sub: WildFire / Advanced WildFire |
| 6.21 | Ensure that 'Wildfire Inline ML' on antivirus profiles are set to enable for all file types | L1 | |
| 6.22 | Ensure that 'Inline Cloud Analysis' on Vulnerability Protection profiles are enabled if 'Advanced Threat Prevention' is available | L1 | If Advanced Threat Prevention |
| 6.23 | Ensure that 'Cloud Inline Categorization' on URL Filtering profiles are enabled if 'Advanced Threat Prevention' is available | L1 | Conditional on subscription |
| 6.24 | Ensure that 'Inline Cloud Analysis' on Anti-Spyware profiles are enabled if 'Advanced Threat Prevention' is available | L1 | If Advanced Threat Prevention |
| 6.25 | Ensure that 'DNS Policies' is configured on Anti-Spyware profiles if 'DNS Security' license is available | L1 | If DNS Security |

### 7 — Security Policies (4)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 7.1 | Ensure application security policies exist when allowing traffic from an untrusted zone to a more trusted zone | L2 | App-ID not just ports on inbound rules |
| 7.2 | Ensure 'Service setting of ANY' in a security policy allowing traffic does not exist | L1 | Use `application-default` |
| 7.3 | Ensure 'Security Policy' denying any/all traffic to/from IP addresses on Trusted Threat Intelligence Sources Exists | L1 | Built-in Palo Alto EDLs (known-malicious / bulletproof IPs) |
| 7.4 | Ensure that logging is enabled on built-in default security policies | L1 | Override `intrazone-default` / `interzone-default` |

### 8 — Decryption (3)

| ID | Recommendation | Lvl | Notes |
|---|---|---|---|
| 8.1 | Ensure 'SSL Forward Proxy Policy' for traffic destined to the Internet is configured | L1 | ⚠️ Privacy/legal review; exempt cert-pinned apps, finance, health |
| 8.2 | Ensure 'SSL Inbound Inspection' is required for all untrusted traffic destined for servers using SSL or TLS | L1 | If you publish TLS services; needs the server keys |
| 8.3 | Ensure that the Certificate used for Decryption is Trusted | L2 | Enterprise CA pushed to endpoints |

### Subscriptions that change the scope
Unlicensed features usually make the related items **fail** rather than N/A. Agree how to treat them before you start.

| Subscription | Items affected |
|---|---|
| Threat Prevention / Advanced TP | 4.1, 4.2, 6.1–6.7, 6.22, 6.24, 7.3 |
| (Advanced) URL Filtering | 6.8–6.12, 6.19, 6.23 |
| WildFire / Advanced WildFire | 5.1–5.8, 6.20, 6.21 |
| DNS Security | 6.25 |

## Assessment Tools

| Tool | How it reads the firewall | Benchmark content | Cost | Verdict |
|---|---|---|---|---|
| **CIS-CAT Pro Assessor v4** | **Offline**: reads an exported config XML (`panos` session type) | 11 v1.1.0, 10 v1.3.0 | CIS SecureSuite membership | Official CIS scoring, but lags the newest benchmark |
| **Tenable Nessus / Security Center / Tenable VM** | **Live** over the PAN-OS XML API (HTTPS) with a *Superuser (read-only)* admin; plugins 64095 + 64286 | 11 v1.2.0 L1/L2, 10 v1.3.0 | Nessus Professional or higher | Most current automated content |
| **Palo Alto BPA** (Strata Cloud Manager → Insights → Posture → Best Practices) | Telemetry or an uploaded tech-support file (TSF) | PAN best practices mapped to **CIS Controls**, *not* the CIS Benchmark | Core features free | Good complement and remediation guide, not a CIS Benchmark result |
| `PaloAltoNetworks/cis-benchmarks` skillet | Panhandler + API | PAN-OS 9 only | Free | ❌ Unmaintained, so don't use |
| Manual review | Benchmark PDF + config XML + screenshots | Any version | Time | Still required for the Ext items (2.5–2.7) and judgement calls |

**Other baselines to know:** DISA STIGs for Palo Alto (NDM / ALG / IDPS) are common in government work. Palo Alto's own "Best Practices" documentation goes beyond the CIS Benchmark.

## Implementation: Running the Assessment

### 1. Scope and inventory
For each firewall, record:
- Model, serial, PAN-OS version, and whether it's in an HA pair
- Whether it uses multiple virtual systems (multi-vsys)
- Whether it's managed by Panorama (and which template stack / device group)
- Active subscriptions
- Features in use: GlobalProtect, IPsec, User-ID, decryption

```
show system info              # model, serial, sw-version, multi-vsys
request license info          # active subscriptions → decides N/A vs Fail
show high-availability all    # HA mode, peer state, link/path monitoring
show ntp                      # NTP sync status (1.6.2)
```

### 2. Pick the benchmark and profile
- L1 for every firewall
- L2 where policy requires it (regulated, crown-jewel segments)
- Write the version into the report, e.g. "CIS Palo Alto Firewall 11 Benchmark v1.2.0, Level 1". Item IDs changed between versions, so always cite the version.

### 3. Collect evidence (read-only)
- Create a dedicated **Superuser (read-only)** admin or an API key bound to a read-only role. Remove it after the assessment.
- **Export the config XML.** Panorama-managed firewalls are the most common trap: the local `running-config.xml` does **not** contain the Panorama-pushed policy and templates. Assess the **merged** view, or checks fail falsely.

```
# CLI: Panorama-managed firewall (local + pushed config)
set cli config-output-format xml
show config merged

# CLI: standalone firewall
show config running
```
- Collect AD evidence for 2.5–2.7: group membership and user-rights assignment for the User-ID service account.
- Take screenshots for manual items and keep them with timestamps.

### 4. Run the tool(s)
- **CIS-CAT Pro:** point a `panos` session at the exported XML file.
- **Nessus:** create a Policy Compliance scan, add PAN-OS credentials, and select the matching `CIS_Palo_Alto_Firewall_11_Benchmark_v1.2.0_L1/L2` audit.
- With no tool, work through the checklist above using the PDF's "Audit" section for each item.

### 5. Validate results
Common false positives:
- Panorama-pushed objects that the tool can't see
- Multi-vsys firewalls where only `vsys1` was evaluated
- Deny rules flagged for using `any`
- Profile *groups* applied to rules instead of individual profiles
- Features that are licensed but deliberately unused (e.g. no GlobalProtect means 1.6.3 is N/A)

### 6. Score and report
For each item, record **Pass / Fail / N/A / Exception** with evidence and a justification. Report:
- % compliance per section and overall, split by L1 and L2
- Top risks first: management exposure (1.2.x), allow rules without threat profiles (6.2/6.5/6.7/5.2), logging (1.1.1.1, 6.10, 7.4)

### 7. Remediate and re-test
Fix in Panorama templates and device groups where possible, not locally on the firewall, or the fix gets overwritten.

**High-risk changes (stage them):**
- 1.2.1 Permitted IPs: lockout risk
- 6.16 Flood thresholds: can drop legitimate traffic if untuned
- 8.1 / 8.2 Decryption: needs privacy/legal review, and can break apps
- 3.3 Preemption: can cause failover flapping

## Validation Rules
- **Permitted IPs (1.2.1/1.2.2)**: No `0.0.0.0/0` and no `any`. Every entry maps to a named admin network or jump host.
- **Threat profiles on allow rules (5.2, 6.2, 6.5, 6.7, 6.12, 6.14)**: Every rule with `action allow` has a profile or profile group attached.
- **Service ANY (7.2)**: No allow rule has `service any`. Use `application-default` or explicit services.
- **Default-rule logging (7.4)**: `intrazone-default` and `interzone-default` are overridden with log-at-session-end.
- **Content updates (4.1, 4.2, 5.6)**: Schedules are set to *download-and-install*, not download-only.

## Testing

### Pre-engagement Checklist
- [ ] PAN-OS version of every firewall known and mapped to a benchmark version
- [ ] Benchmark PDF downloaded from CIS (free for non-commercial use)
- [ ] Profile agreed (L1 / L1+L2) and N/A rules for unlicensed features agreed
- [ ] Read-only admin / API key created and approved
- [ ] Panorama-managed? Plan to collect the **merged** config
- [ ] AD owner lined up for the User-ID evidence (2.5–2.7)
- [ ] Change window booked for remediation and re-test

### Quick Wins (low risk, high value)
- [ ] Disable HTTP and Telnet on the management interface and all profiles (1.2.3, 1.2.4)
- [ ] Set the idle timeout to 10 minutes or less (1.4.1) and lockout on the auth profile (1.4.2)
- [ ] Enable 'Verify Update Server Identity' (1.6.1)
- [ ] Set content updates to download-and-install (4.1, 4.2, 5.6)
- [ ] Enable logging on the default intrazone/interzone rules (7.4)
- [ ] Add a deny rule for Palo Alto's built-in malicious-IP EDLs (7.3)

## Logging & Monitoring
- Forward system, config, traffic, threat, URL and WildFire logs to the SIEM (1.1.1.1). Alert on config commits outside change windows.
- Alert on WildFire *malicious* verdicts (5.5) and on DNS sinkhole hits (6.4). A sinkhole hit means an infected host.
- Re-run the assessment after every PAN-OS upgrade, Panorama template change, and new CIS benchmark release.

## Watch-outs
- **Benchmark naming is confusing.** "Palo Alto Firewall 10" and "11" refer to the PAN-OS major version, and each has its own v1.x.x document version. Always write both.
- **Third-party summaries:** some sites publish "CIS PAN-OS" pages with invented numbering (e.g. 1.1.1 = strong passwords). Use only CIS PDFs or the CIS/Tenable audit content for IDs.
- **CIS-CAT lag:** CIS-CAT Pro content for PAN-OS 11 is v1.1.0 while the benchmark is v1.2.0. Note the difference in the report or use Tenable for v1.2.0.
- **Benchmark ≠ best practice:** passing CIS doesn't mean the rulebase is good. CIS checks settings, not whether rules are least-privilege. Pair it with a rulebase review: unused rules, shadowed rules, and broad allow rules.

## Sources
- CIS Palo Alto Networks Benchmarks page (versions, CIS-CAT content): https://www.cisecurity.org/benchmark/palo_alto_networks
- CIS Benchmarks Update Nov 2025 (PAN-OS 11 v1.2.0 release): https://www.cisecurity.org/insights/blog/cis-benchmarks-update-november-2025
- CIS Benchmarks Update Sep 2025 (PAN-OS 10 v1.3.0 FINAL): https://www.cisecurity.org/insights/blog/cis-benchmarks-september-2025-update
- Tenable audit: CIS Palo Alto Firewall 11 v1.2.0 L1: https://www.tenable.com/audits/CIS_Palo_Alto_Firewall_11_Benchmark_v1.2.0_L1
- Tenable audit: CIS Palo Alto Firewall 11 v1.2.0 L2: https://www.tenable.com/audits/CIS_Palo_Alto_Firewall_11_Benchmark_v1.2.0_L2
- Tenable audit: CIS Palo Alto Firewall 10 v1.3.0 L1: https://www.tenable.com/audits/CIS_Palo_Alto_Firewall_10_Benchmark_v1.3.0_L1
- CIS-CAT Pro Assessor v4 Coverage Guide (PAN-OS = offline only): https://ciscat-assessor.docs.cisecurity.org/en/latest/Coverage%20Guide/
- CIS-CAT Pro Configuration Guide (`panos` session, XML config): https://github.com/CISecurity/CCPA-Docs/blob/master/docs/Configuration%20Guide.md
- Tenable PAN-OS compliance file reference (XML API, Superuser read-only): https://docs.tenable.com/nessus/compliance-checks-reference/Content/PaloAltoFirewallConfigurationAuditComplianceFileReference.htm
- Palo Alto Strata Cloud Manager Best Practices dashboard: https://docs.paloaltonetworks.com/strata-cloud-manager/getting-started/dashboards/best-practices
- PAN-OS support dates: https://endoflife.date/panos
- Deprecated Palo Alto CIS skillet (PAN-OS 9): https://github.com/PaloAltoNetworks/cis-benchmarks

## Projects Using This
- *(Add engagements here after use)*

---
*Documented: 22 October 2026*
*Based on CIS Palo Alto Firewall 11 Benchmark v1.2.0 (audit content) and public vendor/tool documentation*
