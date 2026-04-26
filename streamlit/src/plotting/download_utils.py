import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from typing import Optional
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

def add_download_button(fig, filename: str = None, format: str = "png", dpi: int = 300, key: str = None):
    """
    Ajoute un bouton de téléchargement pour une figure matplotlib.
    
    Args:
        fig: Figure matplotlib
        filename: Nom du fichier (optionnel, généré automatiquement si None)
        format: Format de l'image ('png', 'jpg', 'svg', 'pdf')
        dpi: Résolution de l'image
        key: Clé unique pour le bouton Streamlit
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"graphique_{timestamp}"
    
    # Créer le buffer pour l'image
    img_buffer = io.BytesIO()
    
    try:
        # Sauvegarder la figure dans le buffer
        fig.savefig(img_buffer, format=format, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        img_buffer.seek(0)
        
        # Créer le bouton de téléchargement
        st.download_button(
            label=f"📥 Télécharger ({format.upper()})",
            data=img_buffer.getvalue(),
            file_name=f"{filename}.{format}",
            mime=f"image/{format}",
            key=key,
            help=f"Télécharger le graphique en format {format.upper()}"
        )
        
    except Exception as e:
        st.error(f"Erreur lors de la génération du téléchargement: {e}")
    finally:
        img_buffer.close()

def add_plotly_download_button(fig, filename: str = None, format: str = "png", key: str = None):
    """
    Ajoute un bouton de téléchargement pour une figure Plotly.
    
    Args:
        fig: Figure Plotly
        filename: Nom du fichier (optionnel)
        format: Format de l'image ('png', 'jpg', 'svg', 'pdf', 'html')
        key: Clé unique pour le bouton
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"graphique_plotly_{timestamp}"
    
    try:
        if format == 'html':
            # Export HTML interactif
            html_buffer = io.StringIO()
            fig.write_html(html_buffer)
            html_content = html_buffer.getvalue()
            
            st.download_button(
                label="📥 Télécharger (HTML Interactif)",
                data=html_content,
                file_name=f"{filename}.html",
                mime="text/html",
                key=key,
                help="Télécharger le graphique interactif en HTML"
            )
        else:
            # Export image statique
            img_bytes = fig.to_image(format=format, width=1200, height=800)
            
            st.download_button(
                label=f"📥 Télécharger ({format.upper()})",
                data=img_bytes,
                file_name=f"{filename}.{format}",
                mime=f"image/{format}",
                key=key,
                help=f"Télécharger le graphique en format {format.upper()}"
            )
            
    except Exception as e:
        st.error(f"Erreur lors de la génération du téléchargement Plotly: {e}")

def create_download_section(fig, title: str = "Téléchargement", formats: list = None, key_prefix: str = None):
    """
    Crée une section complète de téléchargement avec plusieurs formats.
    
    Args:
        fig: Figure matplotlib ou Plotly
        title: Titre de la section
        formats: Liste des formats disponibles
        key_prefix: Préfixe pour les clés des boutons
    """
    if formats is None:
        formats = ['png', 'jpg', 'svg', 'pdf']
    
    if key_prefix is None:
        key_prefix = f"download_{datetime.now().strftime('%H%M%S')}"
    
    # Créer une section expandable pour les options de téléchargement
    with st.expander(f"📥 {title}", expanded=False):
        st.markdown("**Choisissez le format de téléchargement :**")
        
        # Créer des colonnes pour les boutons
        cols = st.columns(len(formats))
        
        for i, format_type in enumerate(formats):
            with cols[i]:
                # Générer un nom de fichier basé sur le titre
                clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = clean_title.replace(' ', '_').lower()
                
                # Déterminer le type de figure et ajouter le bon bouton
                if hasattr(fig, 'to_image'):  # Figure Plotly
                    add_plotly_download_button(
                        fig, 
                        filename=filename, 
                        format=format_type,
                        key=f"{key_prefix}_{format_type}"
                    )
                else:  # Figure Matplotlib
                    add_download_button(
                        fig, 
                        filename=filename, 
                        format=format_type,
                        key=f"{key_prefix}_{format_type}"
                    )
        
        # Options avancées
        st.markdown("---")
        st.markdown("**Options avancées :**")
        
        col1, col2 = st.columns(2)
        with col1:
            dpi = st.selectbox(
                "Qualité (DPI)",
                [150, 300, 600, 1200],
                index=1,
                key=f"{key_prefix}_dpi",
                help="Plus le DPI est élevé, meilleure est la qualité (mais fichier plus lourd)"
            )
        
        with col2:
            include_timestamp = st.checkbox(
                "Inclure timestamp",
                value=True,
                key=f"{key_prefix}_timestamp",
                help="Ajouter la date et l'heure au nom du fichier"
            )
        
        # Bouton de téléchargement haute qualité
        if st.button(f"📥 Télécharger HD (PNG {dpi} DPI)", key=f"{key_prefix}_hd"):
            timestamp_suffix = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if include_timestamp else ""
            filename_hd = f"{filename}{timestamp_suffix}"
            
            if hasattr(fig, 'to_image'):  # Plotly
                img_bytes = fig.to_image(format='png', width=1920, height=1080)
                st.download_button(
                    label="💾 Sauvegarder HD",
                    data=img_bytes,
                    file_name=f"{filename_hd}_HD.png",
                    mime="image/png",
                    key=f"{key_prefix}_save_hd"
                )
            else:  # Matplotlib
                add_download_button(
                    fig, 
                    filename=f"{filename_hd}_HD", 
                    format='png',
                    dpi=dpi,
                    key=f"{key_prefix}_save_hd"
                )

def display_plot_with_download(fig, title: str = "Graphique", key_prefix: str = None):
    """
    Affiche un graphique avec les options de téléchargement intégrées.
    
    Args:
        fig: Figure matplotlib ou Plotly
        title: Titre du graphique
        key_prefix: Préfixe pour les clés uniques
    """
    # Afficher le graphique
    if hasattr(fig, 'to_image'):  # Plotly
        st.plotly_chart(fig, use_container_width=True)
    else:  # Matplotlib
        st.pyplot(fig)
    
    # Ajouter les options de téléchargement
    create_download_section(fig, title, key_prefix=key_prefix)

def create_batch_download(figures_dict: dict, key_prefix: str = "batch"):
    """
    Crée une section pour télécharger plusieurs graphiques en lot.
    
    Args:
        figures_dict: Dictionnaire {nom: figure}
        key_prefix: Préfixe pour les clés
    """
    if not figures_dict:
        return
    
    with st.expander("📦 Téléchargement en lot", expanded=False):
        st.markdown("**Télécharger plusieurs graphiques simultanément :**")
        
        # Sélection des graphiques
        selected_plots = st.multiselect(
            "Choisissez les graphiques à télécharger :",
            list(figures_dict.keys()),
            default=list(figures_dict.keys()),
            key=f"{key_prefix}_selection"
        )
        
        if selected_plots:
            col1, col2 = st.columns(2)
            
            with col1:
                batch_format = st.selectbox(
                    "Format",
                    ['png', 'jpg', 'svg', 'pdf'],
                    key=f"{key_prefix}_format"
                )
            
            with col2:
                batch_dpi = st.selectbox(
                    "Qualité (DPI)",
                    [150, 300, 600],
                    index=1,
                    key=f"{key_prefix}_batch_dpi"
                )
            
            if st.button("📥 Télécharger la sélection", key=f"{key_prefix}_download"):
                # Créer un ZIP avec tous les graphiques sélectionnés
                import zipfile
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for plot_name in selected_plots:
                        fig = figures_dict[plot_name]
                        
                        # Créer le buffer pour chaque image
                        img_buffer = io.BytesIO()
                        
                        try:
                            if hasattr(fig, 'to_image'):  # Plotly
                                img_bytes = fig.to_image(format=batch_format, width=1200, height=800)
                                img_buffer.write(img_bytes)
                            else:  # Matplotlib
                                fig.savefig(img_buffer, format=batch_format, dpi=batch_dpi, 
                                          bbox_inches='tight', facecolor='white')
                            
                            img_buffer.seek(0)
                            
                            # Ajouter au ZIP
                            clean_name = "".join(c for c in plot_name if c.isalnum() or c in (' ', '-', '_'))
                            filename = f"{clean_name.replace(' ', '_')}.{batch_format}"
                            zip_file.writestr(filename, img_buffer.getvalue())
                            
                        except Exception as e:
                            st.error(f"Erreur avec {plot_name}: {e}")
                        finally:
                            img_buffer.close()
                
                zip_buffer.seek(0)
                
                # Bouton de téléchargement du ZIP
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="💾 Télécharger le ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"graphiques_{timestamp}.zip",
                    mime="application/zip",
                    key=f"{key_prefix}_zip_download"
                )