# Catalogue CVE du sim Rapid7 et règles de cohérence (v1.4)

Référence pour choisir des CVE dans `hero_pinning` (`config/business-corp-config.yaml`). Seules les CVE présentes dans `VULN_CATALOG_SEED` du sim Rapid7 (`simulator/generators/vulnerabilities.py`) peuvent être épinglées.

⚠️ **Cyberwatch retiré en v1** : seul le catalogue Rapid7 est documenté ici.

## Cohérence CVE / asset (v1.4)

Depuis la v1.4, le sim n'attribue plus les CVE au hasard parmi tout le catalogue : chaque asset ne reçoit que des CVE **applicables à son OS et à ses logiciels**. Avant, 72 % des paires (asset, CVE) remontées dans XSIAM étaient incohérentes (Exchange sur un Mac, Cisco IOS XE sur une Debian, BlueKeep sur Windows 10…).

Mécanique :

- **Plateforme** déduite de l'OS : `windows-client` (+ `office`, `browser`), `windows-server`, `macos` (+ `browser`), `ios`, `linux`, `panos`
- **Rôles** logiciels déclarés par hostname :
  - natifs : `ASSET_ROLES` dans `simulator/generators/assets.py` du sim (ex. `srv-mail` = `exchange`, `srv-ad-01` = `domain-controller`, `srv-ci` = `java` + `teamcity`) ;
  - assets ajoutés : `extra_assets[].roles` dans le YAML ;
  - surcharge des natifs : `asset_roles` dans le YAML.
- **Surcharge d'OS** : `os_overrides` dans le YAML (ex. `srv-vpn` → `PAN-OS 10.2`, valeur à choisir parmi `EXTRA_OS` du sim).
- Chaque CVE déclare dans `CVE_REQUIREMENTS` les combinaisons de tags qu'elle exige. Le tirage (déterministe) ne pioche que dans les CVE compatibles.

Une CVE **épinglée** est toujours ajoutée, même sur un asset incompatible (choix explicite) : préférer une CVE compatible.

Volume attendu : ~115 findings sur 22 assets (contre ~230 avant, dont la majorité incohérents). Les serveurs Linux génériques portent peu de CVE de ce catalogue, ce qui est réaliste.

## Catalogue (49 CVE)

KEV : indicatif (statut CISA à la date de rédaction). Les valeurs EPSS / KEV réellement utilisées sont enrichies par Cortex Vulnerability Intelligence après ingestion. Colonne « assets compatibles » calculée sur le parc Business Corp patché (assets ajoutés et `os_overrides` inclus).

| CVE | Titre | CVSS | KEV | Exige (OU entre alternatives) | Assets compatibles (parc Business Corp) |
|-----|-------|------|-----|-------------------------------|------------------------------------------|
| CVE-2021-44228 | Apache Log4j Remote Code Execution (Log4Shell) | 10.0 | ✅ | `java` | srv-web-01, srv-ci, cloud-app-01, srv-portail |
| CVE-2024-3400 | Palo Alto Networks PAN-OS Command Injection | 10.0 | ✅ | `panos` | srv-vpn |
| CVE-2024-1709 | ConnectWise ScreenConnect Authentication Bypass | 10.0 | ✅ | `screenconnect` | *aucun (orpheline)* |
| CVE-2023-46604 | Apache ActiveMQ Remote Code Execution | 10.0 | ✅ | `activemq` | cloud-app-01 |
| CVE-2023-4966 | Citrix NetScaler ADC Buffer Overflow (CitrixBleed) | 9.4 | ✅ | `citrix` | *aucun (orpheline)* |
| CVE-2023-36884 | Windows Search Remote Code Execution | 8.8 | ✅ | `office+windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2023-23397 | Microsoft Outlook Elevation of Privilege | 9.8 | ✅ | `office+windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2023-38831 | RARLAB WinRAR Code Execution | 7.8 | ✅ | `windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2023-20198 | Cisco IOS XE Web UI Privilege Escalation | 10.0 | ✅ | `cisco-ios` | *aucun (orpheline)* |
| CVE-2023-34362 | Progress MOVEit Transfer SQL Injection | 9.8 | ✅ | `moveit` | *aucun (orpheline)* |
| CVE-2022-30190 | Microsoft Diagnostic Tool (Follina) Remote Code Execution | 7.8 | ✅ | `windows-client OU windows-server` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID, srv-web-01, srv-mail, srv-ad-01, srv-fs-01, srv-adfs-01, srv-print |
| CVE-2022-22965 | Spring Framework Remote Code Execution (Spring4Shell) | 9.8 | ✅ | `java+web` | srv-web-01 |
| CVE-2022-26134 | Atlassian Confluence Server OGNL Injection | 9.8 | ✅ | `confluence` | *aucun (orpheline)* |
| CVE-2021-34527 | Windows Print Spooler RCE (PrintNightmare) | 8.8 | ✅ | `windows-client OU windows-server` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID, srv-web-01, srv-mail, srv-ad-01, srv-fs-01, srv-adfs-01, srv-print |
| CVE-2021-26855 | Microsoft Exchange Server RCE (ProxyLogon) | 9.8 | ✅ | `exchange` | srv-mail |
| CVE-2020-1472 | Netlogon Elevation of Privilege (Zerologon) | 10.0 | ✅ | `domain-controller` | srv-ad-01 |
| CVE-2019-19781 | Citrix ADC Directory Traversal | 9.8 | ✅ | `citrix` | *aucun (orpheline)* |
| CVE-2019-0708 | Windows Remote Desktop RCE (BlueKeep) | 9.8 | ✅ | `windows-legacy` | *aucun (orpheline)* |
| CVE-2017-0144 | Windows SMB RCE (EternalBlue) | 8.1 | ✅ | `windows-legacy` | *aucun (orpheline)* |
| CVE-2024-6387 | OpenSSH regreSSHion Signal Handler Race Condition | 8.1 | — | `linux` | srv-web-02, srv-db-01, srv-db-02, srv-monitoring, srv-ci, cloud-lb-01, cloud-app-01, srv-portail, smtp-relay |
| CVE-2024-38063 | Windows TCP/IP Remote Code Execution | 9.8 | — | `windows-client OU windows-server` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID, srv-web-01, srv-mail, srv-ad-01, srv-fs-01, srv-adfs-01, srv-print |
| CVE-2023-50164 | Apache Struts Path Traversal | 9.8 | ✅ | `java+web` | srv-web-01 |
| CVE-2024-27198 | JetBrains TeamCity Authentication Bypass | 9.8 | ✅ | `teamcity` | srv-ci |
| CVE-2024-23917 | JetBrains TeamCity Authentication Bypass | 9.8 | — | `teamcity` | srv-ci |
| CVE-2023-6875 | POST SMTP Mailer WordPress Plugin Authentication Bypass | 9.8 | — | `php+web` | srv-web-02 |
| CVE-2024-21762 | Fortinet FortiOS Out-of-Bounds Write | 9.6 | ✅ | `fortios` | *aucun (orpheline)* |
| CVE-2023-42917 | Apple WebKit Memory Corruption | 8.8 | ✅ | `macos OU ios` | BSNS-MAC-BOB, BSNS-MAC-EMMA, BSNS-MOB-FLORA |
| CVE-2016-3189 | bzip2recover Use-After-Free | 6.5 | — | `linux` | srv-web-02, srv-db-01, srv-db-02, srv-monitoring, srv-ci, cloud-lb-01, cloud-app-01, srv-portail, smtp-relay |
| CVE-2018-11776 | Apache Struts 2 RCE | 8.1 | ✅ | `java+web` | srv-web-01 |
| CVE-2022-1388 | F5 BIG-IP iControl REST Authentication Bypass | 9.8 | ✅ | `f5` | *aucun (orpheline)* |
| CVE-2023-46747 | F5 BIG-IP TMUI Authentication Bypass | 9.8 | ✅ | `f5` | *aucun (orpheline)* |
| CVE-2024-4577 | PHP CGI Argument Injection | 9.8 | ✅ | `php+windows-server` | *aucun (orpheline)* |
| CVE-2024-30078 | Windows Wi-Fi Driver Remote Code Execution | 8.8 | — | `windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2024-26169 | Windows Error Reporting Service Elevation of Privilege | 7.8 | ✅ | `windows-client OU windows-server` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID, srv-web-01, srv-mail, srv-ad-01, srv-fs-01, srv-adfs-01, srv-print |
| CVE-2023-24880 | Windows SmartScreen Security Feature Bypass | 5.4 | ✅ | `windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2022-41040 | Microsoft Exchange Server SSRF (ProxyNotShell) | 8.8 | ✅ | `exchange` | srv-mail |
| CVE-2022-41082 | Microsoft Exchange Server RCE (ProxyNotShell) | 8.8 | ✅ | `exchange` | srv-mail |
| CVE-2023-3519 | Citrix ADC & Gateway Unauthenticated RCE | 9.8 | ✅ | `citrix` | *aucun (orpheline)* |
| CVE-2024-0204 | Fortra GoAnywhere MFT Authentication Bypass | 9.8 | ✅ | `mft` | srv-portail |
| CVE-2024-21413 | Microsoft Outlook Remote Code Execution | 9.8 | ✅ | `office+windows-client` | BSNS-WIN-ALICE, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID |
| CVE-2024-0012 | Palo Alto Networks PAN-OS Management Interface Authentication Bypass | 9.3 | ✅ | `panos` | srv-vpn |
| CVE-2023-41064 | Apple ImageIO Buffer Overflow (BLASTPASS) | 7.8 | ✅ | `macos OU ios` | BSNS-MAC-BOB, BSNS-MAC-EMMA, BSNS-MOB-FLORA |
| CVE-2023-41993 | Apple WebKit Arbitrary Code Execution | 9.8 | ✅ | `macos OU ios` | BSNS-MAC-BOB, BSNS-MAC-EMMA, BSNS-MOB-FLORA |
| CVE-2024-23222 | Apple WebKit Type Confusion | 8.8 | ✅ | `macos OU ios` | BSNS-MAC-BOB, BSNS-MAC-EMMA, BSNS-MOB-FLORA |
| CVE-2023-4863 | Google Chrome libwebp Heap Buffer Overflow | 8.8 | ✅ | `browser` | BSNS-WIN-ALICE, BSNS-MAC-BOB, BSNS-WIN-CHARLIE, BSNS-WIN-DAVID, BSNS-MAC-EMMA |
| CVE-2023-4911 | GNU C Library Dynamic Loader Buffer Overflow (Looney Tunables) | 7.8 | ✅ | `linux` | srv-web-02, srv-db-01, srv-db-02, srv-monitoring, srv-ci, cloud-lb-01, cloud-app-01, srv-portail, smtp-relay |
| CVE-2024-10979 | PostgreSQL PL/Perl Environment Variable Manipulation | 8.8 | — | `postgresql` | srv-db-01, srv-db-02 |
| CVE-2021-43798 | Grafana Directory Traversal | 7.5 | — | `grafana` | srv-monitoring |
| CVE-2023-51764 | Postfix SMTP Smuggling | 5.3 | — | `smtp` | smtp-relay |


**CVE orphelines** : aucune machine du parc Business Corp n'a le produit concerné (Citrix, F5, FortiOS, Cisco IOS XE, Confluence, MOVEit, ScreenConnect, Windows ancien pour BlueKeep / EternalBlue). Elles restent au catalogue pour un futur asset : par exemple un `f5-waf-01` avec le rôle `f5` (le contrôle compensatoire lui-même vulnérable), en ajoutant si besoin une empreinte d'OS dans `EXTRA_OS`.

## Vérifier qu'une CVE existe dans le catalogue

```bash
grep -n "CVE-2024-3400" <sims>/Rapid7InsightVM-simul/simulator/generators/vulnerabilities.py
```

## Ajouter une CVE au catalogue

1. Ajouter un tuple dans `VULN_CATALOG_SEED` (`simulator/generators/vulnerabilities.py` du sim)
2. Déclarer son applicabilité dans `CVE_REQUIREMENTS` (sans entrée, la CVE n'est jamais tirée)
3. Commit + redeploy, puis épingler via le YAML si besoin
