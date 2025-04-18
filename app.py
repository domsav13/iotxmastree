The following project structure and code set up a Flask web interface to control your `music/mariah.py` script and any pattern scripts in `patterns/`:

**Project Structure**:
```
/ (project root)
├── app.py            # Flask application
├── music/
│   ├── mariah.py     # Music script
│   └── ...           # other music assets
├── patterns/
│   ├── spirals.py    # Example pattern scripts
│   └── ...
└── templates/
    └── index.html    # Main UI template
```

---
# app.py
```python
import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, 'music')
PATTERNS_DIR = os.path.join(BASE_DIR, 'patterns')

# Keep track of running process
running_process = None

@app.route('/')
def index():
    # List available Python scripts in music and patterns
    music_scripts = [f for f in os.listdir(MUSIC_DIR) if f.endswith('.py')]
    pattern_scripts = [f for f in os.listdir(PATTERNS_DIR) if f.endswith('.py')]
    return render_template('index.html', music_scripts=music_scripts, pattern_scripts=pattern_scripts)

@app.route('/run_music', methods=['POST'])
def run_music():
    global running_process
    # Stop any existing process
    if running_process:
        running_process.terminate()
    # Get selected script and optional args
    script = request.form['music_script']
    args = request.form.get('args', '').split()
    cmd = ['python3', os.path.join(MUSIC_DIR, script)] + args
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/run_pattern', methods=['POST'])
def run_pattern():
    global running_process
    if running_process:
        running_process.terminate()
    script = request.form['pattern_script']
    cmd = ['python3', os.path.join(PATTERNS_DIR, script)]
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global running_process
    if running_process:
        running_process.terminate()
        running_process = None
    return redirect(url_for('index'))

from flask import jsonify
from real_time_show import start_realtime_show, animate_from_csv

led_thread = None

@app.route('/run_really_love', methods=['POST'])
def run_really_love():
    global led_thread
    if led_thread and led_thread.is_alive():
        return jsonify({"status": "Show already running"})
    led_thread = start_realtime_show()
    return jsonify({"status": "Really Love light show started"})

if __name__ == '__main__':
    # Accessible on your local network if needed
    app.run(host='0.0.0.0', port=5000, debug=True)
```

---
# templates/index.html
```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IoT Xmas Tree Control</title>
</head>
<body>
  <h1>Music Control</h1>
  <form action="/run_music" method="post">
    <label for="music_script">Choose script:</label>
    <select name="music_script" id="music_script">
      {% for script in music_scripts %}
      <option value="{{ script }}">{{ script }}</option>
      {% endfor %}
    </select>
    <input type="text" name="args" placeholder="Optional args" />
    <button type="submit">Play</button>
  </form>

  <h1>Pattern Control</h1>
  <form action="/run_pattern" method="post">
    <label for="pattern_script">Choose pattern:</label>
    <select name="pattern_script" id="pattern_script">
      {% for script in pattern_scripts %}
      <option value="{{ script }}">{{ script }}</option>
      {% endfor %}
    </select>
    <button type="submit">Run Pattern</button>
  </form>

  <h1>Stop</h1>
  <form action="/stop" method="post">
    <button type="submit">Stop All</button>
  </form>
</body>
</html>
