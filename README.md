# FormaSup BI - Superset Docker

Plateforme de Business Intelligence basée sur Apache Superset 6.0.0, configurée pour FormaSup Auvergne.

## 🚀 Démarrage rapide

```bash
# Aller dans le dossier superset
cd superset

# Construire l'image française
.\build-superset-fr.ps1

# Retour à la racine
cd ..

# Démarrer les services
docker compose up -d

# Accéder à l'application
# URL: http://localhost:8088
# Login: admin / admin
```

## 📁 Structure du projet

- `superset/` - Configuration et sources Superset
- `init/` - Scripts d'initialisation PostgreSQL
- `migration/` - Scripts de migration de données
- `docker-compose.yml` - Orchestration des services
- `Dockerfile` - Image personnalisée

## 📖 Documentation complète

Voir [`superset/README.md`](superset/README.md) pour la documentation détaillée.

## 🐛 Problèmes ?

Consultez la section dépannage dans [`superset/README.md`](superset/README.md).