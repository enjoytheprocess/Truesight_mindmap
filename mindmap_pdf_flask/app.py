# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from pdfminer.high_level import extract_text
from werkzeug.utils import secure_filename
import os

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
            text = extract_text(filepath)
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

if __name__ == '__main__':
    app.run(debug=True)
