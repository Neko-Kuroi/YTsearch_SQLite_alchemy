# app.py
from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_from_directory
import secrets
import threading
import os
import shutil

# Import the scraper function
from scraper import run_scrape

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Required for Flask sessions

# --- Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # User submitted the search form
        keywords = request.form['keywords']
        if not keywords:
            return redirect(url_for('index'))

        # Create a unique ID for this job/session
        session['session_id'] = secrets.token_urlsafe(16)

        # Start the scraper in a background thread
        scrape_thread = threading.Thread(
            target=run_scrape,
            args=(keywords, session['session_id'])
        )
        scrape_thread.start()

        # Redirect to the results page where the user will wait
        return redirect(url_for('results'))

    # If GET, just show the main page
    return render_template('index.html')


@app.route('/results')
def results():
    if 'session_id' not in session:
        return redirect(url_for('index'))
    return render_template('results.html')


@app.route('/status')
def status():
    """An API endpoint for the front-end to poll for updates."""
    if 'session_id' not in session:
        return jsonify({'status': 'error', 'message': 'No session'})

    session_id = session['session_id']
    temp_dir = f"removefolder/{session_id}"
    
    # Check if the completion file exists
    if os.path.exists(f"{temp_dir}/_complete"):
        # Find the result files to offer for download
        files = [f for f in os.listdir(temp_dir) if not f.startswith('_')]
        return jsonify({'status': 'complete', 'files': files})
    else:
        return jsonify({'status': 'running'})


@app.route('/download/<path:filename>')
def download(filename):
    if 'session_id' not in session:
        return redirect(url_for('index'))
    
    session_id = session['session_id']
    directory = os.path.join(os.getcwd(), 'removefolder', session_id)
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/cancel')
def cancel():
    if 'session_id' in session:
        session_id = session['session_id']
        temp_dir = f"removefolder/{session_id}"
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir) # Clean up the folder
        session.clear() # Clear the user's session
    return redirect(url_for('index'))


if __name__ == '__main__':
    # On production, use a proper web server like Gunicorn or Waitress
    app.run(debug=True)
