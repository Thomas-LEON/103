Voici les dernières avancées concernant l'affaire DGFiP suite à la conférence de presse d'hier et aux annonces officielles. J'ai retiré les balises de la veille et intégré les nouveaux éléments de ce matin (19 août 2026) avec la balise **[NEW UPDATE]** pour que tu puisses identifier les changements immédiatement.

---

Dear all,

Please find an update on the data breach affecting the Direction Générale des Finances Publiques (DGFiP), France.

**What happened?**

* A day after DGFiP officially confirmed a data breach where a threat actor claims to hold approximately 678,000 rows of data affecting around 393,000 individuals. The same threat actor, "ZeroBytes", has claimed a second cyberattack on DGFiP on August 14, 2026.
* This new breach targets the Professional Cadastral Data Server (SPDC), which is an online application fully integrated into the DGFiP (Direction générale des Finances publiques) information system. It functions as a specialized gateway that bridges the DGFiP's core land-registry databases with authorized external professionals like notaries and land surveyors.
* Both targeted portals are hosted on the same DGFiP internal sub-network (IP block 145.242.11.0/24).
* The intrusion allegedly took place on July 29, 2026, targeting the Professional Cadastral Data Server (SPDC).
* The threat actors assert they compromised the system using a valid account credential while successfully bypassing Multi-Factor Authentication (MFA) controls.
* In response, the Minister of Public Accounts has publicly admitted to an accumulated "technical debt" across the state's IT infrastructure and announced the immediate, mandatory rollout of two-factor authentication (2FA) for all agents and external partners.
* On August 15, 2026, the Paris public prosecutor's office (Parquet de Paris) officially opened a criminal investigation. Concurrently, trade unions, notably Solidaires Finances Publiques, publicly revealed they had warned the administration about these exact security risks as early as June, strongly condemning the delayed public communication.
* Internal union pressure intensified as CGT Finances Publiques publicly denounced severe underfunding and the loss of over 34,000 positions since 2008, arguing that structural budget reductions have degraded the state's ability to maintain and secure critical IT infrastructure.
* **[NEW UPDATE]** During the government's official press conference on August 18, 2026, Minister of Public Accounts David Amiel issued a public apology regarding the massive data breaches, stating the situation is "unbearable for the French people".
* **[NEW UPDATE]** DGFiP Director General Amélie Verdier admitted the discovery of a third, distinct data breach identified on Monday, August 17, 2026. The new intrusion targeted a public portal dedicated to inheritance and succession data ("portail des successions"), and the unauthorized access was quickly terminated.
* **[NEW UPDATE]** Verdier also provided further details on the primary June attack, confirming that threat actors initially infiltrated the system by compromising the access credentials of a "reputedly secure external agent".

**What is the impact?**

* The threat actors claim to have exfiltrated 252,149 database lines from the SPDC server, currently listed for sale. They released a demonstration sample of 1,092 records.
* ZeroBytes advertises that 2,041,778 property owners are exposed. However, this figure is likely inflated by significant duplication, as a single individual is recorded multiple times if they own several distinct land parcels.
* The breach maps civil identities directly to precise real estate assets, including full names, birth dates and places, physical addresses, and exact property holdings (municipality, parcel number, etc.).
* The impact to BNPP is not yet known. We are in contact with 1LoD who is monitoring the situation.
* Recent analyses and official ministry acknowledgments confirmed that the earlier tax breach exposed highly sensitive indicators, including the reference tax income and withholding tax rates, which threat actors are now crossing with the cadastral data.
* The correlation of cadastral ownership with previously exposed fiscal data elevates the risk of targeted identity theft, document forgery, and real estate-related social engineering. This has triggered immediate alarm within the fintech and cryptocurrency communities, with industry leaders highlighting severe risks of physical extortion and financial fraud.
* Data privacy and compliance experts are raising legal scrutiny regarding potential GDPR Article 33 non-compliance, questioning the seven-week delay between internal incident detection in late June and regulatory notification in mid-August.
* **[NEW UPDATE]** Regarding the third breach, authorities stated it is much less severe than the previous incidents. The compromised inheritance data relates to historical search logs used by creditors to locate heirs, which Verdier compared to widely accessible "public legal notices".
* **[NEW UPDATE]** The DGFiP began individually notifying the estimated 350,000 affected taxpayers on August 17 via email and physical mail, a process expected to conclude by the end of the week.

**What is being done & next steps**

* As of now, the DGFiP has not issued an official confirmation regarding this specific intrusion into the SPDC, despite yesterday's press release acknowledging the previous incident. However, the Ministry of Economy has recently conceded that "cadastral data" (such as addresses and property surfaces) was indeed consulted during the identified illegitimate accesses.
* The DGFiP has officially confirmed it referred the incident to the French Data Protection Authority (CNIL) and will file a formal legal complaint. The judicial investigation is currently being led by the National Anti-Cybercrime Office (Ofac).
* The Ministry of Economy and Finance held an official press conference on August 18, 2026, at 16:00 CET, where Minister David Amiel delivered the government's official response and remediation plan.
* Group CSIRT has opened a ticket for more information with their intelligence provider which includes open source and dark web intelligence.
* RISK ORM is actively monitoring the situation with CSIRT and will provide updates as details emerge following the official announcements.
* **[NEW UPDATE]** As part of the remediation plan announced during the press conference, Minister Amiel unveiled a new cybersecurity action plan. Key measures include enforcing 2FA for all agents by year-end, intensifying internal anti-phishing campaigns, launching a bug bounty program, and utilizing "sovereign AI" in partnership with French startup Mistral AI to simulate attacks and identify vulnerabilities.

**Sources & references**

* **[NEW UPDATE]** Imaz Press Réunion (Aug 18, 2026): "Fisc piraté : le gouvernement présente ses excuses, une 'troisième fuite' repérée et 'coupée'" – imazpress.com
* **[NEW UPDATE]** Anadolu Ajansı (Aug 18, 2026): "France / Cyberattaque de la DGFiP : Amiel présente ses excuses et annonce un durcissement de la cybersécurité de l'État" – aa.com.tr
* **[NEW UPDATE]** KultureGeek (Aug 18, 2026): "Après le piratage des impôts, le gouvernement dévoile un plan pour renforcer la cybersécurité" – kulturegeek.fr
* **[NEW UPDATE]** Club Patrimoine (Aug 19, 2026): "Piratage du fisc : fuite sur les successions, quelles précautions pour les contribuables ?" – clubpatrimoine.com
* Ministère de l'Économie et des Finances (Press Advisory, Aug 18, 2026): "Invitation presse - Point d'étape sur la réponse à la cyberattaque DGFiP par David Amiel" – presse.economie.gouv.fr
* CGT Finances Publiques (Aug 18, 2026): "Déclaration sur les failles de sécurité et les moyens alloués à la DGFiP" – cgtfinancespubliques.fr
* Aladom (Aug 17, 2026): "Piratage des impôts : 678 000 Français concernés..." – aladom.fr
* Solidaires Finances Publiques (Aug 14, 2026): "Cyberattaque à la DGFiP : Solidaires Finances Publiques avait alerté sur les risques dès juin" – solidairesfinancespubliques.org
* Cryptoast (Aug 16, 2026): "Compromissions à la DGFiP : « Cela arrive plusieurs fois par semaine »" – cryptoast.fr
* MeilleureSCPI (Aug 15, 2026): "Piratage DGFiP 2026 : ce que la fuite de données fiscales va générer" – meilleurescpi.com
* LégiFiscal (Aug 17, 2026): "Cyberattaque contre la DGFiP : 678.000 usagers potentiellement concernés" – legifiscal.fr
* Cyberattaque.org (Aug 14, 2026): "DGFiP : une 2ème cyberattaque revendiquée, plus de 2 millions de personnes concernées" – cyberattaque.org
* Ministère de l'Économie et des Finances (Press Release, Aug 13, 2026): "Accès illégitime au système d'information de la Direction générale des Finances publiques" – presse.economie.gouv.fr
* France Épargne (Aug 14, 2026): "Piratage DGFiP : 678 438 lignes fiscales revendiquées" – france-epargne.fr
* SeniorActu (Aug 13, 2026): "Piratage du site des impôts : vos revenus et votre adresse en font peut-être partie" – senioractu.com
* Boursorama (Aug 14, 2026): "Impôts : le site impots.gouv piraté, les données fiscales de près de 700.000 contribuables dans la nature" – boursorama.com
* Fuites Infos (Aug 12, 2026): "678 438 lignes revendiquées chez DGFiP, fuite revendiquée" – fuitesinfos.fr

Kind Regards,
