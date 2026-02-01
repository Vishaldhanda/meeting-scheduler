from flask import Flask, render_template, request
import sqlite3
from collections import Counter

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect("meetings.db")
    conn.row_factory = sqlite3.Row
    return conn

conn = get_db_connection()
conn.execute("""
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participants TEXT,
    time_slot TEXT
)
""")
conn.commit()
conn.close()

availability = {
    "Alice": ["10-11", "2-3", "4-5"],
    "Bob": ["10-11", "3-4"],
    "Charlie": ["10-11", "1-2"]
}

def schedule_meeting(selected_people):
    common_slots = set(availability[selected_people[0]])
    for person in selected_people:
        common_slots &= set(availability[person])
    return sorted(common_slots)[0] if common_slots else None

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        participants = request.form.getlist("participants")
        if participants:
            slot = schedule_meeting(participants)
            if slot:
                result = f"Meeting scheduled at {slot}"
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO meetings (participants, time_slot) VALUES (?, ?)",
                    (", ".join(participants), slot)
                )
                conn.commit()
                conn.close()
            else:
                result = "No common time available"
        else:
            result = "Please select participants"

    conn = get_db_connection()
    meetings = conn.execute("SELECT * FROM meetings").fetchall()
    conn.close()

    total_meetings = len(meetings)
    time_slots = [m["time_slot"] for m in meetings]
    most_common_time = Counter(time_slots).most_common(1)
    most_common_time = most_common_time[0][0] if most_common_time else "N/A"

    person_count = Counter()
    for m in meetings:
        for p in m["participants"].split(", "):
            person_count[p] += 1

    return render_template(
        "index.html",
        people=availability.keys(),
        result=result,
        meetings=meetings,
        total_meetings=total_meetings,
        common_time=most_common_time,
        person_count=person_count
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
