"""
BLOOMS BOT - Academic Question Paper Generator
Main Flask Application
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
from werkzeug.utils import secure_filename
import json

# Import custom modules
from database import init_db, save_document, get_document, save_questions, get_questions_by_filters, clear_all_data, get_question_by_id, delete_question
from pdf_processor import extract_text_from_pdf
from question_generator import generate_questions_from_text
from blooms_classifier import classify_question
from paper_generator import generate_paper, export_to_pdf, export_to_text

app = Flask(__name__)
app.secret_key = 'blooms_bot_secret_key_2024'  # Change in production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXPORT_FOLDER'] = 'exports'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXPORT_FOLDER'], exist_ok=True)

# Initialize database
init_db()

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/')
def index():
    """Home page - Upload PDF"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF upload and processing"""
    if 'pdf_file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('index'))
    
    file = request.files['pdf_file']
    document_type = request.form.get('document_type', 'syllabus')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Extract text from PDF
            flash('Processing PDF...', 'info')
            extracted_text = extract_text_from_pdf(filepath)
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                flash('Could not extract sufficient text from PDF. Please ensure the PDF contains readable text.', 'error')
                os.remove(filepath)
                return redirect(url_for('index'))
            
            # Save document to database
            doc_id = save_document(filename, document_type, extracted_text)
            
            # Generate questions from extracted text
            flash('Generating questions...', 'info')
            questions = generate_questions_from_text(extracted_text, document_type)
            
            if not questions:
                flash('Could not generate questions from the document.', 'error')
                return redirect(url_for('index'))
            
            # Classify and save questions
            flash('Classifying questions using Bloom\'s Taxonomy...', 'info')
            classified_questions = []
            for q in questions:
                classification = classify_question(q['question'], q['marks'])
                classified_questions.append({
                    'document_id': doc_id,
                    'unit': q['unit'],
                    'question': q['question'],
                    'marks': q['marks'],
                    'bloom_level': classification['bloom_level'],
                    'difficulty': classification['difficulty']
                })
            
            save_questions(classified_questions)
            
            flash(f'Successfully processed {filename}! Generated {len(classified_questions)} questions.', 'success')
            return redirect(url_for('generate'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload a PDF.', 'error')
    return redirect(url_for('index'))


@app.route('/generate')
def generate():
    """Question paper generation page"""
    # Get all available questions for preview
    questions = get_questions_by_filters()
    
    if not questions:
        flash('No questions available. Please upload a document first.', 'warning')
        return redirect(url_for('index'))
    
    # Calculate available units
    units = list(set([q['unit'] for q in questions]))
    units.sort()
    
    return render_template('generate.html', units=units, total_questions=len(questions))


@app.route('/create_paper', methods=['POST'])
def create_paper():
    """Generate question paper based on constraints"""
    try:
        # Parse form data
        total_marks = int(request.form.get('total_marks', 100))
        num_questions = int(request.form.get('num_questions', 10))
        
        # Parse unit distribution
        unit_distribution = {}
        for key in request.form:
            if key.startswith('unit_'):
                unit_num = key.replace('unit_', '')
                marks = int(request.form.get(key, 0))
                if marks > 0:
                    unit_distribution[unit_num] = marks
        
        # Parse Bloom's distribution
        bloom_distribution = {}
        for key in request.form:
            if key.startswith('bloom_'):
                level = key.replace('bloom_', '').capitalize()
                percentage = int(request.form.get(key, 0))
                if percentage > 0:
                    bloom_distribution[level] = percentage
        
        # Generate paper
        selected_questions = generate_paper(
            total_marks=total_marks,
            num_questions=num_questions,
            unit_distribution=unit_distribution,
            bloom_distribution=bloom_distribution
        )
        
        if not selected_questions:
            flash('Could not generate a paper with the given constraints. Try relaxing some requirements.', 'error')
            return redirect(url_for('generate'))
        
        # Store selected questions in session-like manner (using JSON file for simplicity)
        session_file = os.path.join(app.config['EXPORT_FOLDER'], 'current_paper.json')
        with open(session_file, 'w') as f:
            json.dump(selected_questions, f)
        
        flash(f'Successfully generated question paper with {len(selected_questions)} questions!', 'success')
        return redirect(url_for('review'))
        
    except Exception as e:
        flash(f'Error generating paper: {str(e)}', 'error')
        return redirect(url_for('generate'))


@app.route('/review')
def review():
    """Review and edit generated paper"""
    session_file = os.path.join(app.config['EXPORT_FOLDER'], 'current_paper.json')
    
    if not os.path.exists(session_file):
        flash('No paper generated yet.', 'warning')
        return redirect(url_for('generate'))
    
    with open(session_file, 'r') as f:
        paper_questions = json.load(f)
    
    # Calculate statistics
    total_marks = sum([q['marks'] for q in paper_questions])
    bloom_stats = {}
    difficulty_stats = {}
    
    for q in paper_questions:
        bloom_stats[q['bloom_level']] = bloom_stats.get(q['bloom_level'], 0) + 1
        difficulty_stats[q['difficulty']] = difficulty_stats.get(q['difficulty'], 0) + 1
    
    return render_template('review.html', 
                         questions=paper_questions,
                         total_marks=total_marks,
                         bloom_stats=bloom_stats,
                         difficulty_stats=difficulty_stats)


@app.route('/replace_question/<int:question_id>', methods=['POST'])
def replace_question(question_id):
    """Replace a question with another from same category"""
    session_file = os.path.join(app.config['EXPORT_FOLDER'], 'current_paper.json')
    
    with open(session_file, 'r') as f:
        paper_questions = json.load(f)
    
    # Find the question to replace
    question_to_replace = None
    for q in paper_questions:
        if q['id'] == question_id:
            question_to_replace = q
            break
    
    if not question_to_replace:
        return jsonify({'error': 'Question not found'}), 404
    
    # Get alternative questions with same criteria
    alternatives = get_questions_by_filters(
        unit=question_to_replace['unit'],
        bloom_level=question_to_replace['bloom_level'],
        marks=question_to_replace['marks']
    )
    
    # Filter out already selected questions
    selected_ids = [q['id'] for q in paper_questions]
    alternatives = [q for q in alternatives if q['id'] not in selected_ids]
    
    if not alternatives:
        return jsonify({'error': 'No alternative questions available'}), 400
    
    # Replace with first alternative
    replacement = alternatives[0]
    for i, q in enumerate(paper_questions):
        if q['id'] == question_id:
            paper_questions[i] = replacement
            break
    
    # Save updated paper
    with open(session_file, 'w') as f:
        json.dump(paper_questions, f)
    
    return jsonify({'success': True, 'replacement': replacement})


@app.route('/remove_question/<int:question_id>', methods=['POST'])
def remove_question(question_id):
    """Remove a question from the paper"""
    session_file = os.path.join(app.config['EXPORT_FOLDER'], 'current_paper.json')
    
    with open(session_file, 'r') as f:
        paper_questions = json.load(f)
    
    # Remove question
    paper_questions = [q for q in paper_questions if q['id'] != question_id]
    
    # Save updated paper
    with open(session_file, 'w') as f:
        json.dump(paper_questions, f)
    
    return jsonify({'success': True})


@app.route('/export/<format>')
def export(format):
    """Export question paper as PDF or TXT"""
    session_file = os.path.join(app.config['EXPORT_FOLDER'], 'current_paper.json')
    
    if not os.path.exists(session_file):
        flash('No paper to export.', 'warning')
        return redirect(url_for('generate'))
    
    with open(session_file, 'r') as f:
        paper_questions = json.load(f)
    
    try:
        if format == 'pdf':
            filepath = export_to_pdf(paper_questions, app.config['EXPORT_FOLDER'])
            return send_file(filepath, as_attachment=True, download_name='question_paper.pdf')
        elif format == 'txt':
            filepath = export_to_text(paper_questions, app.config['EXPORT_FOLDER'])
            return send_file(filepath, as_attachment=True, download_name='question_paper.txt')
        else:
            flash('Invalid export format.', 'error')
            return redirect(url_for('review'))
    except Exception as e:
        flash(f'Error exporting paper: {str(e)}', 'error')
        return redirect(url_for('review'))


@app.route('/reset')
def reset():
    """Clear all data and start fresh"""
    clear_all_data()
    
    # Clear upload and export folders
    for folder in [app.config['UPLOAD_FOLDER'], app.config['EXPORT_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
            except:
                pass
    
    flash('All data cleared successfully.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
