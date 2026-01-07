#!/usr/bin/env python3
"""
Client API avec gestion de limitation de débit pour les API externes.
"""

import logging
import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RateLimitedAPI:
    """
    Client API avec limitation de débit pour éviter les erreurs 429 (too many requests).

    Attributes:
        requests_per_second: Nombre maximum de requêtes par seconde
        min_interval: Intervalle minimum entre deux requêtes (en secondes)
        last_request_time: Horodatage de la dernière requête effectuée
        session: Session HTTP réutilisable avec stratégie de réessai
        lock: Verrou pour synchroniser les requêtes en multithreading
    """

    def __init__(self, requests_per_second):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.session = self._create_session()
        self.lock = threading.Lock()

    def _create_session(self):
        """Crée une session HTTP avec stratégie de réessai automatique"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def request(self, method, url, **kwargs):
        """
        Effectue une requête HTTP avec limitation de débit.

        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL à interroger
            **kwargs: Arguments supplémentaires pour requests.request

        Returns:
            Réponse HTTP ou None en cas d'erreur
        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

            self.last_request_time = time.time()

        try:
            response = self.session.request(method, url, **kwargs)
            # Si on reçoit un code 429, la stratégie de retry de la session s'occupe de la temporisation
            return response
        except requests.exceptions.RequestException as e:
            logging.getLogger("migration").error(f"Erreur de requête API: {e}")
            time.sleep(2)
            return None
