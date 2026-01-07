# FormaSup BI - Plateforme de Reporting

## Presentation

FormaSup BI est une instance personnalisee d'Apache Superset 6.0.0 configuree pour FormaSup Auvergne et ses partenaires academiques (UCA, Clermont School of Business, ISRP).

Interface 100% francaise par defaut.

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
│   ├── backup-messages.po       # Traductions FR completes (backup)
│   ├── check_locale.py          # Script de test des locales
│   ├── config/
│   │   └── superset_config.py   # Configuration personnalisee
│   ├── README-traductions-francaises.md  # Documentation traductions
│   └── README.md                # Documentation projet
├── build-superset-fr.ps1        # Script de build automatise
├── docker-compose.yml           # Orchestration des services
├── Dockerfile                   # Extension de l'image de base
└── README.md                    # Documentation principale
```

### Services

| Service | Port | Description |
| --------- | ------ | ------------- |
| superset-fsa | 8088 | Interface Superset |
| postgres-fsa | 5432 | Base de donnees metier |
| superset-db | 5442 | Base metadonnees Superset |

## Installation

### Prerequis

- Docker Desktop
- PowerShell 7+
- 16 GB RAM minimum

### Etapes

1. **Cloner le depot Superset**

```powershell
git clone https://github.com/apache/superset.git superset/apache-superset-src
cd superset/apache-superset-src
git checkout 6.0.0
cd ../..
```

1. **Construire l'image francaise**

```powershell
.\build-superset-fr.ps1
```

1. **Demarrer les services**

```powershell
docker compose up -d
```

1. **Acceder a l'application**

- URL : <http://localhost:8088>
- Login : admin
- Mot de passe : admin

## Modifications appliquees

Le script `build-superset-fr.ps1` effectue 5 modifications pour forcer le francais :

| Fichier | Modification |
| --------- | -------------- |
| messages.po | Traductions completes (0 chaines vides) |
| superset/config.py | BABEL_DEFAULT_LOCALE = "fr" |
| superset-frontend/src/constants.ts | locale: 'fr', lang: 'fr' |
| plugin-chart-echarts/src/constants.ts | DEFAULT_LOCALE = 'fr' |
| CurrencyFormatter.ts | locale = 'fr-FR' |

## Commandes utiles

### Redemarrer Superset

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
.\build-superset-fr.ps1
docker compose up -d
```

## Depannage

### Interface en anglais

1. Vider le cache navigateur (Ctrl+Shift+Suppr)
2. Verifier l'image : `docker images superset-fr-formasup`
3. Reconstruire : `.\build-superset-fr.ps1`

### Erreur de connexion

```powershell
docker compose ps
```

Tous les services doivent etre "healthy" ou "running".

## Configuration avancee

Editer `superset/config/superset_config.py` pour :

- Modifier le branding
- Configurer les caches
- Activer/desactiver des fonctionnalites
- Configurer Row Level Security

## Licence

Apache Superset : Licence Apache 2.0

---

**Version** : 1.0.0 (Janvier 2026)
**Base** : Apache Superset 6.0.0
