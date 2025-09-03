from flask import Flask, request, render_template, jsonify, redirect, url_for
from collections import defaultdict
from bs4 import BeautifulSoup
from flask_cors import CORS
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory data
overall_leaderboard = []
class_leaderboards = {}
history = []  # snapshots

def compute_leaderboards_from_entries(entries):
    overall_map = {}
    class_map = defaultdict(dict)
    for e in entries:
        name = e.get("name")
        try:
            grade = float(e.get("grade", 0))
        except:
            continue
        weight = float(e.get("weight", 1))
        cls = e.get("class", "General")
        if name not in overall_map:
            overall_map[name] = {"total": 0.0, "weight_sum": 0.0}
        overall_map[name]["total"] += grade * weight
        overall_map[name]["weight_sum"] += weight
        if name not in class_map[cls]:
            class_map[cls][name] = {"total": 0.0, "weight_sum": 0.0}
        class_map[cls][name]["total"] += grade * weight
        class_map[cls][name]["weight_sum"] += weight

    overall = [{"name": name, "gpa": round(v["total"] / v["weight_sum"], 2)} for name, v in overall_map.items()]
    overall.sort(key=lambda x: x["gpa"], reverse=True)

    classes = {}
    for cls, students in class_map.items():
        lst = [{"name": name, "gpa": round(v["total"] / v["weight_sum"], 2)} for name, v in students.items()]
        lst.sort(key=lambda x: x["gpa"], reverse=True)
        classes[cls] = lst

    return overall, classes

def rank_changes(new_list, prev_list):
    prev_ranks = {s['name']: i for i, s in enumerate(prev_list)} if prev_list else {}
    return {s['name']: (prev_ranks.get(s['name'], i) - i) for i, s in enumerate(new_list)}

def compute_trend_for_name(name, snap_list, cls=None):
    relevant = snap_list[-3:] if len(snap_list) >= 3 else snap_list
    vals = []
    for snap in relevant:
        lst = snap['classes'].get(cls, []) if cls else snap['overall']
        for s in lst:
            if s['name'] == name:
                vals.append(s['gpa'])
                break
    return round(vals[-1] - vals[0], 2) if len(vals) >= 2 else 0.0

@app.route("/")
def home():
    latest = history[-1] if history else None
    class_list = list(latest['classes'].keys()) if latest else []
    return render_template("index.html", latest=latest, history=history, class_list=class_list)

@app.route("/update", methods=["POST"])
def update():
    global overall_leaderboard, class_leaderboards, history
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, list):
        return jsonify({"error": "Expected a list of grade entries"}), 400

    overall, classes = compute_leaderboards_from_entries(data)
    prev_overall = history[-1]['overall'] if history else []
    prev_classes = history[-1]['classes'] if history else {}

    overall_changes = rank_changes(overall, prev_overall)
    class_changes = {cls: rank_changes(lst, prev_classes.get(cls, [])) for cls, lst in classes.items()}

    snapshot = {"overall": overall, "classes": classes, "overall_changes": overall_changes, "class_changes": class_changes}

    temp_history = history + [snapshot]
    snapshot['overall_trends'] = {s['name']: compute_trend_for_name(s['name'], temp_history) for s in overall}
    snapshot['class_trends'] = {cls: {s['name']: compute_trend_for_name(s['name'], temp_history, cls) for s in lst} for cls, lst in classes.items()}

    history.append(snapshot)
    if len(history) > 10:
        history.pop(0)

    overall_leaderboard = overall
    class_leaderboards = classes

    return jsonify({"status": "success"}), 200

@app.route("/upload", methods=["POST"])
def upload_html():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    html = file.read()
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return jsonify({"error": "No table found in uploaded HTML"}), 400
    entries = []
    for row in table.find_all("tr")[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) >= 2:
            name = cells[0].get_text(strip=True)
            try:
                grade = float(cells[1].get_text(strip=True))
            except:
                continue
            weight = float(cells[2].get_text(strip=True)) if len(cells) > 2 else 1.0
            cls = cells[3].get_text(strip=True) if len(cells) > 3 else "General"
            entries.append({"name": name, "grade": grade, "weight": weight, "class": cls})

    # Build leaderboard directly without internal test_request_context
    overall, classes = compute_leaderboards_from_entries(entries)
    prev_overall = history[-1]['overall'] if history else []
    prev_classes = history[-1]['classes'] if history else {}
    overall_changes = rank_changes(overall, prev_overall)
    class_changes = {cls: rank_changes(lst, prev_classes.get(cls, [])) for cls, lst in classes.items()}
    snapshot = {"overall": overall, "classes": classes, "overall_changes": overall_changes, "class_changes": class_changes}
    temp_history = history + [snapshot]
    snapshot['overall_trends'] = {s['name']: compute_trend_for_name(s['name'], temp_history) for s in overall}
    snapshot['class_trends'] = {cls: {s['name']: compute_trend_for_name(s['name'], temp_history, cls) for s in lst} for cls, lst in classes.items()}
    history.append(snapshot)
    if len(history) > 10:
        history.pop(0)

    return redirect(url_for('home'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
