import os
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from patterns.grb_tester import light_tree

app = Flask(__name__)
# Path to CSV (can be adjusted if needed)
COORDS_CSV = os.path.join(os.path.dirname(__file__), 'coordinates.csv')

grb_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_grb_test', methods=['POST'])
def run_grb_test():
    global grb_thread
    # Stop existing test if running
    if grb_thread and grb_thread.is_alive():
        return jsonify({'status': 'A test is already running'}), 409

    # Parse form inputs
    try:
        g = int(request.form['g'])
        r = int(request.form['r'])
        b = int(request.form['b'])
        gamma = float(request.form.get('gamma', 2.2))
        duration = float(request.form.get('duration', 10.0))
    except ValueError:
        return jsonify({'status': 'Invalid input'}), 400

    # Start the light_tree in a background thread
    def target():
        light_tree((g, r, b), csv_file=COORDS_CSV, duration=duration, gamma=gamma)

    grb_thread = threading.Thread(target=target, daemon=True)
    grb_thread.start()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
