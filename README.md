

# 🛢️ Projet de Digitalisation - Tchad Petroleum Company

## 📋 Description

Ce projet implémente une solution complète de digitalisation et d'optimisation pour Tchad Petroleum Company, incluant l'analyse de données de production, la maintenance prédictive, et l'optimisation des processus pétroliers.

## 🚀 Fonctionnalités Principales

### 📈 Analyse de Production
- Visualisation interactive des données de production d'huile
- Analyse des tendances temporelles
- Filtrage par période
- Métriques de performance en temps réel

### 🔧 Analyse des Pannes
- Historique des pannes de pompes par bloc
- Calcul du MTBF (Mean Time Between Failures)
- Analyse des patterns de défaillance
- Visualisations des statistiques de maintenance

### 🔮 Modélisation Prédictive

#### 🤖 Maintenance Prédictive
- **Prédiction des pannes de pompes** avec horizon de 7-30 jours
- **Algorithmes ML** : Random Forest, Gradient Boosting
- **Métriques** : Accuracy, Precision, Recall, F1-Score, AUC-ROC
- **Alertes automatiques** basées sur les probabilités de panne
- **Analyse d'importance des features**

#### 📊 Prévision de Production
- **Prédiction de la production d'huile** à court et moyen terme
- **Features temporelles** : tendances, saisonnalité, moyennes mobiles
- **Validation** sur les 2 dernières années
- **Métriques** : RMSE, MAE, R², MSE
- **Visualisations** : séries temporelles, prédictions vs réalité

#### 💧 Optimisation de l'Injection d'Eau
- **Optimisation des paramètres d'injection**
- **Maximisation de l'efficacité** huile/eau
- **Recommandations automatiques** basées sur l'IA
- **Analyse de corrélation** injection-production

#### 📊 Dashboard KPIs
- **Indicateurs de performance** en temps réel
- **Analyse comparative** automatique
- **Alertes intelligentes** basées sur les seuils
- **Rapports d'analyse** automatisés

## 🏗️ Architecture du Projet

```
projet_tchad_petroleum/
├── app.py                          # Application principale Streamlit
├── requirements.txt                # Dépendances Python
├── README.md                      # Documentation
├── data/
│   └── Données de production Rev.xlsx  # Données Excel
├── pages/
│   ├── 1_📈_Analyse_de_Production.py   # Page d'analyse de production
│   ├── 2_🔧_Analyse_des_Pannes.py      # Page d'analyse des pannes
│   └── 3_🔮_Modélisation_Prédictive.py # Page de modélisation prédictive
└── src/
    ├── __init__.py
    ├── data_loader.py              # Chargement et préparation des données
    ├── predictive_models.py        # Modèles de machine learning
    └── plotting.py                 # Fonctions de visualisation
```

## 🛠️ Installation et Configuration

### Prérequis
- Python 3.8+
- pip

### Installation

1. **Cloner le projet** :
```bash
git clone <repository-url>
cd projet_tchad_petroleum
```

2. **Installer les dépendances** :
```bash
pip install -r requirements.txt
```

3. **Placer les données** :
   - Copier le fichier Excel dans le dossier `data/`
   - Vérifier que le nom correspond à `Données de production Rev.xlsx`

4. **Lancer l'application** :
```bash
streamlit run app.py
```

5. **Accéder à l'interface** :
   - Ouvrir http://localhost:8501 dans votre navigateur

## 📊 Utilisation

### 1. Analyse de Production
- Naviguez vers "Analyse de Production"
- Utilisez les filtres de date pour explorer les données
- Analysez les tendances et les métriques

### 2. Analyse des Pannes
- Consultez l'historique des pannes par bloc
- Analysez les statistiques de maintenance
- Identifiez les patterns de défaillance

### 3. Modélisation Prédictive

#### Configuration Initiale
1. Allez dans "Modélisation Prédictive" > "Accueil"
2. Configurez le nombre d'années pour la validation (recommandé : 2 ans)
3. Visualisez l'aperçu des données

#### Maintenance Prédictive
1. Sélectionnez "Maintenance Prédictive"
2. Configurez l'horizon de prédiction (7-30 jours)
3. Cliquez sur "Entraîner le Modèle"
4. Analysez les métriques de performance
5. Utilisez "Prédictions en Temps Réel" pour les alertes

#### Prévision de Production
1. Sélectionnez "Prévision de Production"
2. Configurez l'horizon de prévision
3. Entraînez le modèle
4. Analysez les résultats et générez des prévisions

#### Optimisation Injection d'Eau
1. Sélectionnez "Optimisation Injection d'Eau"
2. Entraînez le modèle d'optimisation
3. Obtenez des recommandations automatiques

#### Dashboard KPIs
1. Consultez les indicateurs en temps réel
2. Générez des rapports d'analyse automatiques
3. Surveillez les alertes intelligentes

## 🔧 Fonctionnalités Techniques

### Modèles de Machine Learning
- **Random Forest** : Classification et régression
- **Gradient Boosting** : Prévisions de séries temporelles
- **Validation croisée** : Évaluation robuste des modèles
- **Feature Engineering** : Moyennes mobiles, tendances, lags

### Métriques de Performance
- **Classification** : Accuracy, Precision, Recall, F1-Score, AUC-ROC
- **Régression** : RMSE, MAE, R², MSE
- **Validation temporelle** : Split chronologique des données

### Visualisations Avancées
- **Matrices de confusion** pour la classification
- **Courbes ROC** pour l'évaluation des modèles
- **Graphiques de résidus** pour la régression
- **Séries temporelles** interactives
- **Dashboards KPIs** personnalisés

## 📈 Bénéfices Attendus

### Opérationnels
- **Réduction des temps d'arrêt** grâce à la maintenance prédictive
- **Optimisation de la production** par les prévisions
- **Amélioration de l'efficacité** de l'injection d'eau
- **Prise de décision** basée sur les données

### Économiques
- **Réduction des coûts** de maintenance
- **Maximisation de la récupération** d'huile
- **Optimisation des ressources** humaines et matérielles
- **Planification améliorée** des opérations

## 🔮 Développements Futurs

### Phase 2 - Intégration Avancée
- **API REST** pour l'intégration avec d'autres systèmes
- **Base de données** temps réel
- **Alertes automatiques** par email/SMS
- **Modèles ensemble** pour améliorer la précision

### Phase 3 - Intelligence Artificielle
- **Deep Learning** pour les séries temporelles complexes
- **Computer Vision** pour l'analyse d'images de terrain
- **NLP** pour l'analyse des rapports d'intervention
- **Optimisation multi-objectifs** avancée

## 🤝 Support et Maintenance

### Mise à Jour des Données
- Remplacer le fichier Excel dans le dossier `data/`
- Redémarrer l'application pour actualiser le cache

### Dépannage
- Vérifier les logs dans la console Streamlit
- S'assurer que toutes les dépendances sont installées
- Vérifier le format des données Excel

### Contact
Pour toute question ou support technique, contactez l'équipe de développement.

---

**🛢️ Tchad Petroleum Company - Système de Digitalisation et d'Optimisation**  
*Développé avec ❤️ pour l'excellence opérationnelle*