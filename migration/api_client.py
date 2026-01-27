#!/usr/bin/env python3
"""
Client API avec gestion de limitation de débit pour les API externes.
"""

import logging
import threading
import time

import requests # type: ignore
from requests.adapters import HTTPAdapter # type: ignore
from urllib3.util.retry import Retry # type: ignore


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

    def __init__(self, requests_per_second, retries: int = 3, backoff_factor: int = 1):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.session = self._create_session()
        self.lock = threading.Lock()

    def _create_session(self):
        """Creates an HTTP session with automatic retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.retries, status_forcelist=[429, 500, 502, 503, 504], backoff_factor=self.backoff_factor
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        return session

    def request(self, method, url, **kwargs):
        """
        Perform an HTTP request with rate limiting.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to query
            **kwargs: Additional arguments for requests.request

        Returns:
            HTTP response or None in case of error
        """
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

            self.last_request_time = time.time()

        try:
            response = self.session.request(method, url, **kwargs)
            # If we receive a 429 code, the session's retry strategy handles the timeout
            return response
        except requests.exceptions.RequestException as e:
            logging.getLogger("migration").error(f"API request error: {e}")
            time.sleep(2)
            return None
