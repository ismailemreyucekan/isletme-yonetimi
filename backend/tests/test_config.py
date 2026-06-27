"""Ayar (Settings) ayrıştırma testleri — özellikle CORS_ORIGINS env davranışı."""

from __future__ import annotations

from app.core.config import Settings


def test_cors_origins_from_csv_env(monkeypatch):
    """Virgülle ayrılmış CORS_ORIGINS env değeri listeye çevrilmeli (Docker senaryosu)."""
    monkeypatch.setenv("CORS_ORIGINS", "http://a.example.com, http://b.example.com")
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["http://a.example.com", "http://b.example.com"]


def test_cors_origins_default():
    settings = Settings(_env_file=None)
    assert settings.cors_origins == ["http://localhost:5173"]
