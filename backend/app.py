import random
import threading

from flask import Flask, jsonify, request
from flask_cors import CORS

from scanner import cleanup, clone_repo, scan_for_dead_code

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# Eulogy templates
# ---------------------------------------------------------------------------

_OPENINGS = [
    "Friends, colleagues, and fellow developers — we are gathered here today",
    "Dearly beloved, we are assembled in this solemn repository",
    "We come together in grief and in git blame",
    "It is with heavy hearts and empty call stacks that we gather",
    "Let us bow our heads and close our IDEs for a moment",
]

_DEEDS = {
    "function": [
        "who executed faithfully — if only once, or perhaps never at all.",
        "who stood ready at every compile, yet was never truly called upon.",
        "whose body was full of logic, but whose name was never invoked.",
        "who asked for arguments and received only silence.",
    ],
    "variable": [
        "who held a value close to their heart, a value no one ever read.",
        "who was assigned with such hope, yet referenced by none.",
        "who sat on the stack, waiting patiently for a purpose that never came.",
        "whose value was set in stone — and then promptly ignored.",
    ],
    "class": [
        "who was instantiated in spirit but never in practice.",
        "whose methods were many, whose callers were zero.",
        "who designed a beautiful interface that the world never used.",
        "who inherited everything, and passed it on to no one.",
    ],
    "import": [
        "who was brought into scope with such enthusiasm, then never spoken of again.",
        "who crossed module boundaries only to be forgotten at the door.",
        "whose symbols were imported but whose presence was never felt.",
    ],
    "attribute": [
        "who lived on an object no one touched.",
        "who was set with care and read with never.",
        "who belonged to a class that had better things to worry about.",
    ],
}

_BLAME = [
    "We do not ask why they were written. We know why — a deadline loomed.",
    "They were born of a TODO that became a NEVER.",
    "Perhaps they were ahead of their time. Or perhaps the time simply passed.",
    "A refactor was promised. The refactor never came.",
    "They survived three pull requests, two code reviews, and one very tired Friday.",
    "Git log shows they were committed at 11:47 PM. Say no more.",
    "They were marked for deletion once. The branch was abandoned. Life went on.",
]

_CLOSINGS = [
    "May they find purpose in the great /dev/null beyond.",
    "Rest easy. The linter cannot reach you there.",
    "Gone but not forgotten — mostly forgotten, but still.",
    "May your memory be garbage collected peacefully.",
    "You will not be missed by the runtime, but you will be missed by us.",
    "Fly free, uncalled function. Fly free.",
    "In the end, we are all just dead code waiting to be discovered.",
]


def _build_eulogy(name: str, typ: str, filename: str, line: int) -> str:
    opening = random.choice(_OPENINGS)
    deeds_pool = _DEEDS.get(typ, _DEEDS["function"])
    deed = random.choice(deeds_pool)
    blame = random.choice(_BLAME)
    closing = random.choice(_CLOSINGS)

    return (
        f"{opening} to mourn the passing of `{name}` — "
        f"a {typ} of {filename}, line {line} — "
        f"{deed} "
        f"{blame} "
        f"{closing}"
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    messages = [
        "All systems alive. Unlike your code.",
        "Heartbeat detected. More than we can say for your unused functions.",
        "Server is up. Your dead code, however, is not.",
        "Operational. Currently accepting bodies.",
        "Running on port 5001. Accepting the deceased since today.",
    ]
    return jsonify({"status": "ok", "message": random.choice(messages)})


@app.route("/analyze", methods=["POST"])
def analyze():
    body = request.get_json(silent=True) or {}
    github_url = (body.get("github_url") or "").strip()

    if not github_url:
        return jsonify({"error": "github_url is required"}), 400

    repo_path = None
    try:
        repo_path = clone_repo(github_url)
        dead_code = scan_for_dead_code(repo_path)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if repo_path:
            # Clean up in a background thread so the response isn't delayed
            threading.Thread(target=cleanup, args=(repo_path,), daemon=True).start()

    return jsonify({"total": len(dead_code), "results": dead_code})


@app.route("/eulogize", methods=["POST"])
def eulogize():
    body = request.get_json(silent=True) or {}

    name = (body.get("name") or "").strip()
    typ = (body.get("type") or "function").strip()
    filename = (body.get("filename") or "unknown file").strip()
    line = body.get("line", 0)

    if not name:
        return jsonify({"error": "name is required"}), 400

    eulogy = _build_eulogy(name, typ, filename, line)
    return jsonify({"eulogy": eulogy, "name": name, "type": typ, "filename": filename, "line": line})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(port=5001, debug=True)
