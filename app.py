import os
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from patterns.grb_tester import light_tree

app = Flask(__name__)
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV   = os.path.join(BASE_DIR, 'coordinates.csv')
PATTERNS_DIR = os.path.join(BASE_DIR, 'patterns')

task_process = None
grb_thread   = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_grb_test', methods=['POST'])
def run_grb_test():
    global grb_thread
    if grb_thread and grb_thread.is_alive():
        return jsonify({'status': 'GRB test already running'}), 409
    try:
        g        = int(request.form['g'])
        r        = int(request.form['r'])
        b        = int(request.form['b'])
        gamma    = float(request.form.get('gamma', 2.2))
        duration = float(request.form.get('duration', 10.0))
    except ValueError:
        return jsonify({'status': 'Invalid GRB input'}), 400
    def grb_task():
        light_tree((g, r, b), csv_file=COORDS_CSV, duration=duration, gamma=gamma)
    grb_thread = threading.Thread(target=grb_task, daemon=True)
    grb_thread.start()
    return redirect(url_for('index'))

def _start_pattern(cmd):
    global task_process
    if task_process:
        task_process.terminate()
    task_process = subprocess.Popen(cmd)

@app.route('/run_compass', methods=['POST'])
def run_compass():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'compass_rose.py'),
        '--num-slices', request.form['num_slices'],
        '--width', request.form['width'],
        '--rps', request.form['rps'],
        '--interval', request.form['interval'],
        '--color', request.form['g_comp'], request.form['r_comp'], request.form['b_comp']
    ]
    if request.form.get('reverse'):
        cmd.append('--reverse')
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_voronoi', methods=['POST'])
def run_voronoi():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'voronoi_bloom.py'),
        '--num-seeds', request.form['num_seeds'],
        '--interval', request.form['interval_v'],
        '--change-interval', request.form['change_interval'],
        '--transition', request.form['transition']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_platonic', methods=['POST'])
def run_platonic():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'rotating_platonic.py'),
        '--shape', request.form['shape'],
        '--interval', request.form['interval_p'],
        '--speed', request.form['speed'],
        '--threshold', request.form['threshold'],
        '--vertex-color', request.form['g_vert'], request.form['r_vert'], request.form['b_vert'],
        '--edge-color', request.form['g_edge'], request.form['r_edge'], request.form['b_edge']
    ]
    if request.form.get('show_edges'):
        cmd.append('--show-edges')
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_twister', methods=['POST'])
def run_twister():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'twister.py'),
        '--interval', request.form['interval_t'],
        '--rotations-per-sec', request.form['rps_t'],
        '--turns', request.form['turns_t'],
        '--range', request.form['z_range']
    ]
    if request.form.get('reverse_t'):
        cmd.append('--reverse')
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_snake', methods=['POST'])
def run_snake():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'snake.py'),
        '--num-snakes', request.form['num_snakes'],
        '--length', request.form['length'],
        '--delay', request.form['delay'],
        '--neighbors', request.form['neighbors'],
        '--min-bright', request.form['min_bright'],
        '--max-bright', request.form['max_bright']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_random_plane', methods=['POST'])
def run_random_plane():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'random_plane.py'),
        '--interval', request.form['interval_plane'],
        '--plane-speed', request.form['plane_speed'],
        '--thickness-factor', request.form['thickness']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_contagious', methods=['POST'])
def run_contagious():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'covid.py'),
        '--interval', request.form['interval_c'],
        '--contagion-speed', request.form['speed_c'],
        '--hold-time', request.form['hold_time']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_pulse', methods=['POST'])
def run_pulse():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'pulse.py'),
        '--center', request.form.get('center', ''),
        '--interval', request.form['interval_pulse'],
        '--speed', request.form['speed_pulse'],
        '--thickness', request.form['thickness_pulse'],
        '--color', request.form['r_pulse'], request.form['g_pulse'], request.form['b_pulse']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_fireworks', methods=['POST'])
def run_fireworks():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'fireworks.py'),
        '--interval', request.form['fw_interval'],
        '--firework-duration', request.form['fw_duration'],
        '--spawn-chance', request.form['fw_spawn'],
        '--blast-radius-factor', request.form['fw_radius']
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))
    
@app.route('/run_helix', methods=['POST'])
def run_helix():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'helix.py'),
        '--interval',      request.form['interval_h'],
        '--rps',           request.form['rps_h'],
        '--turns',         request.form['turns_h'],
        '--color1',        request.form['r1_h'], request.form['g1_h'], request.form['b1_h'],
        '--color2',        request.form['r2_h'], request.form['g2_h'], request.form['b2_h']
    ]
    if request.form.get('reverse_h'):
        cmd.append('--reverse')
    cmd.extend(['--range', request.form['z_range_h']])
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/run_heartbeat', methods=['POST'])
def run_heartbeat():
    cmd = [
        'python3', os.path.join(PATTERNS_DIR, 'heartbeat.py'),
        '--period',        request.form.get('period', '1.0'),
        '--min-intensity', request.form.get('min_int', '20'),
        '--max-intensity', request.form.get('max_int', '255'),
        '--frame-delay',   request.form.get('frame_delay', '0.02'),
    ]
    _start_pattern(cmd)
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    global task_process, grb_thread
    if task_process:
        task_process.terminate()
        task_process = None
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
