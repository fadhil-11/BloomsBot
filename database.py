"""
Database operations for BLOOMS BOT
Handles SQLite database creation and CRUD operations
"""

import sqlite3
from datetime import datetime

DB_NAME = 'blooms.db'

def get_connection():
    """Create and return database connection"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Documents table - stores uploaded PDFs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            document_type TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Questions table - stores generated questions with classifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            unit TEXT NOT NULL,
            question TEXT NOT NULL,
            marks INTEGER NOT NULL,
            bloom_level TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def save_document(filename, document_type, extracted_text):
    """Save uploaded document to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO documents (filename, document_type, extracted_text)
        VALUES (?, ?, ?)
    ''', (filename, document_type, extracted_text))
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return doc_id


def get_document(doc_id):
    """Retrieve document by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    doc = cursor.fetchone()
    conn.close()
    
    return dict(doc) if doc else None


def save_questions(questions):
    """Save multiple questions to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    for q in questions:
        cursor.execute('''
            INSERT INTO questions (document_id, unit, question, marks, bloom_level, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (q['document_id'], q['unit'], q['question'], q['marks'], 
              q['bloom_level'], q['difficulty']))
    
    conn.commit()
    conn.close()


def get_questions_by_filters(unit=None, bloom_level=None, difficulty=None, marks=None):
    """
    Retrieve questions based on filters
    If no filters provided, returns all questions
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM questions WHERE 1=1'
    params = []
    
    if unit:
        query += ' AND unit = ?'
        params.append(unit)
    
    if bloom_level:
        query += ' AND bloom_level = ?'
        params.append(bloom_level)
    
    if difficulty:
        query += ' AND difficulty = ?'
        params.append(difficulty)
    
    if marks:
        query += ' AND marks = ?'
        params.append(marks)
    
    cursor.execute(query, params)
    questions = cursor.fetchall()
    conn.close()
    
    return [dict(q) for q in questions]


def get_question_by_id(question_id):
    """Retrieve a single question by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
    question = cursor.fetchone()
    conn.close()
    
    return dict(question) if question else None


def delete_question(question_id):
    """Delete a question from database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()


def clear_all_data():
    """Clear all data from database (for reset functionality)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM questions')
    cursor.execute('DELETE FROM documents')
    conn.commit()
    conn.close()


def get_statistics():
    """Get overall statistics about questions in database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total questions
    cursor.execute('SELECT COUNT(*) as total FROM questions')
    stats['total_questions'] = cursor.fetchone()['total']
    
    # Questions by unit
    cursor.execute('SELECT unit, COUNT(*) as count FROM questions GROUP BY unit')
    stats['by_unit'] = {row['unit']: row['count'] for row in cursor.fetchall()}
    
    # Questions by Bloom's level
    cursor.execute('SELECT bloom_level, COUNT(*) as count FROM questions GROUP BY bloom_level')
    stats['by_bloom'] = {row['bloom_level']: row['count'] for row in cursor.fetchall()}
    
    # Questions by difficulty
    cursor.execute('SELECT difficulty, COUNT(*) as count FROM questions GROUP BY difficulty')
    stats['by_difficulty'] = {row['difficulty']: row['count'] for row in cursor.fetchall()}
    
    # Questions by marks
    cursor.execute('SELECT marks, COUNT(*) as count FROM questions GROUP BY marks')
    stats['by_marks'] = {row['marks']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    return stats
