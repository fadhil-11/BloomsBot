"""
Question Paper Generator Module for BLOOMS BOT
Assembles question papers based on constraints and exports them
"""

import random
from datetime import datetime
from database import get_questions_by_filters
from fpdf import FPDF


def generate_paper(total_marks, num_questions, unit_distribution, bloom_distribution):
    """
    Generate a question paper based on specified constraints
    
    Args:
        total_marks: Target total marks for the paper
        num_questions: Target number of questions
        unit_distribution: Dict mapping units to their mark allocation
        bloom_distribution: Dict mapping Bloom levels to their percentages
        
    Returns:
        List of selected questions or None if impossible
    """
    # Get all available questions
    all_questions = get_questions_by_filters()
    
    if not all_questions:
        return None
    
    # Calculate target marks per Bloom level
    bloom_targets = {}
    for level, percentage in bloom_distribution.items():
        bloom_targets[level] = (percentage / 100) * total_marks
    
    # Try to select questions meeting all constraints
    selected_questions = []
    remaining_marks = total_marks
    attempts = 0
    max_attempts = 1000
    
    # Group questions by criteria for efficient selection
    questions_by_criteria = organize_questions(all_questions)
    
    # Selection strategy: iteratively pick best-fit questions
    while len(selected_questions) < num_questions and remaining_marks > 0 and attempts < max_attempts:
        attempts += 1
        
        # Find best candidate question
        candidate = find_best_candidate(
            questions_by_criteria,
            selected_questions,
            remaining_marks,
            unit_distribution,
            bloom_targets,
            num_questions - len(selected_questions)
        )
        
        if candidate:
            selected_questions.append(candidate)
            remaining_marks -= candidate['marks']
            
            # Update targets
            if candidate['unit'] in unit_distribution:
                unit_distribution[candidate['unit']] -= candidate['marks']
            if candidate['bloom_level'] in bloom_targets:
                bloom_targets[candidate['bloom_level']] -= candidate['marks']
        else:
            # No suitable candidate found, relax constraints slightly
            break
    
    # Verify we have a reasonable paper
    if len(selected_questions) >= max(3, num_questions * 0.7):
        return selected_questions
    
    # If strict matching failed, try relaxed approach
    return generate_paper_relaxed(all_questions, total_marks, num_questions)


def organize_questions(questions):
    """
    Organize questions by unit, marks, and Bloom's level for efficient lookup
    """
    organized = {}
    
    for q in questions:
        key = (q['unit'], q['marks'], q['bloom_level'])
        if key not in organized:
            organized[key] = []
        organized[key].append(q)
    
    return organized


def find_best_candidate(questions_by_criteria, selected, remaining_marks, 
                       unit_distribution, bloom_targets, remaining_count):
    """
    Find the best question to add next based on current constraints
    """
    selected_ids = [q['id'] for q in selected]
    candidates = []
    
    # Get all available questions
    for key, question_list in questions_by_criteria.items():
        for q in question_list:
            if q['id'] in selected_ids:
                continue
            
            # Check if question fits constraints
            if q['marks'] > remaining_marks:
                continue
            
            # Calculate fitness score
            score = calculate_fitness_score(q, unit_distribution, bloom_targets, remaining_marks)
            candidates.append((score, q))
    
    if not candidates:
        return None
    
    # Sort by fitness score and pick best
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def calculate_fitness_score(question, unit_distribution, bloom_targets, remaining_marks):
    """
    Calculate how well a question fits current needs
    Higher score = better fit
    """
    score = 0
    
    # Prefer questions from units that need more marks
    if question['unit'] in unit_distribution:
        unit_need = unit_distribution[question['unit']]
        if unit_need > 0:
            score += min(10, unit_need / question['marks'])
    
    # Prefer questions from Bloom levels that need more coverage
    if question['bloom_level'] in bloom_targets:
        bloom_need = bloom_targets[question['bloom_level']]
        if bloom_need > 0:
            score += min(10, bloom_need / question['marks'])
    
    # Slightly prefer questions that fit mark allocation better
    mark_fit = 1 - (abs(remaining_marks - question['marks']) / remaining_marks)
    score += mark_fit * 2
    
    return score


def generate_paper_relaxed(questions, target_marks, target_count):
    """
    Generate paper with relaxed constraints (fallback method)
    """
    # Simple approach: try to get close to target marks and count
    questions_sorted = sorted(questions, key=lambda x: x['marks'])
    
    selected = []
    total = 0
    
    # Use greedy approach with randomization
    available = questions.copy()
    random.shuffle(available)
    
    for q in available:
        if len(selected) >= target_count:
            break
        if total + q['marks'] <= target_marks * 1.1:  # Allow 10% overage
            selected.append(q)
            total += q['marks']
    
    return selected if len(selected) >= 3 else None


def export_to_pdf(questions, export_folder):
    """
    Export question paper to PDF format
    
    Args:
        questions: List of questions to export
        export_folder: Folder to save the PDF
        
    Returns:
        Path to generated PDF file
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'EXAMINATION QUESTION PAPER', 0, 1, 'C')
    pdf.ln(5)
    
    # Metadata
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 0, 1)
    pdf.cell(0, 8, f'Total Marks: {sum([q["marks"] for q in questions])}', 0, 1)
    pdf.cell(0, 8, f'Total Questions: {len(questions)}', 0, 1)
    pdf.ln(5)
    
    # Instructions
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Instructions:', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 6, '1. Answer all questions.\n2. Each question carries marks as indicated.\n3. Write clearly and legibly.')
    pdf.ln(5)
    
    # Questions
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Questions:', 0, 1)
    pdf.ln(3)
    
    for idx, q in enumerate(questions, 1):
        # Question number and marks
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, f'Q{idx}. [{q["marks"]} marks] - {q["unit"]}', 0, 1)
        
        # Question text
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, q['question'])
        
        # Metadata (optional, can be commented out)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 5, f'[Bloom\'s Level: {q["bloom_level"]}, Difficulty: {q["difficulty"]}]', 0, 1)
        pdf.ln(3)
    
    # Save PDF
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'question_paper_{timestamp}.pdf'
    filepath = f'{export_folder}/{filename}'
    
    pdf.output(filepath)
    return filepath


def export_to_text(questions, export_folder):
    """
    Export question paper to text format
    
    Args:
        questions: List of questions to export
        export_folder: Folder to save the text file
        
    Returns:
        Path to generated text file
    """
    lines = []
    
    # Header
    lines.append('=' * 70)
    lines.append('EXAMINATION QUESTION PAPER')
    lines.append('=' * 70)
    lines.append('')
    
    # Metadata
    lines.append(f'Generated: {datetime.now().strftime("%B %d, %Y %H:%M")}')
    lines.append(f'Total Marks: {sum([q["marks"] for q in questions])}')
    lines.append(f'Total Questions: {len(questions)}')
    lines.append('')
    
    # Instructions
    lines.append('INSTRUCTIONS:')
    lines.append('-' * 70)
    lines.append('1. Answer all questions.')
    lines.append('2. Each question carries marks as indicated.')
    lines.append('3. Write clearly and legibly.')
    lines.append('')
    
    # Questions
    lines.append('QUESTIONS:')
    lines.append('-' * 70)
    lines.append('')
    
    for idx, q in enumerate(questions, 1):
        lines.append(f'Q{idx}. [{q["marks"]} marks] - {q["unit"]}')
        lines.append(f'    {q["question"]}')
        lines.append(f'    [Bloom\'s Level: {q["bloom_level"]}, Difficulty: {q["difficulty"]}]')
        lines.append('')
    
    # Statistics
    lines.append('=' * 70)
    lines.append('PAPER STATISTICS:')
    lines.append('-' * 70)
    
    # Bloom's distribution
    bloom_counts = {}
    for q in questions:
        bloom_counts[q['bloom_level']] = bloom_counts.get(q['bloom_level'], 0) + 1
    
    lines.append('Bloom\'s Taxonomy Distribution:')
    for level, count in sorted(bloom_counts.items()):
        lines.append(f'  {level}: {count} questions')
    
    lines.append('')
    
    # Difficulty distribution
    diff_counts = {}
    for q in questions:
        diff_counts[q['difficulty']] = diff_counts.get(q['difficulty'], 0) + 1
    
    lines.append('Difficulty Distribution:')
    for diff, count in sorted(diff_counts.items()):
        lines.append(f'  {diff}: {count} questions')
    
    lines.append('')
    lines.append('=' * 70)
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'question_paper_{timestamp}.txt'
    filepath = f'{export_folder}/{filename}'
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return filepath


def validate_paper_constraints(questions, total_marks, num_questions):
    """
    Validate if generated paper meets basic constraints
    
    Returns:
        Tuple (is_valid, issues_list)
    """
    issues = []
    
    # Check question count
    if len(questions) < num_questions * 0.8:
        issues.append(f'Only {len(questions)} questions generated (target: {num_questions})')
    
    # Check total marks
    actual_marks = sum([q['marks'] for q in questions])
    if abs(actual_marks - total_marks) > total_marks * 0.2:
        issues.append(f'Total marks {actual_marks} differs significantly from target {total_marks}')
    
    # Check for duplicate questions
    question_texts = [q['question'] for q in questions]
    if len(question_texts) != len(set(question_texts)):
        issues.append('Duplicate questions detected')
    
    is_valid = len(issues) == 0
    return is_valid, issues
