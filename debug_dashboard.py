# --- PRÉPARATION DU TEXTE CONDENSÉ POUR SAUVER DES TOKENS ---
condensed_report = ""
for inc in incidents:
    condensed_report += f"- TITRE: {inc['preview']}\n"
    if inc['country']: condensed_report += f"  CIBLES: {inc['country']} / {inc['companies']}\n"
    condensed_report += f"  RÉSUMÉ: {inc['overview']}\n\n"
# --- 1. L'EXECUTIVE BRIEF (Généré par l'IA) ---
with st.spinner("🧠 AI is drafting the Executive Summary (Context Reduced)..."):
    auth_ctx = init_llm_auth()
    # On envoie le texte condensé (condensed_report) au lieu du contenu brut (content) !
    brief, raw_ai = generate_executive_brief(condensed_report, auth_ctx)
