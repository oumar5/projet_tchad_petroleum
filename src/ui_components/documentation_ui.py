import streamlit as st
import os
from pathlib import Path

class DocumentationUI:
    """Composant UI pour afficher la documentation intégrée."""
    
    DOCS_PATH = Path("docs")
    
    DOCUMENTATION_MENU = {
        "📖 Guide Utilisateur": "user-guide.md",
        "🏗️ Architecture": "architecture.md", 
        "🤖 Modèles Prédictifs": "prediction-models.md",
        "📊 Interface UI": "user-interface.md",
        "👨‍💻 Développement": "development.md",
        "🚀 Déploiement": "deployment.md",
        "📥 Collecte Données": "data-collection.md",
        "🧹 Nettoyage Données": "data-cleaning.md"
    }
    
    @staticmethod
    def render():
        """Affiche l'interface de documentation."""
        st.title("📚 Documentation Tchad Petroleum")
        
        # Menu de sélection
        selected_doc = st.selectbox(
            "Choisissez une section de documentation :",
            list(DocumentationUI.DOCUMENTATION_MENU.keys()),
            key="doc_selector"
        )
        
        # Affichage du document sélectionné
        if selected_doc:
            filename = DocumentationUI.DOCUMENTATION_MENU[selected_doc]
            DocumentationUI._display_markdown_file(filename)
    
    @staticmethod
    def _display_markdown_file(filename: str):
        """Affiche le contenu d'un fichier Markdown."""
        file_path = DocumentationUI.DOCS_PATH / filename
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Affichage avec style personnalisé
                st.markdown("""
                <style>
                .doc-container {
                    background: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    margin: 1rem 0;
                }
                .doc-container h1 {
                    color: #1f4e79;
                    border-bottom: 3px solid #2e8b57;
                    padding-bottom: 0.5rem;
                }
                .doc-container h2 {
                    color: #2e8b57;
                    margin-top: 2rem;
                }
                .doc-container h3 {
                    color: #1f4e79;
                }
                .doc-container code {
                    background: #f8f9fa;
                    padding: 0.2rem 0.4rem;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
                .doc-container pre {
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 5px;
                    border-left: 4px solid #2e8b57;
                    overflow-x: auto;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Conteneur pour le contenu
                st.markdown('<div class="doc-container">', unsafe_allow_html=True)
                st.markdown(content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Bouton de téléchargement
                st.download_button(
                    label=f"📥 Télécharger {filename}",
                    data=content,
                    file_name=filename,
                    mime="text/markdown"
                )
                
            else:
                st.error(f"❌ Fichier non trouvé : {filename}")
                st.info("Vérifiez que le fichier existe dans le dossier docs/")
                
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
            st.info("Contactez l'administrateur si le problème persiste.")
    
    @staticmethod
    def render_quick_help():
        """Affiche une aide rapide dans la sidebar."""
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📚 Documentation")
        
        if st.sidebar.button("📖 Ouvrir Documentation", key="open_docs"):
            st.session_state['show_documentation'] = True
            st.rerun()
        
        # Liens rapides
        st.sidebar.markdown("""
        **Accès Rapide :**
        - Guide Utilisateur
        - Architecture Système  
        - Modèles ML
        - Interface UI
        """)
    
    @staticmethod
    def render_embedded_help(doc_type: str = "user-guide"):
        """Affiche une aide contextuelle intégrée."""
        if doc_type in ["user-guide", "architecture", "models", "ui"]:
            filename_map = {
                "user-guide": "user-guide.md",
                "architecture": "architecture.md",
                "models": "prediction-models.md",
                "ui": "user-interface.md"
            }
            
            filename = filename_map.get(doc_type)
            if filename:
                with st.expander(f"📖 Aide - {doc_type.title()}"):
                    DocumentationUI._display_markdown_file(filename)