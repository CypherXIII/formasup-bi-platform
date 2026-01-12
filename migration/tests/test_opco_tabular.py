#!/usr/bin/env python3
"""
Tests for OPCO enrichment Tabular API helpers.
"""

from api_enrichment import get_opco_by_siret, get_opco_by_siren


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def request(self, method, url, params=None, headers=None):
        self.calls.append({"method": method, "url": url, "params": params, "headers": headers})
        return self._response


def test_get_opco_by_siret_uses_uppercase_filter_and_opco_columns():
    payload = {"data": [{"SIRET": "49444152000017", "OPCO_PROPRIETAIRE": "OPCO2I"}]}
    client = DummyClient(DummyResponse(200, payload))

    opco = get_opco_by_siret("49444152000017", client)

    assert client.calls[0]["params"]["SIRET__exact"] == "49444152000017"
    assert opco == "OPCO 2I"


def test_get_opco_by_siren_prefers_most_common_and_uppercase_field():
    payload = {
        "data": [
            {"OPCO_PROPRIETAIRE": "AKTO"},
            {"OPCO_GESTION": "OPCO2I"},
            {"OPCO_PROPRIETAIRE": "OPCO2I"},
        ]
    }
    client = DummyClient(DummyResponse(200, payload))

    opco = get_opco_by_siren("123456789", client)

    assert client.calls[0]["params"]["SIRET__startswith"] == "123456789"
    assert opco == "OPCO 2I"
