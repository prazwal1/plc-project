"""
web/app.py - Flask backend for the online PL compiler.

Run from the project root:
  python web/app.py
Then open http://localhost:5000
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, render_template, request, jsonify
from main import run_source

app = Flask(__name__, template_folder='templates', static_folder='static')

# Load example files once at startup so the frontend can list them.
EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'examples')

def _load_examples() -> dict[str, str]:
    examples = {}
    if os.path.isdir(EXAMPLES_DIR):
        for fname in sorted(os.listdir(EXAMPLES_DIR)):
            if fname.endswith('.pl'):
                with open(os.path.join(EXAMPLES_DIR, fname)) as f:
                    examples[fname] = f.read()
    return examples

EXAMPLES = _load_examples()


@app.route('/')
def index():
    return render_template('index.html', examples=list(EXAMPLES.keys()))


@app.route('/example/<name>')
def get_example(name):
    if name not in EXAMPLES:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'source': EXAMPLES[name]})


@app.route('/run', methods=['POST'])
def run():
    data     = request.get_json(force=True)
    source   = data.get('source', '')
    show_tac = bool(data.get('show_tac', False))

    if not source.strip():
        return jsonify({'output': '', 'error': 'Empty program.'})

    try:
        output = run_source(source, show_tac=show_tac)
        return jsonify({'output': output, 'error': ''})
    except Exception as e:
        return jsonify({'output': '', 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
