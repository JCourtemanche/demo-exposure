# Inventaire des catalogues CVE des 2 sims

Référence rapide pour choisir des CVE dans `hero_pinning` du YAML — seules les CVE présentes dans `VULN_CATALOG_SEED` (Rapid7) ou `CVE_CATALOG_SEED` (Cyberwatch) peuvent être pinnées.

Les 2 sims partagent **majoritairement** le même catalogue (40 CVE réelles), mais quelques CVE peuvent être exclusives à l'un ou l'autre. En cas de doute, vérifier via `grep CVE-YYYY-NNNN <fork>/simulator/generators/{vulnerabilities.py,cves.py}`.

## Catalogue commun (présent dans les 2 sims — vérifié)

| CVE | Nom court | CVSS | KEV | Usage démo suggéré |
|-----|-----------|------|-----|---------------------|
| CVE-2021-44228 | Log4Shell (Apache Log4j) | 10.0 | ✅ | Hero 1 alt ou Hero 5 |
| CVE-2024-3400 | PAN-OS GlobalProtect | 10.0 | ✅ | **Hero 1 préféré** |
| CVE-2024-1709 | ScreenConnect | 10.0 | ✅ | Hero 1 alt |
| CVE-2023-46604 | Apache ActiveMQ RCE | 10.0 | ✅ | Hero 2 alt |
| CVE-2023-4966 | CitrixBleed | 9.4 | ✅ | Hero 1 alt |
| CVE-2023-36884 | Windows Search RCE | 7.5 | ✅ | Hero 4 alt |
| CVE-2023-23397 | Outlook Elevation of Privilege | 9.8 | ✅ | Hero 4 alt |
| CVE-2023-38831 | WinRAR | 7.8 | ✅ | Hero 4 alt |
| CVE-2023-20198 | Cisco IOS XE | 10.0 | ✅ | Hero 1 alt |
| CVE-2023-34362 | MOVEit Transfer | 9.8 | ✅ | Hero 2 alt |
| CVE-2022-30190 | **Follina** (MSDT RCE) | 7.8 | ✅ | **Hero 4 préféré** |
| CVE-2022-22965 | Spring4Shell | 9.8 | ✅ | Hero 4 alt / Hero 5 alt |
| CVE-2022-26134 | Confluence OGNL | 9.8 | ✅ | Hero 2 alt |
| CVE-2021-34527 | PrintNightmare | 8.8 | ✅ | Hero 3 alt (Windows) |
| CVE-2021-26855 | **ProxyLogon** (Exchange) | 9.8 | ✅ | **Hero 2 préféré** |
| CVE-2020-1472 | **Zerologon** (Netlogon) | 10.0 | ✅ | **Hero 3 (proxy)** |
| CVE-2019-19781 | Citrix ADC | 9.8 | ✅ | Hero 1 alt |
| CVE-2019-0708 | BlueKeep | 9.8 | ✅ | Hero 3 alt |
| CVE-2017-0144 | EternalBlue | 8.1 | ✅ | Hero 3 alt (Windows old) |
| CVE-2024-6387 | regreSSHion (OpenSSH) | 8.1 | — | Hero 4 alt |
| CVE-2024-38063 | Windows TCP/IP RCE | 9.8 | — | Hero 4 alt |
| CVE-2023-50164 | Struts path traversal | 9.8 | ✅ | Hero 2 alt |
| CVE-2024-27198 | TeamCity auth bypass | 9.8 | ✅ | Hero 1 alt |
| CVE-2024-23917 | TeamCity Server | 9.8 | — | — |
| CVE-2023-6875 | POST SMTP Mailer | 9.8 | — | — |
| CVE-2024-21762 | FortiOS SSL VPN | 9.6 | ✅ | Hero 1 alt (VPN) |
| CVE-2023-42917 | WebKit | 8.8 | ✅ | Hero 4 alt |
| CVE-2016-3189 | **bzip2 use-after-free** | 6.5 | — | **Hero 6 préféré** (modéré) |
| CVE-2018-11776 | Struts 2 namespace | 8.1 | — | Hero 5 alt |
| CVE-2022-1388 | F5 BIG-IP iControl REST | 9.8 | ✅ | Hero 1 alt (ironique — F5 lui-même vuln) |
| CVE-2023-46747 | F5 BIG-IP Config Utility | 9.8 | ✅ | Hero 1 alt |
| CVE-2024-4577 | PHP CGI arg injection | 9.8 | ✅ | Hero 2 alt |
| CVE-2024-30078 | Wi-Fi driver RCE | 8.8 | — | — |
| CVE-2024-26169 | Windows Error Reporting | 7.8 | ✅ | Hero 4 alt (EoP) |
| CVE-2023-24880 | SmartScreen bypass | 5.4 | ✅ | Hero 6 alt (modéré + KEV) |
| CVE-2022-41040 | ProxyNotShell part 1 | 8.8 | ✅ | Hero 2 alt |
| CVE-2022-41082 | ProxyNotShell part 2 | 8.8 | ✅ | Hero 2 alt |
| CVE-2023-3519 | Citrix ADC RCE | 9.8 | ✅ | Hero 1 alt |
| CVE-2024-0204 | GoAnywhere MFT | 9.8 | ✅ | Hero 2 alt (portail transfert) |
| CVE-2024-21413 | Outlook MonikerLink | 9.8 | — | Hero 4 alt |

## Champs disponibles par sim

### Rapid7 (`vulnerabilities.py`)

Fields : `id`, `title`, `description`, `severity`, `severityScore`, `cves`, `cvss` (v2 & v3), `riskScore`, `categories`, `exploits`, `malwareKits`, `pci` block, `denialOfService`.

**Note importante** : Rapid7 sim ne porte PAS de champ `epss` ni `kev` — ces valeurs seront **auto-enrichies par Cortex Vulnerability Intelligence** après ingestion. Pas besoin de les avoir dans le sim.

### Cyberwatch (`cves.py`)

Fields : `cve_code`, `content`, `level`, `score`, `score_v3`, `epss`, `exploit_code_maturity`, `exploitable`, `technologies`, `cvss`, `cvss_v3`, `cwe`, `published`, `last_modified`.

**Cyberwatch porte l'EPSS natif** — utile pour Hero 4 (EPSS Follina). Le KEV n'est pas natif mais Cortex l'ajoute post-ingestion.

## Vérifier qu'une CVE existe dans un catalogue

```powershell
cd C:\Users\jcourtemanch\Documents\dev\demo\sims\Rapid7InsightVM-simul
Select-String -Path simulator\generators\vulnerabilities.py -Pattern "CVE-2024-3400"

cd ..\cyberwatch-simul
Select-String -Path simulator\generators\cves.py -Pattern "CVE-2024-3400"
```

## Ajouter une CVE au catalogue (si vraiment nécessaire)

Non recommandé pour la démo v1 — le catalogue de 40 CVE couvre toutes les hero cases documentées.

Si besoin de forcer une CVE absente (ex : CVE-2024-XXXXX du mois) :
1. Ouvrir `simulator/generators/vulnerabilities.py` (Rapid7) ou `cves.py` (Cyberwatch)
2. Ajouter un tuple au `VULN_CATALOG_SEED` / `CVE_CATALOG_SEED` en respectant la structure
3. Commit + redeploy
4. Pinner via le YAML

Ce cas de figure est documenté comme roadmap v3 (script mensuel d'update CVE actualité).
