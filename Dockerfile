# FormaSup BI - Image Superset francisee
# Base: superset-fr-formasup:latest (construite avec build-superset-fr.ps1)
# 
# L'image de base contient deja:
# - Les traductions compilees (.mo pour backend, .json pour frontend)
# - Superset 6.0.0 complet
#
# Ce Dockerfile ajoute uniquement:
# - psycopg2 pour PostgreSQL
# - Locales francaises
# - Configuration personnalisee (superset_config.py)
# - Logo et favicon

FROM superset-fr-formasup:latest

USER root

# Installation packages supplementaires (PostgreSQL client)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        locales \
        nodejs \
        npm && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Installation de psycopg2
RUN uv pip install psycopg2-binary

# Regenerer messages.json pour les traductions frontend
# Le Dockerfile officiel supprime les .json, donc on les regenere ici
COPY backup-messages.po /tmp/messages.po
RUN npm install -g po2json && \
    po2json --domain superset --format jed1.x --fuzzy /tmp/messages.po \
    /app/superset/translations/fr/LC_MESSAGES/messages.json && \
    rm /tmp/messages.po

# Configuration des locales francaises
RUN sed -i '/fr_FR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=fr_FR.UTF-8
ENV LANGUAGE=fr_FR:fr
ENV LC_ALL=fr_FR.UTF-8

# Creer les repertoires necessaires pour les assets
RUN mkdir -p /app/superset/static/assets/images/ && \
    chown -R superset:superset /app/superset/static/assets/ && \
    chmod -R 755 /app/superset/static/assets/

# Copier la configuration personnalisee
COPY superset/config/superset_config.py /app/pythonpath/
RUN chown superset:superset /app/pythonpath/superset_config.py

USER superset

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8088/health || exit 1
