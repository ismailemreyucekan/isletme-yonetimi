"""Faz 0 auth + tenant izolasyonu testleri."""

from __future__ import annotations

API = "/api/v1"


async def _register(client, *, name="Kafe Lojik", email="owner@kafe.com", password="parola123"):
    return await client.post(
        f"{API}/auth/register",
        json={
            "restaurant_name": name,
            "owner_name": "Sahip",
            "email": email,
            "password": password,
        },
    )


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_register_creates_owner_and_tokens(client):
    resp = await _register(client)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["role"] == "owner"
    assert data["user"]["email"] == "owner@kafe.com"


async def test_duplicate_email_rejected(client):
    await _register(client)
    resp = await _register(client)
    assert resp.status_code == 409


async def test_login_and_me(client):
    await _register(client)
    login = await client.post(
        f"{API}/auth/login",
        json={"email": "owner@kafe.com", "password": "parola123"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    me = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "owner@kafe.com"


async def test_wrong_password_rejected(client):
    await _register(client)
    login = await client.post(
        f"{API}/auth/login",
        json={"email": "owner@kafe.com", "password": "yanlis"},
    )
    assert login.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get(f"{API}/auth/me")
    assert resp.status_code in (401, 403)


async def test_refresh_returns_new_tokens(client):
    reg = await _register(client)
    refresh_token = reg.json()["refresh_token"]
    resp = await client.post(
        f"{API}/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["access_token"]


async def test_access_token_rejected_on_refresh_endpoint(client):
    reg = await _register(client)
    access = reg.json()["access_token"]
    resp = await client.post(f"{API}/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


async def test_tenant_isolation_two_restaurants(client):
    """İki ayrı işletme kaydı farklı restaurant_id'ler üretmeli."""
    r1 = await _register(client, name="Kafe Bir", email="a@bir.com")
    r2 = await _register(client, name="Kafe Iki", email="b@iki.com")
    assert r1.json()["user"]["restaurant_id"] != r2.json()["user"]["restaurant_id"]

    token1 = r1.json()["access_token"]
    rest1 = await client.get(
        f"{API}/auth/me/restaurant", headers={"Authorization": f"Bearer {token1}"}
    )
    assert rest1.status_code == 200
    assert rest1.json()["slug"] == "kafe-bir"
