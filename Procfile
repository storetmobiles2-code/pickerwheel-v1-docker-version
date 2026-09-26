# Production entry point. `backend/main.py`'s `if __name__ == '__main__':`
# block (python main.py, the Werkzeug dev server) is for LOCAL DEV ONLY -
# this Procfile is what a real hosting platform should run instead.
#
# --workers MUST stay at 1: Socket.IO has no message_queue configured
# (see SOCKETIO_MESSAGE_QUEUE in backend/app/config.py), so broadcasts
# only reach clients connected to the SAME worker process. More than one
# worker (or more than one instance/replica) would silently drop
# real-time updates for some connected admins with no error anywhere.
# Don't raise --workers above 1 without first adding Redis as the
# Socket.IO message queue and testing cross-worker broadcasts.
#
# gthread (not eventlet/gevent) matches the app's existing
# async_mode='threading' Socket.IO config - lower risk than switching to
# a greenlet-based worker, since that needs monkey-patching main.py and
# isn't needed while running as a single instance.
web: cd backend && gunicorn --worker-class gthread --workers 1 --threads 4 --timeout 120 -b 0.0.0.0:$PORT main:app
