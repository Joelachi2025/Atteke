import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as streamlit_app

# --- 1. CONFIGURATION STRICTE DE LA PAGE (DOIT ÊTRE LA PREMIÈRE INSTRUCTION) ---
streamlit_app.set_page_config(page_title="Atteke - Gestion Coopérative", layout="wide", page_icon="📁")

# --- 2. CONFIGURATION DU STOCKAGE PHYSIQUE ---
DOSSIER_ARCHIVES = "archives_documents"
if not os.path.exists(DOSSIER_ARCHIVES):
    os.makedirs(DOSSIER_ARCHIVES)

# --- 3. COMPTES UTILISATEURS (IDENTIFIANTS ET ROLES) ---
COMPTES_VALIDES = {
    "admin": {"mp": "Admin2026", "role": "Administrateur"},
    "Responsable lutte contre le travail des enfants": {"mp": "Djane2026", "role": "Durabilité"},
    "Responsable productivité": {"mp": "Gueu2026", "role": "Durabilité"},
    "Responsable environnement": {"mp": "Mito2026", "role": "Durabilité"},
    "Responsable social": {"mp": "Zongo2026", "role": "Durabilité"},
    "Responsable Bonne gouvernance": {"mp": "Honore2026", "role": "Durabilité"},
}

CATEGORIES_DOCUMENTS = [
    "Factures & Reçus",
    "Procès-Verbaux (PV de réunions CA et AG)",
    "Contrats Exportateurs et SOCOOPACDI",
    "Documents de Certification (Fairtrade, Rainforest Alliance, etc.)",
    "Procès-Verbaux de formations et sensibilisations",
    "Politiques et Procédures internes",
    "Contrats & Adhésions Membres",
    "Rapports Financiers",
    "Courriers (Arrivés/Départs)",
    "Registres de Collecte / Pesée",
    "Autres documents"
]

# --- 4. INITIALISATION DE LA BASE DE DONNÉES ---
def initialiser_bdd_atteke():
    connexion = sqlite3.connect("atteke_archives.db")
    curseur = connexion.cursor()
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            categorie TEXT NOT NULL,
            description TEXT,
            nom_fichier TEXT NOT NULL,
            chemin_fichier TEXT NOT NULL,
            auteur_depot TEXT NOT NULL,
            role_auteur TEXT NOT NULL,
            date_depot TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    connexion.commit()
    connexion.close()

initialiser_bdd_atteke()

# --- 5. GESTION DE LA SESSION ---
if "auth" not in streamlit_app.session_state:
    streamlit_app.session_state["auth"] = False
if "user" not in streamlit_app.session_state:
    streamlit_app.session_state["user"] = ""
if "role" not in streamlit_app.session_state:
    streamlit_app.session_state["role"] = ""

# --- 6. ÉCRAN DE CONNEXION ---
if not streamlit_app.session_state["auth"]:
    # Structure centrée pour l'écran de login
    col_gauche, col_centre, col_droite = streamlit_app.columns([1, 2, 1])
    
    with col_centre:
        streamlit_app.markdown("<br><br>", unsafe_allow_html=True)
        streamlit_app.markdown("<h2 style='text-align: center;'>🔐 Connexion - Application Atteke</h2>", unsafe_allow_html=True)
        streamlit_app.markdown("<p style='text-align: center; color: gray;'>Système d'Archivage Numérique de la Coopérative</p>", unsafe_allow_html=True)
        
        with streamlit_app.form("form_login"):
            id_saisi = streamlit_app.text_input("Identifiant utilisateur")
            mp_saisi = streamlit_app.text_input("Mot de passe", type="password")
            soumettre = streamlit_app.form_submit_button("Se connecter", use_container_width=True)
            
            if soumettre:
                if id_saisi in COMPTES_VALIDES and COMPTES_VALIDES[id_saisi]["mp"] == mp_saisi:
                    streamlit_app.session_state["auth"] = True
                    streamlit_app.session_state["user"] = id_saisi
                    streamlit_app.session_state["role"] = COMPTES_VALIDES[id_saisi]["role"]
                    streamlit_app.rerun()
                else:
                    streamlit_app.error("Identifiant ou mot de passe incorrect.")

# --- 7. APPLICATION PRINCIPALE (ACCÈS APPROUVÉ) ---
else:
    # Configuration de la barre latérale
    streamlit_app.sidebar.markdown(f"### 👤 Utilisateur : **{streamlit_app.session_state['user'].upper()}**")
    streamlit_app.sidebar.markdown(f"💼 Rôle : `{streamlit_app.session_state['role']}`")
    
    if streamlit_app.sidebar.button("🚪 Se déconnecter", use_container_width=True):
        streamlit_app.session_state["auth"] = False
        streamlit_app.session_state["user"] = ""
        streamlit_app.session_state["role"] = ""
        streamlit_app.rerun()
        
    streamlit_app.sidebar.markdown("---")
    
    menu = ["📊 Tableau de Bord", "🔍 Rechercher & Consulter", "📤 Archiver un Document"]
    choix = streamlit_app.sidebar.radio("Navigation principale", menu)
    
    nom_agent = streamlit_app.session_state["user"]
    role_agent = streamlit_app.session_state["role"]

    # --- 7.1. TABLEAU DE BORD ---
    if choix == "📊 Tableau de Bord":
        streamlit_app.title("📊 Tableau de Bord Analytique - Atteke")
        
        connexion = sqlite3.connect("atteke_archives.db")
        df_stats = pd.read_sql_query("SELECT id, categorie, auteur_depot, date_depot FROM documents", connexion)
        connexion.close()
        
        if df_stats.empty:
            streamlit_app.info("Le système ne contient aucun document pour le moment. Utilisez l'onglet 'Archiver' pour commencer.")
        else:
            total_docs = len(df_stats)
            categories_distinctes = df_stats["categorie"].nunique()
            derniere_activite = df_stats["date_depot"].max()
            
            kpi1, kpi2, kpi3 = streamlit_app.columns(3)
            with kpi1:
                streamlit_app.metric(label="📄 Total Documents Archivés", value=total_docs)
            with kpi2:
                streamlit_app.metric(label="🗂️ Catégories Actives", value=categories_distinctes)
            with kpi3:
                streamlit_app.metric(label="🕒 Dernière mise à jour", value=str(derniere_activite)[:16])
                
            streamlit_app.markdown("---")
            
            graphe_col1, graphe_col2 = streamlit_app.columns(2)
            
            with graphe_col1:
                streamlit_app.markdown("### 📁 Documents par Catégorie")
                df_cat = df_stats.groupby("categorie").size().reset_index(name="Nombre")
                fig_bar = px.bar(df_cat, x="categorie", y="Nombre", color="Nombre", labels={"categorie": "Catégorie", "Nombre": "Quantité"}, color_continuous_scale="Blues")
                streamlit_app.plotly_chart(fig_bar, use_container_width=True)
                
            with graphe_col2:
                streamlit_app.markdown("### 🧑‍💻 Contribution par Utilisateur")
                df_user = df_stats.groupby("auteur_depot").size().reset_index(name="Volume")
                fig_pie = px.pie(df_user, values="Volume", names="auteur_depot", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                streamlit_app.plotly_chart(fig_pie, use_container_width=True)

    # --- 7.2. MOTEUR DE RECHERCHE ---
    elif choix == "🔍 Rechercher & Consulter":
        streamlit_app.title("🔍 Recherche Avancée dans les Archives")
        
        c1, c2 = streamlit_app.columns(2)
        with c1:
            recherche = streamlit_app.text_input("Rechercher par mot-clé (Titre, notes...)")
        with c2:
            cat_filtre = streamlit_app.selectbox("Filtrer par catégorie", ["Toutes"] + CATEGORIES_DOCUMENTS)
            
        connexion = sqlite3.connect("atteke_archives.db")
        requete = "SELECT id, titre, categorie, description, nom_fichier, auteur_depot, role_auteur, date_depot FROM documents WHERE 1=1"
        params = []
        
        if recherche:
            requete += " AND (titre LIKE ? OR description LIKE ?)"
            params.extend([f"%{recherche}%", f"%{recherche}%"])
        if cat_filtre != "Toutes":
            requete += " AND categorie = ?"
            params.append(cat_filtre)
            
        requete += " ORDER BY date_depot DESC"
        df_docs = pd.read_sql_query(requete, connexion, params=params)
        connexion.close()
        
        if df_docs.empty:
            streamlit_app.info("Aucun document archivé ne correspond à ces critères.")
        else:
            streamlit_app.write(f"📁 **{len(df_docs)}** document(s) trouvé(s) :")
            
            for idx, ligne in df_docs.iterrows():
                with streamlit_app.expander(f"📄 [{ligne['categorie']}] {ligne['titre']} (Déposé par {ligne['auteur_depot']})"):
                    streamlit_app.write(f"**Description / Résumé :** {ligne['description']}")
                    streamlit_app.write(f"**Date exacte de numérisation :** {ligne['date_depot']}")
                    
                    chemin_reel = os.path.join(DOSSIER_ARCHIVES, f"{ligne['id']}_{ligne['nom_fichier']}")
                    if os.path.exists(chemin_reel):
                        with open(chemin_reel, "rb") as f:
                            data_f = f.read()
                        streamlit_app.download_button(
                            label="📥 Télécharger le document",
                            data=data_f,
                            file_name=ligne['nom_fichier'],
                            key=f"btn_{ligne['id']}"
                        )
                    else:
                        streamlit_app.error("Le fichier physique est introuvable sur le disque.")

    # --- 7.3. EXÉCUTION DE L'ARCHIVAGE ---
    elif choix == "📤 Archiver un Document":
        streamlit_app.title("📤 Numérisation et Indexation de document")
        
        with streamlit_app.form("form_depot", clear_on_submit=True):
            titre = streamlit_app.text_input("Titre officiel du document")
            cat = streamlit_app.selectbox("Type / Catégorie", CATEGORIES_DOCUMENTS)
            desc = streamlit_app.text_area("Notes, références ou détails à archiver")
            fichier = streamlit_app.file_uploader("Sélectionner le fichier", type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx"])
            
            bouton = streamlit_app.form_submit_button("Enregistrer l'archive")
            
            if bouton:
                if titre and fichier:
                    nom_original = fichier.name
                    
                    connexion = sqlite3.connect("atteke_archives.db")
                    curseur = connexion.cursor()
                    curseur.execute("""
                        INSERT INTO documents (titre, categorie, description, nom_fichier, chemin_fichier, auteur_depot, role_auteur)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        titre,
                        cat,
                        desc,
                        nom_original,
                        "",  # Chemin à remplir après l'insertion pour récupérer l'ID
                        nom_agent,
                        role_agent
                    ))
                    id_nouveau_doc = curseur.lastrowid
                    chemin_physique = os.path.join(DOSSIER_ARCHIVES, f"{id_nouveau_doc}_{nom_original}")
                    curseur.execute("UPDATE documents SET chemin_fichier = ? WHERE id = ?", (chemin_physique, id_nouveau_doc))
                    connexion.commit()
                    connexion.close()
                    
                    with open(chemin_physique, "wb") as f:
                        f.write(fichier.getbuffer())
                    
                    streamlit_app.success("Document archivé avec succès !")