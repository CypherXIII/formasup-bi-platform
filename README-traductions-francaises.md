# Résolution du problème de traductions françaises dans Superset 6.0.0

## Contexte du problème

Superset 6.0.0 présente un bug connu (#35569) introduit par le PR #34119 qui cause une condition de course (race condition) dans le chargement des traductions. Ce bug empêche l'affichage des traductions françaises dans l'interface utilisateur, même si les fichiers de traduction sont présents.

### Symptômes observés
- Les traductions backend (.mo) fonctionnent correctement
- Les traductions frontend (.json) ne se chargent pas
- L'endpoint `/superset/language_pack/fr/` retourne une erreur "Language pack doesn't exist on the server"
- L'interface reste en anglais malgré la configuration française

## Analyse du problème

### Root cause identifié
Le problème vient d'une **race condition** entre :
1. **Backend** : Fallback hardcodé vers "en" au lieu d'utiliser `BABEL_DEFAULT_LOCALE`
2. **Frontend** : Chargement asynchrone du language pack qui s'exécute après le rendu React

### Code problématique identifié
- `superset/views/base.py` ligne 406 : `language = locale.language if locale else "en"`
- `superset-frontend/src/preamble.ts` : IIFE async non attendue
- `superset-frontend/src/views/index.tsx` : Rendu React immédiat sans attendre le language pack

## Solutions appliquées

### 1. Correction backend (base.py)
**Fichier modifié** : `superset/views/base.py`

```python
# Avant
language = locale.language if locale else "en"

# Après
language = locale.language if locale else app.config.get("BABEL_DEFAULT_LOCALE", "en")
```

Cette modification permet d'utiliser la configuration `BABEL_DEFAULT_LOCALE = "fr"` au lieu du fallback hardcodé vers "en".

### 2. Correction frontend (preamble.ts)
**Fichier modifié** : `superset-frontend/src/preamble.ts`

```typescript
// Avant : IIFE async non exportée
(async () => {
  // chargement du language pack...
})();

// Après : Fonction exportée
export async function initPreamble(): Promise<void> {
  // chargement du language pack...
}
```

### 3. Correction frontend (index.tsx)
**Fichier modifié** : `superset-frontend/src/views/index.tsx`

```typescript
// Avant : Rendu immédiat
import ReactDOM from 'react-dom';
import App from './App';
ReactDOM.render(<App />, document.getElementById('app'));

// Après : Attendre le language pack
import ReactDOM from 'react-dom';
import { initPreamble } from '../preamble';

(async () => {
  try {
    await initPreamble();
  } finally {
    const { default: App } = await import('./App');
    ReactDOM.render(<App />, document.getElementById('app'));
  }
})();
```

### 4. Suppression de l'import direct de preamble
**Fichier modifié** : `superset-frontend/src/views/RootContextProviders.tsx`

```typescript
// Supprimé l'import direct car preamble est maintenant importé dans index.tsx
// import '../preamble';
```

### 5. Configuration Superset
**Fichier modifié** : `superset/config/superset_config.py`

Ajout des configurations suivantes :
```python
BABEL_DEFAULT_LOCALE = "fr"
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Français"},
}

# Workaround pour le bug #35569
COMMON_BOOTSTRAP_OVERRIDES_FUNC = lambda app, user: {
    "locale": "fr",
    "language_pack": get_language_pack("fr")
}

# Permission pour accéder au language pack
FLASK_APP_MUTATOR = lambda app: app.appbuilder.sm.add_permission_to_role(
    "can language pack Superset", "Public"
)
```

## Architecture des traductions Superset

Superset utilise deux systèmes de traduction :

### Backend (Flask-Babel)
- **Fichiers** : `.po` → `.mo` (compilés)
- **Emplacement** : `superset/translations/fr/LC_MESSAGES/messages.mo`
- **Utilisation** : Traductions côté serveur, templates Jinja2

### Frontend (@superset-ui/translation)
- **Fichiers** : `.po` → `.json` (format jed1.x)
- **Emplacement** : `superset/translations/fr/LC_MESSAGES/messages.json`
- **Utilisation** : Traductions côté client, composants React

## Processus de build et déploiement

### 1. Build de l'image de base
```bash
cd apache-superset-src
docker build --build-arg BUILD_TRANSLATIONS=true -t superset-fr-formasup:latest --target lean .
```

### 2. Build de l'image locale
```bash
docker compose build --no-cache
```

### 3. Déploiement
```bash
docker compose up -d
```

### 4. Vérification
```bash
# Vérifier les fichiers de traduction
docker exec superset-fsa ls -la /app/superset/translations/fr/LC_MESSAGES/

# Tester l'endpoint du language pack
docker exec superset-fsa curl -s 'http://localhost:8088/superset/language_pack/fr/'

# Vérifier les logs
docker logs superset-fsa --tail 50
```

## Résultats obtenus

### Corrections réussies
- **Backend** : Utilise maintenant `BABEL_DEFAULT_LOCALE` au lieu de "en"
- **Frontend** : Attend le chargement du language pack avant le rendu React
- **Configuration** : Workaround appliqué pour contourner le bug #35569
- **Permissions** : Rôle Public a accès au language pack

### Fonctionnalités validées
- L'endpoint `/superset/language_pack/fr/` retourne maintenant les traductions JSON
- Les fichiers `messages.mo` et `messages.json` sont présents
- L'interface utilisateur s'affiche en français
- Les traductions persistent après rechargement de page

### Limitations connues
- Le bug #35569 est un problème upstream qui nécessite une correction dans Superset
- Cette solution est un workaround qui peut être affecté par les futures mises à jour
- Le script `po2json.sh` n'est pas trouvé pendant le build (mais les traductions fonctionnent)

## Fichiers modifiés

### Code source Superset
- `superset/views/base.py` : Correction du fallback backend
- `superset-frontend/src/preamble.ts` : Export de la fonction initPreamble
- `superset-frontend/src/views/index.tsx` : Attendre initPreamble avant rendu
- `superset-frontend/src/views/RootContextProviders.tsx` : Suppression import preamble

### Configuration locale
- `superset/config/superset_config.py` : Configuration française + workaround
- `docker-compose.yml` : Images et healthcheck
- `Dockerfile` : Build personnalisé

## Commandes de maintenance

### Redémarrage complet
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Vérification des traductions
```bash
# Fichiers présents
docker exec superset-fsa ls -la /app/superset/translations/fr/LC_MESSAGES/

# Endpoint fonctionnel
docker exec superset-fsa curl -s 'http://localhost:8088/superset/language_pack/fr/' | head -20

# Logs d'initialisation
docker logs superset-fsa | grep -i "language\|traduction\|fr"
```

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

## Conclusion

La solution implémentée corrige efficacement le bug de traductions françaises dans Superset 6.0.0 en appliquant :

1. **Les corrections upstream** du GitHub issue #35569
2. **Un workaround de configuration** pour contourner la race condition
3. **Une architecture de build** optimisée pour les traductions

L'interface Superset s'affiche maintenant entièrement en français, résolvant le problème initial de l'utilisateur qui souhaitait "qu'il n'y est plus d'anglais sur le front end".