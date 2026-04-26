# SmartBarrel — Phase 2 : IoT & Systèmes Embarqués

> Roadmap de la phase d'industrialisation : remplacer la saisie manuelle de données par une **collecte automatique** via capteurs terrain et systèmes embarqués.

---

## 1. Vision

À l'issue de la **Phase 1**, SmartBarrel est une plateforme web/mobile alimentée par saisie manuelle ou import Excel/CSV. Les données arrivent au mieux quotidiennement, parfois avec retard, et restent sujettes aux erreurs humaines.

**La Phase 2 transforme SmartBarrel en plateforme temps réel** :

- Les **capteurs sur le terrain** mesurent en continu pression, débit, température, vibration, niveau
- Les **systèmes embarqués** (edge gateways) collectent, pré-traitent et transmettent les données
- L'`etl-service` ingère ces flux automatiquement, sans intervention humaine
- Les modèles ML s'entraînent sur des données haute fréquence et **gagnent en précision**
- Les alertes deviennent **temps réel** (panne détectée → notification en quelques secondes)

> **Pourquoi cette phase est cruciale** : l'IA ne vaut que par la qualité de ses données d'entrée. La saisie manuelle plafonne la précision des modèles. L'IoT débloque le passage à l'échelle.

---

## 2. Architecture cible

```
   [TERRAIN]                          [RÉSEAU]                [CLOUD / DC]
   ─────────                          ────────                ────────────

  ┌──────────┐
  │ Capteurs │ ── (4-20 mA / Modbus) ──┐
  │ pression │                         │
  └──────────┘                         │
                                       ▼
  ┌──────────┐                   ┌──────────────┐                ┌─────────────┐
  │ Capteurs │ ──────────────────▶  Edge Gateway│   MQTT/TLS     │  MQTT       │
  │ débit    │                   │ (RPi/PLC)    │ ───────────▶  │  Broker     │
  └──────────┘                   │ - filtrage   │  cellulaire    │ (EMQX)      │
                                 │ - agrégation │  / satellite   └──────┬──────┘
  ┌──────────┐                   │ - buffer     │  / LoRaWAN            │
  │ Capteurs │                   └──────────────┘                       ▼
  │ vibration│                          ▲                       ┌─────────────┐
  └──────────┘                          │                       │ etl-service │
                                  Alim solaire +                │ (FastAPI)   │
  ┌──────────┐                    batterie + IP68               └──────┬──────┘
  │ SCADA    │ ── OPC UA ──────────────┘                               │
  │ existant │                                                         ▼
  └──────────┘                                                  ┌─────────────┐
                                                                │ PostgreSQL  │
                                                                │ + RabbitMQ  │
                                                                └─────────────┘
```

---

## 3. Capteurs par cas d'usage

### 3.1 Maintenance prédictive (pompes immergées)

| Mesure | Capteur recommandé | Fréquence | Intérêt |
|--------|-------------------|-----------|---------|
| **Vibration** (axes X/Y/Z) | Accéléromètre piézo IEPE | 1 kHz (rafale) → résumé 1 min | Signature panne précoce |
| **Température moteur** | Sonde PT100 / RTD | 1 / minute | Surchauffe |
| **Courant moteur** | Pince ampèremétrique | 1 / seconde | Effort anormal |
| **Pression refoulement** | Transmetteur 4-20 mA | 1 / minute | Bouchage / fuite |

### 3.2 Production / réservoir

| Mesure | Capteur | Fréquence |
|--------|---------|-----------|
| **Débit huile** | Débitmètre Coriolis ou ultrasonique | 1 / minute |
| **Débit eau** | Débitmètre électromagnétique | 1 / minute |
| **Watercut** | Analyseur en ligne (capacitif ou microondes) | 5 / minute |
| **Pression tête de puits** | Transmetteur de pression | 1 / minute |
| **Température fond** | Sonde PT100 | 5 / minute |

### 3.3 Injection d'eau

| Mesure | Capteur | Fréquence |
|--------|---------|-----------|
| **Débit injecté** | Débitmètre électromagnétique | 1 / minute |
| **Pression injection** | Transmetteur | 1 / minute |
| **Qualité eau** (TDS, pH) | Sonde multiparamètre | 1 / heure |

---

## 4. Hardware embarqué

### 4.1 Edge Gateway

| Profil | Hardware | Cas d'usage |
|--------|----------|-------------|
| **Bas coût** | Raspberry Pi 5 industriel (ex. Revolution Pi) | Têtes de puits isolées |
| **Industriel léger** | Siemens IOT2050 | Environnements ATEX-like |
| **PLC** | Siemens S7-1200 / Allen-Bradley CompactLogix | Sites avec SCADA existant |
| **Microcontrôleur** | ESP32-S3 + LoRa | Capteurs autonomes très basse consommation |

**Stack edge logiciel** :
- OS : Debian / Yocto / Buildroot
- Runtime : Python (paho-mqtt, pymodbus) ou Node-RED pour prototypage rapide
- Buffer local : SQLite pour résilience hors-ligne
- Mise à jour OTA : balena.io ou rauc

### 4.2 Communication

| Protocole | Portée | Bande passante | Coût | Cas d'usage |
|-----------|--------|----------------|------|-------------|
| **LoRaWAN** | 5-15 km | très faible | très bas | Capteurs isolés, faible débit |
| **Cellulaire 4G/5G** | partout (couverture) | élevée | moyen | Tête de puits, gateway principal |
| **Satellite (Iridium, Starlink)** | partout | moyenne-élevée | élevé | Sites désertiques sans couverture cellulaire |
| **Wi-Fi industriel / mesh** | 100 m - 1 km | élevée | bas | Plateforme avec plusieurs équipements proches |
| **OPC UA** | LAN | élevée | bas | Intégration SCADA existant |
| **Modbus RTU/TCP** | LAN / RS-485 | faible | bas | Capteurs industriels classiques |

**Recommandation pour le Tchad** :
- Site avec couverture 4G → **cellulaire** comme primaire
- Site désertique → **Starlink** ou **Iridium** comme primaire
- Capteurs isolés → **LoRaWAN** vers gateway central, puis cellulaire/satellite

### 4.3 Protocole d'application : MQTT

**Pourquoi MQTT** :
- Standard de fait pour l'IoT industriel
- Léger (idéal pour bandes passantes limitées)
- Publish/subscribe → s'intègre parfaitement à l'architecture événementielle de SmartBarrel
- Support natif TLS et authentification par certificat

**Broker** : **EMQX** (open-source, scalable, support cluster) ou **HiveMQ Community**.

**Convention de topics** :
```
smartbarrel/
├── well/{well_id}/
│   ├── pressure
│   ├── flow/oil
│   ├── flow/water
│   ├── temperature
│   └── pump/
│       ├── vibration
│       ├── current
│       └── temperature
├── injection/{injection_id}/
│   ├── flow
│   └── pressure
└── gateway/{gateway_id}/
    ├── status
    └── heartbeat
```

**Format payload** : JSON ou MessagePack
```json
{
  "ts": "2026-08-15T14:32:01Z",
  "well_id": "BLOC-X-12",
  "value": 142.7,
  "unit": "bar",
  "quality": "good"
}
```

---

## 5. Alimentation et conditions terrain

### 5.1 Énergie

Les puits au Tchad sont souvent isolés sans accès au réseau électrique. Solution standard :

- **Panneaux solaires** 100-300 W selon consommation
- **Batteries LiFePO4** 50-200 Ah (durée de vie 10+ ans)
- **Régulateur MPPT**
- Autonomie cible : **5 jours sans soleil**

### 5.2 Conditions environnementales

- **Boîtiers IP65/IP68** pour étanchéité poussière + eau
- **Plage température** : -10 °C à +70 °C (déserts du nord du Tchad → chaud diurne, froid nocturne)
- **ATEX Zone 1/2** pour zones explosives autour des têtes de puits
- **Protection foudre** : parafoudre en amont du gateway

---

## 6. Sécurité (OT/IT)

L'IoT industriel est une **surface d'attaque critique** : un capteur compromis peut conduire à la falsification de données, voire à des dégâts physiques sur les équipements.

### Mesures obligatoires

| Couche | Mesure |
|--------|--------|
| **Identité device** | Certificat X.509 unique par gateway, provisionné en usine |
| **Transport** | TLS 1.3 obligatoire pour MQTT (port 8883) |
| **Authentification broker** | mTLS (client + serveur) |
| **Autorisation** | ACL MQTT par device : un gateway ne peut publier que sur ses propres topics |
| **Réseau** | VPN ou APN privé entre gateways et broker ; segmentation OT/IT |
| **Firmware** | Signature des images OTA, rollback automatique si échec |
| **Secrets** | Pas de credentials en clair, pas de Wi-Fi en mode "default password" |
| **Audit** | Tout message publié horodaté + traçable au gateway émetteur |
| **Intégrité données** | Signature HMAC optionnelle des payloads pour mesures critiques |

> **Référence** : suivre le standard **IEC 62443** (cybersécurité industrielle) pour la conception et l'exploitation.

---

## 7. Intégration avec l'application SmartBarrel

### 7.1 `etl-service` étendu

Le service ETL de Phase 1 (qui ingère Excel) gagne un nouveau connecteur **MQTT subscriber** :

```
etl-service/
├── connectors/
│   ├── excel_connector.py       # Phase 1
│   ├── csv_connector.py         # Phase 1
│   ├── mqtt_connector.py        # Phase 2 (nouveau)
│   ├── opcua_connector.py       # Phase 2 (nouveau)
│   └── modbus_connector.py      # Phase 2 (nouveau)
└── pipelines/
    ├── normalize.py
    ├── validate.py
    └── publish.py               # → RabbitMQ (data.ingested)
```

Les services métier (`production-service`, `maintenance-service`, `ml-service`) ne changent pas : ils consomment les mêmes événements RabbitMQ qu'en Phase 1. **Découplage total** : les capteurs ne savent pas qu'ils alimentent une IA.

### 7.2 Tables time-series

Les flux haute fréquence doivent être stockés efficacement. Deux options :

| Option | Avantage | Inconvénient |
|--------|----------|--------------|
| **TimescaleDB** (extension Postgres) | Reste dans Postgres, SQL standard, hypertables performantes | Une dépendance de plus |
| **InfluxDB** dédié | Optimisé time-series natif | Stack supplémentaire à maintenir |

**Recommandation** : **TimescaleDB**, pour rester sur PostgreSQL et préserver la cohérence transactionnelle avec les schémas métier.

### 7.3 Temps réel côté Flutter

Les écrans Flutter de Phase 1 (dashboard, monitoring puits) reçoivent les données capteurs via **WebSocket** ouvert sur la gateway Traefik :

```
Flutter → wss://api.smartbarrel.td/v1/realtime/wells/{id}
       ← stream live (1 message / mesure)
```

Permet d'afficher des graphiques qui se mettent à jour en direct, type SCADA.

---

## 8. Plan de déploiement

### Jalon 2.1 — POC sur 1 puits (8 sem.)

- [ ] Choix capteurs + commande
- [ ] Assemblage gateway prototype (Raspberry Pi)
- [ ] Coffret électrique + alimentation solaire
- [ ] Setup broker EMQX + connecteur MQTT dans `etl-service`
- [ ] Premières mesures en production sur **1 puits pilote**
- [ ] Validation : données arrivent bien dans la DB et s'affichent dans Flutter

**Livrable** : un puits "smart" avec mesures temps réel visibles dans l'app.

### Jalon 2.2 — Pilote 1 bloc (12 sem.)

- [ ] Industrialisation du gateway (boîtier IP65, certifications)
- [ ] Déploiement sur **tous les puits d'un bloc** (~10-20 puits)
- [ ] Intégration **SCADA existant** via OPC UA si présent
- [ ] Pré-traitement edge (compression, agrégation, filtrage)
- [ ] Procédures d'installation et de maintenance documentées
- [ ] Formation des techniciens terrain

**Livrable** : un bloc entièrement instrumenté, données 100 % automatiques.

### Jalon 2.3 — Généralisation (12 sem.)

- [ ] Roll-out sur tous les blocs
- [ ] Migration TimescaleDB pour stocker l'historique haute fréquence
- [ ] **Ré-entraînement des modèles ML** sur les nouvelles données (gain de précision attendu)
- [ ] Alertes temps réel (WebSocket → push notif Flutter)
- [ ] Dashboard SCADA-like pour opérateurs salle de contrôle
- [ ] Tableau de bord santé du parc IoT (gateways en ligne, batteries, signal)

**Livrable** : SmartBarrel devient une plateforme **temps réel à l'échelle de la production nationale**.

---

## 9. Budget indicatif (à raffiner)

| Poste | Coût unitaire (USD) | Quantité | Total |
|-------|---------------------|----------|-------|
| Capteurs par puits (vibration, pression, débit, temp) | 2 000 - 5 000 | × N puits | variable |
| Gateway industriel + boîtier | 800 - 2 000 | × 1 par groupe de puits | variable |
| Panneaux solaires + batterie + régulateur | 500 - 1 500 | × 1 par gateway | variable |
| Connectivité (cellulaire/satellite mensuelle) | 30 - 200 / mois | × N gateways | OPEX |
| Broker EMQX + TimescaleDB | self-hosted | infra existante | inclus |
| Installation + formation | service | | variable |

> **Ordre de grandeur** : pour un POC 1 puits = **~6 000 - 10 000 USD**. Pour un bloc complet = **50 000 - 200 000 USD** selon nombre de puits.

---

## 10. Risques spécifiques à la Phase 2

| Risque | Mitigation |
|--------|-----------|
| **Coût initial élevé** | POC sur 1 puits avant d'engager le bloc complet ; ROI démontré avant scale |
| **Cybersécurité OT** | Suivre IEC 62443 ; audits de sécurité ; segmentation réseau stricte |
| **Maintenance hardware terrain** | Stocks de capteurs/gateways de rechange ; télé-diagnostic ; techniciens formés |
| **Qualité des données capteur** | Validation croisée avec saisie manuelle pendant 3 mois ; détection d'anomalies sur les capteurs eux-mêmes |
| **Connectivité instable** | Buffer local SQLite sur gateway (jusqu'à 7 jours) ; sync différée |
| **Vandalisme / vol** | Boîtiers verrouillés ; géolocalisation ; gardiennage selon zones |
| **Conditions désertiques** | Hardware certifié -10/+70 °C ; tests de qualification avant déploiement |
| **Compétences IoT/OT internes** | Recrutement / formation d'un profil **automaticien/IoT** ; partenariat avec intégrateur local |

---

## 11. Compétences à mobiliser

La Phase 2 nécessite des profils que la Phase 1 (full-soft) ne couvrait pas :

- **Automaticien / instrumentiste** : choix capteurs, mise en service, maintenance
- **Ingénieur électronique embarquée** : conception/intégration gateway, alimentation
- **Ingénieur cybersécurité OT** : durcissement, conformité IEC 62443
- **Technicien terrain** : installation, diagnostic, intervention sur site
- **Data engineer time-series** : optimisation TimescaleDB, agrégations, downsampling

À recruter ou à externaliser via partenariat.

---

## 12. Indicateurs de succès

À l'issue de la Phase 2, les KPIs suivants doivent être atteints :

| KPI | Cible |
|-----|-------|
| Couverture capteurs | **100 %** des puits actifs |
| Disponibilité du flux de données | **≥ 99 %** sur 30 jours glissants |
| Latence ingestion (capteur → DB) | **< 10 secondes** |
| Précision des modèles ML | **+10 à +20 %** vs Phase 1 |
| Suppression de la saisie manuelle | **100 %** des données opérationnelles |
| Alertes panne détectées avant survenue | **+50 %** vs Phase 1 |

---

*Document vivant — à raffiner après le POC du Jalon 2.1.*
