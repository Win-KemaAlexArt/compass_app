import os
import json
import queue
import logging
import threading
from flask import Flask, Response, send_from_directory

log = logging.getLogger(__name__)

class CompassStateAnnouncer:
    """
    Thread-safe pub-sub для передачи OrientationState SSE-клиентам.
    Каждый клиент получает свою очередь (maxsize=5).
    """
    def __init__(self):
        self._listeners: list[queue.Queue] = []
        self._lock = threading.Lock()

    def listen(self) -> queue.Queue:
        """Создает новую очередь для слушателя SSE."""
        q = queue.Queue(maxsize=5)
        with self._lock:
            self._listeners.append(q)
        return q

    def announce(self, msg: str) -> None:
        """Рассылает сообщение всем активным слушателям."""
        with self._lock:
            dead_indices = []
            for i, q in enumerate(self._listeners):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    dead_indices.append(i)
            
            for i in reversed(dead_indices):
                del self._listeners[i]

app = Flask(__name__)
announcer = CompassStateAnnouncer()
_calibration_trigger = threading.Event()
_calibration_save_trigger = threading.Event()

def _format_sse(data: str, event: str = None) -> str:
    """RFC-корректный SSE-формат."""
    msg = f"data: {data}\n\n"
    if event:
        msg = f"event: {event}\n{msg}"
    return msg

@app.route("/")
def index():
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    return send_from_directory(static_dir, "index.html")

@app.route("/stream")
def stream():
    """SSE-поток: бесконечный генератор JSON событий."""
    def generate():
        messages = announcer.listen()
        while True:
            try:
                msg = messages.get(timeout=15)
                yield _format_sse(msg)
            except queue.Empty:
                yield _format_sse("{}", event="heartbeat")
    
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.route("/calibrate", methods=["POST"])
def trigger_calibrate():
    _calibration_trigger.set()
    return {"status": "calibration_triggered"}, 202

@app.route("/calibrate/save", methods=["POST"])
def trigger_save_calibration():
    _calibration_save_trigger.set()
    return {"status": "save_triggered"}, 202

@app.route("/health")
def health():
    return {"status": "ok", "listeners": len(announcer._listeners)}, 200

def push_state(state_dict: dict) -> None:
    """Пушит состояние (или событие) всем SSE клиентам."""
    # Если в словаре есть ключ 'event', форматируем как именованное событие SSE
    event_name = state_dict.pop("event", None)
    payload = json.dumps(state_dict)
    msg = _format_sse(payload, event=event_name)
    announcer.announce(msg)

def start_server(port: int = 8080) -> None:
    """Запускает Flask сервер в daemon-потоке."""
    final_port = int(os.environ.get("COMPASS_PORT", port))
    
    def run():
        log.info("Web UI: http://localhost:%d", final_port)
        app.run(
            host="127.0.0.1",
            port=final_port,
            threaded=True,
            debug=False,
            use_reloader=False
        )

    thread = threading.Thread(target=run, daemon=True, name="flask-server")
    thread.start()

def get_calibration_trigger() -> threading.Event:
    return _calibration_trigger

def get_calibration_save_trigger() -> threading.Event:
    return _calibration_save_trigger
