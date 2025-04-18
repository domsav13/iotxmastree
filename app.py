# app.py

import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for
from real_time_show import start_realtime_show

app = Flask(__name__)
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR    = os.path.join(BASE_DIR, 'music')
PATTERNS_DIR = os.path.join(BASE_DIR, 'patterns')

running_process = None
led_thread      = None

@app.route('/')
def index():
    music_scripts   = [f for f in os.listdir(MUSIC_DIR) if f.endswith('.py')]
    pattern_scripts = [f for f in os.listdir(PATTERNS_DIR) if f.endswith('.py')]
    return render_template('index.html',
                           music_scripts=music_scripts,
                           pattern_scripts=pattern_scripts)

@app.route('/run_music', methods=['POST'])
def run_music():
    global running_process
    if running_process:
        running_process.terminate()
    script = request.form['music_script']
    args   = request.form.get('args', '').split()
    cmd    = ['python3', os.path.join(MUSIC_DIR, script)] + args
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/run_pattern', methods=['POST'])
def run_pattern():
    global running_process
    if running_process:
        running_process.terminate()
    script = request.form['pattern_script']
    cmd    = ['python3', os.path.join(PATTERNS_DIR, script)]
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/run_really_love', methods=['POST'])
def run_really_love():
    global running_process, led_thread
    # stop any existing subprocess
    if running_process:
        running_process.terminate()
    # start the realtime light show thread
    if not (led_thread and led_thread.is_alive()):
        led_thread = start_realtime_show()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global running_process, led_thread
    if running_process:
        running_process.terminate()
        running_process = None
    # Note: the light‐show thread will naturally exit when its loop completes
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
