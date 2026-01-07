# FormaSup BI - Plateforme de Reporting

## Présentation

FormaSup BI est une instance personnalisée d'Apache Superset 6.0.0 configurée pour FormaSup Auvergne et ses partenaires académiques (UCA, Clermont School of Business, ISRP).

**Interface 100% française par défaut** grâce à des corrections techniques du bug #35569 de Superset 6.0.0.

## Architecture

```txt
postgres_docker/
├── init/                        # Scripts init PostgreSQL
├── migration/                   # Scripts de migration
├── superset/
│   ├── apache-superset-src/     # Code source Superset (tag 6.0.0)
│   ├── assets/
│   │   ├── images/
│   │       ├── favicon.ico
│   │       └── logo.png
│   ├── backup-messages.po       # Traductions FR complètes (backup)
│   ├── build-superset-fr.ps1    # Script de build automatisé
│   ├── check_locale.py          # Script de test des locales
│   ├── config/
│   │   └── superset_config.py   # Configuration personnalisée
│   └── README.md                # Cette documentation
├── docker-compose.yml           # Orchestration des services
├── Dockerfile                   # Extension de l'image de base
└── README.md                    # Documentation principale (racine)
```

### Services

| Service | Port | Description |
| --------- | ------ | ------------- |
| superset-fsa | 8088 | Interface Superset |
| postgres-fsa | 5432 | Base de données métier |
| superset-db | 5442 | Base métadonnées Superset |

## Installation

### Prérequis

- Docker Desktop
- PowerShell 7+
- 16 GB RAM minimum

### Étapes

1. **Cloner le dépôt Superset**

```powershell
git clone https://github.com/apache/superset.git superset/apache-superset-src
cd superset/apache-superset-src
git checkout 6.0.0
cd ../..
```

2. **Construire l'image française**

```powershell
cd superset
.\build-superset-fr.ps1
cd ..
```

3. **Démarrer les services**

```powershell
docker compose up -d
```

4. **Accéder à l'application**

- URL : <http://localhost:8088>
- Login : admin
- Mot de passe : admin

## Traductions Françaises

### Problème résolu

Superset 6.0.0 présente un bug connu (#35569) qui cause une **race condition** dans le chargement des traductions françaises. Ce bug empêche l'affichage des traductions malgré la présence des fichiers.

### Solutions appliquées

#### 1. Corrections du code source
- **Backend** (`superset/views/base.py`) : Utilisation de `BABEL_DEFAULT_LOCALE` au lieu du fallback "en"
- **Frontend** (`superset-frontend/src/preamble.ts`) : Attendre le chargement du language pack avant rendu React

#### 2. Configuration personnalisée
- `BABEL_DEFAULT_LOCALE = "fr"`
- `LANGUAGES = {"fr": {"flag": "fr", "name": "Français"}}`
- Workaround pour contourner la race condition

#### 3. Architecture des traductions
- **Backend** : Fichiers `.po` → `.mo` (Flask-Babel)
- **Frontend** : Fichiers `.po` → `.json` (format jed1.x)

### Modifications appliquées

Le script `build-superset-fr.ps1` effectue 5 modifications pour forcer le français :

| Fichier | Modification |
| --------- | -------------- |
| messages.po | Traductions complètes (0 chaînes vides) |
| superset/config.py | BABEL_DEFAULT_LOCALE = "fr" |
| superset-frontend/src/constants.ts | locale: 'fr', lang: 'fr' |
| plugin-chart-echarts/src/constants.ts | DEFAULT_LOCALE = 'fr' |
| CurrencyFormatter.ts | locale = 'fr-FR' |

## Commandes utiles

### Redémarrer Superset

```powershell
docker compose restart superset
```

### Voir les logs

```powershell
docker logs superset-fsa --tail 100 -f
```

### Sauvegarder les bases

```powershell
docker exec postgres-fsa pg_dump -U postgres FSA > backup_fsa.sql
docker exec superset-db pg_dump -U superset superset > backup_superset.sql
```

### Reconstruire l'image

```powershell
cd superset
.\build-superset-fr.ps1
cd ..
docker compose up -d
```

### Vérifier les traductions

```bash
# Fichiers présents
docker exec superset-fsa ls -la /app/superset/translations/fr/LC_MESSAGES/

# Endpoint fonctionnel
docker exec superset-fsa curl -s 'http://localhost:8088/superset/language_pack/fr/' | head -20

# Logs d'initialisation
docker logs superset-fsa | grep -i "language\|traduction\|fr"
```

## Dépannage

### Interface en anglais

1. Vider le cache navigateur (Ctrl+Shift+Suppr)
2. Vérifier l'image : `docker images superset-fr-formasup`
3. Reconstruire : `cd superset && .\build-superset-fr.ps1 && cd ..`

### Erreur de connexion

```powershell
docker compose ps
```

Tous les services doivent être "healthy" ou "running".

### Debug avancé

```bash
# Inspecter le bootstrap data
docker exec superset-fsa curl -s 'http://localhost:8088/superset/bootstrap_data/' | jq '.locale'

# Vérifier les permissions
docker exec superset-fsa python -c "
from superset import app
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset import security_manager
    print('Public role permissions:', [p.name for p in security_manager.get_public_role().permissions])
"
```

## Configuration avancée

Éditer `superset/config/superset_config.py` pour :

- Modifier le branding
- Configurer les caches
- Activer/désactiver des fonctionnalités
- Configurer Row Level Security

## Licence

Apache Superset : Licence Apache 2.0

---

**Version** : 1.0.0 (Janvier 2026)
**Base** : Apache Superset 6.0.0
