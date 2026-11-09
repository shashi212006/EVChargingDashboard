
from flask import Flask, render_template, jsonify
import threading
import time
import random

app = Flask(__name__)

TOTAL_CHARGERS = 3
TOTAL_EVS = 5

semaphore = threading.Semaphore(TOTAL_CHARGERS)
lock = threading.Lock()

chargers = [
    {"id": i, "status": "Available", "ev_id": None}
    for i in range(1, TOTAL_CHARGERS + 1)
]

waiting = []
completed = []
started = False
finished = False


def charge_ev(ev_id):
    global finished

    with lock:
        waiting.append(ev_id)

    semaphore.acquire()

    try:
        with lock:
            if ev_id in waiting:
                waiting.remove(ev_id)

            charger = next(
                c for c in chargers
                if c["status"] == "Available"
            )

            charger["status"] = "Charging"
            charger["ev_id"] = ev_id

        # Simulate the charging process
        time.sleep(random.randint(5, 10))

        with lock:
            charger["status"] = "Available"
            charger["ev_id"] = None
            completed.append(ev_id)

    finally:
        semaphore.release()

    with lock:
        if len(completed) == TOTAL_EVS:
            finished = True


def start_simulation():
    global started, finished

    with lock:
        if started and not finished:
            return

        # Reset the previous simulation
        for charger in chargers:
            charger["status"] = "Available"
            charger["ev_id"] = None

        waiting.clear()
        completed.clear()

        started = True
        finished = False

    for ev_id in range(1, TOTAL_EVS + 1):
        threading.Thread(
            target=charge_ev,
            args=(ev_id,),
            daemon=True
        ).start()


    for ev_id in range(1, TOTAL_EVS + 1):
        threading.Thread(
            target=charge_ev,
            args=(ev_id,),
            daemon=True
        ).start()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    start_simulation()
    return jsonify({"message": "Simulation started"})


@app.route("/api/status")
def get_status():
    with lock:
        active = sum(
            1 for c in chargers
            if c["status"] == "Charging"
        )

        return jsonify({
            "total_chargers": TOTAL_CHARGERS,
            "occupied": active,
            "available": TOTAL_CHARGERS - active,
            "waiting": len(waiting),
            "completed": len(completed),
            "total_evs": TOTAL_EVS,
            "chargers": [dict(c) for c in chargers],
            "waiting_vehicles": list(waiting),
            "completed_vehicles": list(completed),
            "started": started,
            "finished": finished
        })


if __name__ == "__main__":
    app.run(debug=False, port=5000)
