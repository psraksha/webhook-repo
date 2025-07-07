from flask import Flask, request, render_template, jsonify
from datetime import datetime
from app.extensions import mongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/database"
mongo.init_app(app)
db = mongo.db

@app.route('/')
def api_root():
    events = list(db.events.find().sort("timestamp", -1).limit(10))
    print("fetched events: ",events)
    for event in events:
        event['timestamp'] = event['timestamp'].strftime("%d %b %Y - %I:%M %p UTC")
    return render_template('index.html', events=events)

@app.route('/github', methods=['POST'])
def api_gh_message():
    data = request.json
    event = request.headers.get('X-GitHub-Event')  # Custom header name
    event_info = {}

    if event == 'push':
        is_merge_commit=False
        if 'head_commit' in data and len(data['head_commit'].get('parents', [])) > 1:
            is_merge_commit = True
        event_info = {
            "event": "push",
            "pusher": data["pusher"]["name"],
            "to_branch": data["ref"].split("/")[-1],
            "is_merge": is_merge_commit,
            "timestamp": datetime.utcnow()
        }
    elif event == 'pull_request':
        pr = data["pull_request"]
        event_info = {
            "event": "pull_request",
            "author": pr["user"]["login"],
            "from_branch": pr["head"]["ref"],
            "to_branch": pr["base"]["ref"],
            "timestamp": datetime.utcnow()
        }

    if event_info:
        db.events.insert_one(event_info)
        return jsonify({"status": "event saved"}), 200
    else:
        return jsonify({"status": "unsupported or missing event"}), 400

if __name__ == '__main__':
    app.run(debug=True)
