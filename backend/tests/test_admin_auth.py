"""
Admin authentication: the shared-password gate on HTTP admin routes and
on the WebSocket admin:* mutation handlers.

Happy path:
  - correct password grants access to admin routes and WebSocket events
Failure path:
  - missing/wrong password is rejected (401) on HTTP admin routes,
    across a representative sample (not just one route)
  - missing/wrong password is rejected on WebSocket admin mutation
    events (regression: these used to accept mutations from any
    connected socket with no check at all)
"""
import pytest


# A representative sample of admin routes spanning different resource
# types and HTTP methods - not exhaustive, but enough to catch a
# regression in require_admin_auth itself rather than one route's use of it.
PROTECTED_ROUTES = [
    ('GET', '/api/admin/prizes'),
    ('GET', '/api/admin/inventory'),
    ('GET', '/api/admin/stats'),
    ('GET', '/api/admin/guaranteed-wins'),
    ('GET', '/api/admin/special-events'),
    ('GET', '/api/admin/templates'),
]


@pytest.mark.parametrize('method,path', PROTECTED_ROUTES)
def test_admin_route_rejects_missing_password(client, method, path):
    resp = client.open(path, method=method)
    assert resp.status_code == 401
    assert resp.get_json()['success'] is False


@pytest.mark.parametrize('method,path', PROTECTED_ROUTES)
def test_admin_route_rejects_wrong_password(client, method, path, wrong_admin_headers):
    resp = client.open(path, method=method, headers=wrong_admin_headers)
    assert resp.status_code == 401


@pytest.mark.parametrize('method,path', PROTECTED_ROUTES)
def test_admin_route_accepts_correct_password(client, method, path, admin_headers):
    resp = client.open(path, method=method, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['success'] is True


def test_reset_daily_wins_rejects_missing_password(client):
    resp = client.post('/api/admin/reset-daily-wins', json={'confirmation': 'RESET'})
    assert resp.status_code == 401


def test_websocket_admin_join_rejects_missing_password(socketio_client):
    socketio_client.emit('admin:join', {})
    received = socketio_client.get_received()
    events = [msg['name'] for msg in received]
    assert 'admin:error' in events
    assert 'admin:joined' not in events


def test_websocket_admin_join_rejects_wrong_password(socketio_client):
    socketio_client.emit('admin:join', {'admin_password': 'wrong'})
    received = socketio_client.get_received()
    events = [msg['name'] for msg in received]
    assert 'admin:error' in events
    assert 'admin:joined' not in events


def test_websocket_admin_join_accepts_correct_password(socketio_client):
    socketio_client.emit('admin:join', {'admin_password': 'myTAdmin2025'})
    received = socketio_client.get_received()
    events = [msg['name'] for msg in received]
    assert 'admin:joined' in events


def test_websocket_admin_add_prize_rejects_missing_password(socketio_client):
    socketio_client.emit('admin:add_prize', {'name': 'Sneaky Prize', 'category_id': 3})
    received = socketio_client.get_received()
    events = [msg['name'] for msg in received]
    assert 'admin:error' in events

    from app.database import execute_sql
    count = execute_sql(
        "SELECT COUNT(*) AS n FROM prizes WHERE name = 'Sneaky Prize'"
    )[0]['n']
    assert count == 0  # nothing was actually created
