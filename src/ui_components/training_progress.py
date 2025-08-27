import streamlit as st
import time
from typing import Dict, List, Optional
import threading
from datetime import datetime

class TrainingProgress:
    """Composant pour afficher la progression d'entraînement des modèles."""
    
    def __init__(self):
        self.progress_data = {}
        self.current_model = None
        self.start_time = None
        self.total_models = 0
        self.completed_models = 0
        
    def initialize_training(self, model_names: List[str]):
        """Initialise la session d'entraînement."""
        self.total_models = len(model_names)
        self.completed_models = 0
        self.start_time = datetime.now()
        
        # Initialiser les données de progression pour chaque modèle
        for model_name in model_names:
            self.progress_data[model_name] = {
                'status': 'pending',
                'progress': 0,
                'start_time': None,
                'end_time': None,
                'error': None,
                'metrics': None,
                'stage': 'En attente'
            }
    
    def start_model_training(self, model_name: str):
        """Démarre l'entraînement d'un modèle."""
        self.current_model = model_name
        self.progress_data[model_name].update({
            'status': 'training',
            'start_time': datetime.now(),
            'stage': 'Préparation des données'
        })
    
    def update_model_progress(self, model_name: str, progress: int, stage: str = None):
        """Met à jour la progression d'un modèle."""
        if model_name in self.progress_data:
            self.progress_data[model_name]['progress'] = progress
            if stage:
                self.progress_data[model_name]['stage'] = stage
    
    def complete_model_training(self, model_name: str, success: bool = True, 
                              error: str = None, metrics: Dict = None):
        """Marque l'entraînement d'un modèle comme terminé."""
        if model_name in self.progress_data:
            self.progress_data[model_name].update({
                'status': 'completed' if success else 'error',
                'end_time': datetime.now(),
                'progress': 100 if success else self.progress_data[model_name]['progress'],
                'error': error,
                'metrics': metrics,
                'stage': 'Terminé' if success else 'Erreur'
            })
            
            if success:
                self.completed_models += 1
    
    def render_progress_dashboard(self):
        """Affiche le tableau de bord de progression."""
        if not self.progress_data:
            return
        
        st.subheader("📊 Progression de l'Entraînement")
        
        # Progression globale
        overall_progress = (self.completed_models / self.total_models) * 100 if self.total_models > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Progression Globale", f"{overall_progress:.1f}%")
        with col2:
            st.metric("Modèles Terminés", f"{self.completed_models}/{self.total_models}")
        with col3:
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                st.metric("Temps Écoulé", f"{elapsed.seconds//60}m {elapsed.seconds%60}s")
        
        # Barre de progression globale
        st.progress(overall_progress / 100)
        
        # Détails par modèle
        st.markdown("### 🔍 Détails par Modèle")
        
        for model_name, data in self.progress_data.items():
            with st.expander(f"{self._get_status_icon(data['status'])} {model_name}", 
                           expanded=(data['status'] == 'training')):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Barre de progression du modèle
                    st.progress(data['progress'] / 100)
                    st.write(f"**Étape :** {data['stage']}")
                    
                    # Temps d'entraînement
                    if data['start_time']:
                        if data['end_time']:
                            duration = data['end_time'] - data['start_time']
                            st.write(f"**Durée :** {duration.seconds}s")
                        else:
                            elapsed = datetime.now() - data['start_time']
                            st.write(f"**Temps écoulé :** {elapsed.seconds}s")
                
                with col2:
                    # Statut et métriques
                    status_color = {
                        'pending': '🟡',
                        'training': '🔵',
                        'completed': '🟢',
                        'error': '🔴'
                    }
                    st.write(f"**Statut :** {status_color.get(data['status'], '⚪')} {data['status'].title()}")
                    
                    if data['error']:
                        st.error(f"Erreur: {data['error']}")
                    
                    if data['metrics']:
                        st.write("**Métriques :**")
                        for metric, value in data['metrics'].items():
                            if isinstance(value, float):
                                st.write(f"- {metric}: {value:.4f}")
                            else:
                                st.write(f"- {metric}: {value}")
    
    def _get_status_icon(self, status: str) -> str:
        """Retourne l'icône correspondant au statut."""
        icons = {
            'pending': '⏳',
            'training': '🔄',
            'completed': '✅',
            'error': '❌'
        }
        return icons.get(status, '⚪')
    
    def render_live_progress(self, placeholder):
        """Affiche la progression en temps réel dans un placeholder."""
        with placeholder.container():
            if self.current_model and self.current_model in self.progress_data:
                current_data = self.progress_data[self.current_model]
                
                st.write(f"🔄 **Entraînement en cours :** {self.current_model}")
                st.write(f"📍 **Étape :** {current_data['stage']}")
                
                # Barre de progression animée
                progress_bar = st.progress(current_data['progress'] / 100)
                
                # Temps écoulé
                if current_data['start_time']:
                    elapsed = datetime.now() - current_data['start_time']
                    st.write(f"⏱️ **Temps écoulé :** {elapsed.seconds}s")
    
    def get_training_summary(self) -> Dict:
        """Retourne un résumé de l'entraînement."""
        successful_models = [name for name, data in self.progress_data.items() 
                           if data['status'] == 'completed']
        failed_models = [name for name, data in self.progress_data.items() 
                        if data['status'] == 'error']
        
        total_time = None
        if self.start_time:
            end_time = max([data.get('end_time', datetime.now()) 
                          for data in self.progress_data.values() 
                          if data.get('end_time')])
            if end_time:
                total_time = (end_time - self.start_time).seconds
        
        return {
            'total_models': self.total_models,
            'successful_models': successful_models,
            'failed_models': failed_models,
            'success_rate': len(successful_models) / self.total_models * 100 if self.total_models > 0 else 0,
            'total_time': total_time
        }
    
    def render_training_summary(self):
        """Affiche le résumé final de l'entraînement."""
        summary = self.get_training_summary()
        
        st.subheader("📋 Résumé de l'Entraînement")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Modèles Totaux", summary['total_models'])
        with col2:
            st.metric("Succès", len(summary['successful_models']))
        with col3:
            st.metric("Échecs", len(summary['failed_models']))
        with col4:
            st.metric("Taux de Succès", f"{summary['success_rate']:.1f}%")
        
        if summary['total_time']:
            st.write(f"⏱️ **Temps total d'entraînement :** {summary['total_time']//60}m {summary['total_time']%60}s")
        
        # Détails des succès et échecs
        if summary['successful_models']:
            st.success(f"✅ **Modèles entraînés avec succès :** {', '.join(summary['successful_models'])}")
        
        if summary['failed_models']:
            st.error(f"❌ **Modèles en échec :** {', '.join(summary['failed_models'])}")
            
            # Détails des erreurs
            st.write("**Détails des erreurs :**")
            for model in summary['failed_models']:
                if model in self.progress_data and self.progress_data[model]['error']:
                    st.write(f"- **{model}:** {self.progress_data[model]['error']}")

def get_training_progress() -> TrainingProgress:
    """Retourne l'instance globale de TrainingProgress."""
    # Initialiser si pas encore fait
    if 'training_progress' not in st.session_state:
        st.session_state.training_progress = TrainingProgress()
    return st.session_state.training_progress