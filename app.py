import os
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from patterns.grb_tester import light_tree

app = Flask(__name__)
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV    = os.path.join(BASE_DIR, 'coordinates.csv')
PATTERNS_DIR  = os.path.join(BASE_DIR, 'patterns')

# Globals for managing running tasks
running_process = None
grb_thread      = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_grb_test', methods=['POST'])
def run_grb_test():
    global grb_thread
    if grb_thread and grb_thread.is_alive():
        return jsonify({'status': 'A GRB test is already running'}), 409
    try:
        g        = int(request.form['g'])
        r        = int(request.form['r'])
        b        = int(request.form['b'])
        gamma    = float(request.form.get('gamma', 2.2))
        duration = float(request.form.get('duration', 10.0))
    except ValueError:
        return jsonify({'status': 'Invalid GRB input'}), 400
    def grb_target():
        light_tree((g, r, b), csv_file=COORDS_CSV, duration=duration, gamma=gamma)
    grb_thread = threading.Thread(target=grb_target, daemon=True)
    grb_thread.start()
    return redirect(url_for('index'))

@app.route('/run_compass', methods=['POST'])
def run_compass():
    global running_process
    if running_process:
        running_process.terminate()
    # Parse form inputs
    num_slices     = request.form['num_slices']
    width          = request.form['width']
    rps            = request.form.get('rps', '0.2')
    interval       = request.form.get('interval', '0.05')
    g_comp, r_comp, b_comp = request.form['g_comp'], request.form['r_comp'], request.form['b_comp']
    reverse        = request.form.get('reverse')
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'compass_rose.py'),
        '--num-slices', num_slices,
        '--width', width,
        '--rps', rps,
        '--interval', interval,
        '--color', g_comp, r_comp, b_comp
    ]
    if reverse:
        cmd.append('--reverse')
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/run_voronoi', methods=['POST'])
def run_voronoi():
    global running_process
    if running_process:
        running_process.terminate()
    # Parse form inputs
    num_seeds      = request.form['num_seeds']
    interval       = request.form.get('interval', '0.1')
    change_interval= request.form.get('change_interval', '10.0')
    transition     = request.form.get('transition', '2.0')
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'voronoi_bloom.py'),
        '--num-seeds', num_seeds,
        '--interval', interval,
        '--change-interval', change_interval,
        '--transition', transition
    ]
    running_process = subprocess.Popen(cmd)
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global running_process, grb_thread
    if running_process:
        running_process.terminate()
        running_process = None
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
