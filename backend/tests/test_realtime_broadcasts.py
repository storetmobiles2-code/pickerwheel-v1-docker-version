"""
Real-time broadcasts to connected WebSocket clients - the mechanism
admin.html's live-update banner (multi-device readiness P1) depends on.

Happy path:
  - a prize mutation over HTTP broadcasts prizes:updated to a connected
    socket, and the payload is valid JSON (regression test for the
    datetime-serialization bug found while building this: adding
    updated_at to Prize.get_all() broke every broadcast that included it
    once a real client was connected to receive it, via
    "Object of type datetime is not JSON serializable")
  - the payload's nested datetime fields arrive as ISO strings, not
    raw/opaque values a JS client couldn't use
"""
from app import socketio as flask_socketio


def test_prize_mutation_broadcasts_to_connected_client(app, admin_headers):
    client = app.test_client()
    sio = flask_socketio.test_client(app, flask_test_client=client)
    sio.get_received()  # drain the initial 'connected' event

    resp = client.post('/api/admin/prizes', json={
        'name': 'Broadcast Test Prize', 'category_id': 3,
    }, headers=admin_headers)
    assert resp.status_code == 200

    received = sio.get_received()
    events = {msg['name']: msg['args'][0] for msg in received}

    assert 'prizes:updated' in events
    assert any(p['name'] == 'Broadcast Test Prize' for p in events['prizes:updated']['prizes'])

    assert 'prize:added' in events
    assert events['prize:added']['prize']['name'] == 'Broadcast Test Prize'
    # updated_at must have made it through emit() as a plain ISO string,
    # not a raw datetime (which would have raised before this was fixed)
    assert isinstance(events['prize:added']['prize']['updated_at'], str)
    assert 'T' in events['prize:added']['prize']['updated_at']


def test_inventory_change_broadcasts_to_connected_client(app, admin_headers, make_prize):
    from app.models import Inventory
    prize = make_prize(quantity=10, daily_limit=5)
    current = Inventory.get_for_prize(prize['id'])
    client = app.test_client()
    sio = flask_socketio.test_client(app, flask_test_client=client)
    sio.get_received()

    resp = client.post(f'/api/admin/inventory/{prize["id"]}/set', json={
        'quantity': 7, 'expected_updated_at': current['updated_at'].isoformat(),
    }, headers=admin_headers)
    assert resp.status_code == 200

    received = sio.get_received()
    events = {msg['name']: msg['args'][0] for msg in received}
    assert 'prizes:updated' in events
