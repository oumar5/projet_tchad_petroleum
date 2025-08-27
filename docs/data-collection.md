# 📥 Guide de Collecte des Données Pétrolières

## Vue d'Ensemble

Ce document détaille les processus de collecte, sources et formats des données utilisées dans le système de modélisation prédictive de Tchad Petroleum Company.

## 🎯 Objectifs de la Collecte

- **Centralisation** des données opérationnelles
- **Standardisation** des formats de données
- **Automatisation** des processus de collecte
- **Qualité** et intégrité des données
- **Traçabilité** des sources de données

## 📊 Sources de Données

### 1. Données de Production

#### 📍 Source Principale
- **Fichier** : `Données de production Rev.xlsx`
- **Feuille** : `Prod YOM BlocsFaillés X, Y et Z`
- **Fréquence** : Quotidienne
- **Format** : Excel (.xlsx)

#### 📋 Colonnes Collectées

| Colonne | Type | Description | Unité |
|---------|------|-------------|-------|
| Date | DateTime | Date de production | YYYY-MM-DD |
| Nombre total des puits | Integer | Puits totaux en service | Unités |
| Nombre des puits actifs | Integer | Puits en production active | Unités |
| Production journaliere d'huile bbl | Float | Production quotidienne huile | Barils |
| Production journaliere d'eau bbl | Float | Production quotidienne eau | Barils |
| Teneur en eau (Watercut) | Float | Pourcentage d'eau | % |
| Water Oil Ratio | Float | Ratio eau/huile | Ratio |
| Production journaliere d'eau en kilo baril jour | Float | Production eau en milliers | kbbl/j |

### 2. Données de Pannes

#### 📍 Source
- **Fichier** : `Données de production Rev.xlsx`
- **Feuille** : `Historiq Pannes pompes`
- **Fréquence** : Événementielle
- **Format** : Excel (.xlsx)

#### 📋 Informations Collectées
- Date de notification d'endommagement
- Type de panne
- Bloc concerné
- Durée d'intervention
- Coût de réparation
- Pièces remplacées

### 3. Données d'Interventions

#### 📍 Source
- **Fichier** : `Données de production Rev.xlsx`
- **Feuille** : `Interventions` (si disponible)
- **Fréquence** : Événementielle
- **Format** : Excel (.xlsx)

#### 📋 Informations Collectées
- Date d'intervention
- Type d'intervention
- Personnel impliqué
- Durée d'intervention
- Résultats obtenus

## 🔄 Processus de Collecte

### 1. Collecte Manuelle (Actuelle)

```python
# Exemple de collecte via data_loader.py
@st.cache_data
def load_production_data():
    """Charge et nettoie les données de production."""
    try:
        df = pd.read_excel(
            DATA_PATH + 'Données de production Rev.xlsx',
            sheet_name='Prod YOM BlocsFaillés X, Y et Z',
            skiprows=4,
            header=None,
            names=column_names
        )
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except FileNotFoundError:
        st.error("Fichier de production non trouvé.")
        return pd.DataFrame()
```

### 2. Validation des Données

#### ✅ Contrôles Automatiques
- **Format des dates** : Conversion automatique
- **Types de données** : Validation des types numériques
- **Valeurs manquantes** : Détection et signalement
- **Cohérence** : Vérification des relations logiques

#### 🚨 Alertes de Qualité
- Données manquantes > 5%
- Valeurs aberrantes détectées
- Incohérences temporelles
- Formats non conformes

## 📁 Structure des Fichiers

### Organisation Recommandée

```
data/
├── raw/                          # Données brutes
│   ├── production/
│   │   └── Données de production Rev.xlsx
│   ├── maintenance/
│   │   └── historique_pannes.xlsx
│   └── interventions/
│       └── log_interventions.xlsx
├── processed/                    # Données traitées
│   ├── production_clean.csv
│   ├── failures_processed.csv
│   └── interventions_clean.csv
└── archive/                      # Archives
    ├── 2023/
    └── 2024/
```

## 🔧 Configuration de Collecte

### Variables d'Environnement

```bash
# Chemin des données
DATA_PATH=./data/

# Configuration Excel
EXCEL_ENGINE=openpyxl
SKIP_ROWS=4

# Validation
MAX_MISSING_PERCENT=5
DATE_FORMAT=%Y-%m-%d
```

### Paramètres de Collecte

```python
# Configuration dans data_loader.py
COLLECTION_CONFIG = {
    'production': {
        'file': 'Données de production Rev.xlsx',
        'sheet': 'Prod YOM BlocsFaillés X, Y et Z',
        'skip_rows': 4,
        'date_column': 'Date'
    },
    'failures': {
        'file': 'Données de production Rev.xlsx',
        'sheet': 'Historiq Pannes pompes',
        'date_column': "Date de notification d'endomagement de la pompe"
    }
}
```

## 📈 Métriques de Qualité

### Indicateurs Surveillés

| Métrique | Seuil Acceptable | Action si Dépassé |
|----------|------------------|-------------------|
| Données manquantes | < 5% | Alerte + Investigation |
| Valeurs aberrantes | < 2% | Validation manuelle |
| Retard de collecte | < 24h | Notification équipe |
| Erreurs de format | 0% | Correction immédiate |

### Dashboard de Qualité

```python
# Exemple de métriques calculées
def get_data_quality_metrics(df):
    return {
        'completeness': (1 - df.isnull().sum().sum() / df.size) * 100,
        'freshness': (datetime.now() - df['Date'].max()).days,
        'consistency': validate_data_consistency(df),
        'accuracy': calculate_accuracy_score(df)
    }
```

## 🚀 Automatisation Future

### Phase 2 - Collecte Automatisée

#### 🔗 Intégrations Prévues
- **SCADA** : Collecte temps réel depuis systèmes de contrôle
- **Capteurs IoT** : Données de terrain automatisées
- **ERP** : Intégration avec systèmes de gestion
- **API** : Interfaces de données standardisées

#### 📡 Architecture Cible

```
Sources → ETL Pipeline → Data Lake → Processing → Application
   ↓           ↓            ↓           ↓           ↓
SCADA      Apache Kafka   MinIO    Spark/Pandas  Streamlit
IoT        Apache Airflow  S3       MLflow       API REST
ERP        Custom Scripts  HDFS     Jupyter      Dashboard
```

### Phase 3 - Intelligence Avancée

#### 🤖 Collecte Intelligente
- **Détection d'anomalies** en temps réel
- **Prédiction de qualité** des données
- **Auto-correction** des erreurs mineures
- **Apprentissage** des patterns de données

## 🛠️ Outils et Technologies

### Actuels
- **Pandas** : Manipulation des données
- **Openpyxl** : Lecture fichiers Excel
- **Streamlit** : Cache et interface
- **NumPy** : Calculs numériques

### Futurs
- **Apache Kafka** : Streaming de données
- **Apache Airflow** : Orchestration ETL
- **Great Expectations** : Validation de données
- **DVC** : Versioning des données

## 📚 Bonnes Pratiques

### ✅ Recommandations

1. **Sauvegarde régulière** des fichiers sources
2. **Versioning** des données critiques
3. **Documentation** des changements de format
4. **Tests** de validation automatisés
5. **Monitoring** continu de la qualité

### ❌ À Éviter

1. Modification directe des fichiers sources
2. Collecte sans validation
3. Formats propriétaires non documentés
4. Données sensibles non chiffrées
5. Absence de traçabilité

## 🔍 Dépannage

### Problèmes Courants

#### 📁 Fichier Non Trouvé
```python
# Vérification de l'existence
if not os.path.exists(file_path):
    st.error(f"Fichier non trouvé: {file_path}")
    st.info("Vérifiez que le fichier est dans le dossier data/")
```

#### 📊 Format Incorrect
```python
# Validation du format
try:
    df = pd.read_excel(file_path)
except Exception as e:
    st.error(f"Erreur de format: {e}")
    st.info("Vérifiez que le fichier est un Excel valide")
```

#### 📅 Dates Invalides
```python
# Conversion sécurisée des dates
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
invalid_dates = df['Date'].isnull().sum()
if invalid_dates > 0:
    st.warning(f"{invalid_dates} dates invalides détectées")
```

## 📞 Support

Pour toute question sur la collecte des données :
- **Documentation** : Consulter ce guide
- **Logs** : Vérifier les messages d'erreur Streamlit
- **Support** : Contacter l'équipe technique
- **Formation** : Sessions disponibles sur demande

---

*Ce document est mis à jour régulièrement. Dernière révision : Version 2.0*