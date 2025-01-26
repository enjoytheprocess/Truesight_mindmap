# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from pdfminer.high_level import extract_text, LAParams
from werkzeug.utils import secure_filename
import os
import Testing2

# Testing 2 imports
import openai
import time
import random
import webbrowser
from pyvis.network import Network

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///explanations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

db = SQLAlchemy(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Explanation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'phrase': self.phrase,
            'text': self.text
        }

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return render_template('upload.html', error="No file part")
        file = request.files['pdf_file']
        if file.filename == '':
            return render_template('upload.html', error="No selected file")
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Extract text from PDF
            custom_params = LAParams()
            custom_params.word_margin = 0.2
            text = extract_text(filepath, laparams=custom_params)

            # ---
            make_mind_map(text)

            # Save extracted text to a file associated with the uploaded PDF
            text_filename = f"{os.path.splitext(filename)[0]}_extracted.txt"
            text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], text_filename)
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            # Store the uploaded filename in the session
            session['uploaded_pdf'] = filename
            session['extracted_text_file'] = text_filename
            return redirect(url_for('viewer'))
        else:
            return render_template('upload.html', error="Invalid file type. Please upload a PDF.")
    return render_template('upload.html')

@app.route('/viewer')
def viewer():
    uploaded_pdf = session.get('uploaded_pdf', None)
    extracted_text_file = session.get('extracted_text_file', None)
    
    if uploaded_pdf and extracted_text_file:
        pdf_url = url_for('static', filename=f"uploads/{uploaded_pdf}")
        text_filepath = os.path.join(app.config['UPLOAD_FOLDER'], extracted_text_file)
        try:
            with open(text_filepath, 'r', encoding='utf-8') as f:
                pdf_text = f.read()
        except FileNotFoundError:
            pdf_text = ""
    else:
        pdf_url = None
        pdf_text = ""
    
    return render_template('viewer.html', pdf_text=pdf_text, pdf_url=pdf_url)

@app.route('/add_explanation', methods=['POST'])
def add_explanation():
    data = request.get_json()
    phrase = data.get('phrase', '').strip()
    text = data.get('explanationText', '').strip()
    if phrase and text:
        explanation = Explanation(phrase=phrase, text=text)
        db.session.add(explanation)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'message': 'Invalid data.'}), 400

@app.route('/get_explanations', methods=['GET'])
def get_explanations():
    explanations = Explanation.query.all()
    return jsonify([exp.to_dict() for exp in explanations])

# @app.template_filter('nl2br')
# def nl2br(value):
#     return value.replace('\n', '\n')

@app.template_filter('escapejs')
def escapejs(value):
    return value.replace("'", "\\'").replace('"', '\\"')

# Optional: Cleanup command to delete uploaded files
import click
from flask.cli import with_appcontext

@app.cli.command('cleanup')
@with_appcontext
def cleanup():
    """Remove all files in the uploads directory."""
    upload_folder = app.config['UPLOAD_FOLDER']
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
                print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def make_mind_map(user_input):
    response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Consider the following text's (given by the user) main topics, brief descriptions of those topics, and connections between the topics. Create for me two outputs in a code block. The first is a dictionary where the keys are the main topic titles and the values are the descriptions. Keep both brief (the title should be a few words, the description should be a few sentences). The second is a list of tuples where each tuple contains two topics, representing the fact that those topics are connected in some way. In the code, AND THIS IS EXTREMELY IMPORTANT, the dictionary should be called 'dict' and the list of tuples should be called 'tup'. Say NOTHING ELSE, IT IS OF VITAL IMPORTANCE THAT YOU SAY NOTHING ELSE."
                },
                {
                    "role": "user",
                    "content": user_input
                }],
        )

    response_text = response.choices[0].message.content
    response_lines = response_text.split('\n')
    dict_start = response_lines.index('```python') + 1
    dict_end = response_lines.index('```', dict_start)
    dict_code = '\n'.join(response_lines[dict_start:dict_end])
    exec(dict_code, globals())

    print("Dictionary:", dict)
    print("List of Tuples:", tup)
    
    # Generate the mind map
    Testing2.make_mind_map(dict, tup)

    # Define the new path in the "uploads" folder
    print(os.getcwd())
    mind_map_folder = os.path.join(os.getcwd(), "static", "mind_map_folder")
    os.makedirs(mind_map_folder, exist_ok=True)  # Ensure the "uploads" folder exists
    mind_map_path = os.path.join(mind_map_folder, "mind_map.html")

    # Wait for mind_map.html to be created (max wait: 10 sec)
    timeout = 10  # Maximum wait time in seconds
    start_time = time.time()

    while not os.path.exists(mind_map_path):
        if time.time() - start_time > timeout:
            return "Error: mind_map.html was not generated in time.", 500
        time.sleep(0.5)  # Check every 500ms

# Serve files from static/uploads
@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    uploads_dir = os.path.join(app.root_path, "static", "uploads")  # Correct uploads path
    return send_from_directory(uploads_dir, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
