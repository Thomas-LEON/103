One day after the DGFiP publicly acknowledged an unauthorized intrusion affecting 678,438 tax records, the threat actor known as "ZeroBytes" claimed a second breach targeting the Professional Cadastral Data Server (SPDC). This claimed compromise involves land and property ownership records, sparking significant concern across the financial and technology sectors regarding the systemic vulnerability of state infrastructure.

### What Happened?

* **The Claim:** On **August 14, 2026**, the entity known as **"ZeroBytes"** publicly claimed a second data breach against the French Directorate General of Public Finance (DGFiP).
* **The Target:** The intrusion reportedly occurred on **July 29, 2026**, against the **Professional Cadastral Data Server (SPDC)** hosted on the domain `apexappliext.dgfip.finances.gouv.fr`.
* **The Stated Attack Vector:** The threat actors stated that access was gained using **valid account credentials** while **bypassing Multi-Factor Authentication (MFA)** controls. **[NEW UPDATE]** In response, the Minister of Public Accounts has publicly admitted to an accumulated "technical debt" across the state's IT infrastructure and announced the immediate, mandatory rollout of two-factor authentication (2FA) for all agents and external partners.

### Context: Infrastructure & Timeline

* **Shared Infrastructure:** Both targeted platforms (`impots.gouv.fr` and the SPDC) are hosted on the **same DGFiP internal sub-network** (IP block `145.242.11.0/24`, ASN 34177).
* **Timeline of Events:** Following the initial tax portal intrusion detected in **late June 2026**, the DGFiP managed the incident internally. The claimed **second intrusion occurred on July 29**. Public disclosure occurred on August 12 when the threat actor posted the tax dataset for sale, followed by the DGFiP's official acknowledgment on August 13 and the second cadastral claim on August 14.
* **[NEW UPDATE] Escalation & Criticism:** On August 15, 2026, the Paris public prosecutor's office (*Parquet de Paris*) officially opened a criminal investigation. Concurrently, trade unions, notably *Solidaires Finances Publiques*, publicly revealed they had warned the administration about these exact security risks as early as June, strongly condemning the delayed public communication.

### What is the Impact?

* **Data Volume:** The threat actor claims to hold **252,149 database rows**, currently listed for sale, and published an unverified **sample of 1,092 records** as proof of access.
* **Scope of Records:** The listing advertises **2,041,778 property owner records**. This figure reflects multiple entries per individual across separate land parcels rather than distinct citizens.
* **Compromised Data Fields:** The extracted dataset maps civil identities to specific real estate assets:
* **Civil identity:** Full names (including maiden names) and gender.
* **Birth records:** Date and place of birth.
* **Contact details:** Physical addresses of rights holders.
* **Real estate holdings:** Department, municipality, cadastral section, parcel identifier, and the nature of property rights.
* **[UPDATED FACT - Corrected from review:]** Recent analyses and official ministry acknowledgments confirmed that the earlier tax breach exposed highly sensitive indicators, including the reference tax income and withholding tax rates, which threat actors are now crossing with the cadastral data.


* **Risk Profile:** Correlation of cadastral ownership with previously exposed fiscal data facilitates targeted identity theft, document forgery, and real estate-related social engineering. This has triggered immediate alarm within the fintech and cryptocurrency communities. Industry leaders are publicly highlighting the severe risks of physical extortion and financial fraud, with some calling for a moratorium on state data collection until security protocols are reinforced.

### What is Being Done?

* **Administrative Status:** The DGFiP has not issued a formal confirmation regarding the claimed breach of the SPDC server. However, the Ministry of Economy has recently conceded that "cadastral data" (such as addresses and property surfaces) was indeed consulted during the identified illegitimate accesses.
* **Third-Party Assessment:** External security researchers and specialized media have reviewed the 1,092-line sample, noting that its structure matches legitimate SPDC data exports.
* **[NEW UPDATE] Legal & Regulatory Action:** The DGFiP has officially confirmed it referred the incident to the French Data Protection Authority (CNIL) and will file a formal legal complaint. The judicial investigation is currently being led by the National Anti-Cybercrime Office (Ofac).
* **Monitoring:** Analysts are tracking the distribution of the files and monitoring the threat actor's assertion of ongoing system access.

### Next Steps

* **Anticipated Official Acknowledgment:** The DGFiP is expected to complete its technical evaluation of the SPDC platform and issue a formal statement regarding the validity and perimeter of the claim.
* **Regulatory Filings:** Direct advisories to identified rights holders are anticipated as the exact exfiltration scope is finalized by Ofac investigators.
* **Banking Risk Considerations:** The combination of cadastral records and fiscal indicators elevates the risk of credit application fraud and account takeover attempts.
* **Internal Oversight:** Financial institutions should urgently review fraud detection rules and verification procedures across mortgage, consumer credit, and customer onboarding channels.

---

### Sources & References

* **[NEW UPDATE] Aladom (Aug 17, 2026):** "Piratage des impôts : 678 000 Français concernés..." – [aladom.fr](https://www.aladom.fr/actualites/secteur-service/11265/piratage-des-impots-678-000-francais-concernes-par-le-vol-de-donnees-a-la-dgfip-ce-quil-faut-savoir/)
* **[NEW UPDATE] Solidaires Finances Publiques (Aug 14, 2026):** "Cyberattaque à la DGFiP : Solidaires Finances Publiques avait alerté sur les risques dès juin" – [solidairesfinancespubliques.org](https://solidairesfinancespubliques.org/vie-des-services/particulier/7541-cyberattaque-a-la-dgfip-solidaires-finances-publiques-avait-alerte-sur-les-risques-des-juin.html)
* **Cryptoast (Aug 16, 2026):** "Compromissions à la DGFiP : « Cela arrive plusieurs fois par semaine »" – cryptoast.fr
* **MeilleureSCPI (Aug 15, 2026):** "Piratage DGFiP 2026 : ce que la fuite de données fiscales va générer" – meilleurescpi.com
* **LégiFiscal (Aug 17, 2026):** "Cyberattaque contre la DGFiP : 678.000 usagers potentiellement concernés" – legifiscal.fr
* **Cyberattaque.org (Aug 14, 2026):** "DGFiP : une 2ème cyberattaque revendiquée, plus de 2 millions de personnes concernées" – cyberattaque.org
* **Ministère de l'Économie et des Finances (Press Release, Aug 13, 2026):** "Accès illégitime au système d'information de la Direction générale des Finances publiques" – presse.economie.gouv.fr
* **France Épargne (Aug 14, 2026):** "Piratage DGFiP : 678 438 lignes fiscales revendiquées" – france-epargne.fr
* **SeniorActu (Aug 13, 2026):** "Piratage du site des impôts : vos revenus et votre adresse en font peut-être partie" – senioractu.com
* **Boursorama (Aug 14, 2026):** "Impôts : le site impots.gouv piraté, les données fiscales de près de 700.000 contribuables dans la nature" – boursorama.com
* **Fuites Infos (Aug 12, 2026):** "678 438 lignes revendiquées chez DGFiP, fuite revendiquée" – fuitesinfos.fr
* **Network Intelligence / BGP Routing Data:** Analysis of DGFiP subnet allocation (ASN 34177) for IPs 145.242.11.100 and 145.242.11.9.
