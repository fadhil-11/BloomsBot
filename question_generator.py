"""
Question generation module for BLOOMS BOT
Generates academic questions from extracted document text
"""

import re
import random
from pdf_processor import extract_units_from_text, extract_topics_from_unit


# Question templates based on Bloom's Taxonomy levels
QUESTION_TEMPLATES = {
    'Remember': [
        "Define {topic}.",
        "What is {topic}?",
        "List the main features of {topic}.",
        "State the key components of {topic}.",
        "Identify the characteristics of {topic}.",
        "Recall the fundamental principles of {topic}.",
        "Name the types of {topic}.",
    ],
    'Understand': [
        "Explain {topic} in your own words.",
        "Describe the concept of {topic}.",
        "Summarize the main points of {topic}.",
        "Discuss the significance of {topic}.",
        "Illustrate {topic} with an example.",
        "Interpret the meaning of {topic}.",
        "Compare {topic} with related concepts.",
    ],
    'Apply': [
        "Demonstrate how {topic} can be implemented.",
        "Apply the principles of {topic} to solve a practical problem.",
        "Show how {topic} works in a real-world scenario.",
        "Use {topic} to develop a solution.",
        "Implement {topic} in a given context.",
        "Execute the steps involved in {topic}.",
    ],
    'Analyze': [
        "Analyze the structure of {topic}.",
        "Break down {topic} into its constituent parts.",
        "Examine the relationship between {topic} and related concepts.",
        "Compare and contrast different aspects of {topic}.",
        "Investigate the factors that influence {topic}.",
        "Distinguish between the components of {topic}.",
    ],
    'Evaluate': [
        "Evaluate the effectiveness of {topic}.",
        "Assess the advantages and disadvantages of {topic}.",
        "Critique the approach used in {topic}.",
        "Judge the validity of {topic}.",
        "Justify the importance of {topic}.",
        "Recommend improvements for {topic}.",
    ],
    'Create': [
        "Design a system that implements {topic}.",
        "Develop a new approach for {topic}.",
        "Construct a model demonstrating {topic}.",
        "Propose a solution using {topic}.",
        "Formulate a hypothesis about {topic}.",
        "Generate alternative methods for {topic}.",
    ]
}


def generate_questions_from_text(text, document_type='syllabus'):
    """
    Generate questions from extracted document text
    
    Args:
        text: Extracted text from PDF
        document_type: Type of document (syllabus/lecture_notes)
        
    Returns:
        List of question dictionaries
    """
    questions = []
    
    # Extract units from text
    units = extract_units_from_text(text)
    
    # If no units detected, create default unit
    if not units:
        units = {"Unit 1": text}
    
    # Generate questions for each unit
    for unit_name, unit_text in units.items():
        # Extract topics from this unit
        topics = extract_key_concepts(unit_text)
        
        # Generate different types of questions per unit
        unit_questions = generate_questions_for_unit(unit_name, topics, unit_text)
        questions.extend(unit_questions)
    
    # Ensure we have a good distribution
    questions = balance_question_distribution(questions)
    
    return questions


def extract_key_concepts(text):
    """
    Extract key concepts and topics from text for question generation
    
    Args:
        text: Unit or section text
        
    Returns:
        List of key concepts
    """
    concepts = []
    
    # Method 1: Extract capitalized multi-word terms (technical concepts)
    technical_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b', text)
    concepts.extend(technical_terms)
    
    # Method 2: Extract terms after common academic markers
    markers = [
        r'define[sd]?\s+(\w+(?:\s+\w+){0,2})',
        r'concept of\s+(\w+(?:\s+\w+){0,2})',
        r'called\s+(\w+(?:\s+\w+){0,2})',
        r'known as\s+(\w+(?:\s+\w+){0,2})',
        r'refers to\s+(\w+(?:\s+\w+){0,2})',
        r'meaning of\s+(\w+(?:\s+\w+){0,2})',
    ]
    
    for marker in markers:
        matches = re.findall(marker, text, re.IGNORECASE)
        concepts.extend(matches)
    
    # Method 3: Extract nouns that appear frequently (likely important topics)
    words = re.findall(r'\b[A-Z][a-z]{3,}\b', text)
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top frequent terms
    frequent_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    concepts.extend([term[0] for term in frequent_terms])
    
    # Clean and deduplicate
    concepts = list(set([c.strip() for c in concepts if len(c.strip()) > 3]))
    
    # Return top concepts
    return concepts[:15]


def generate_questions_for_unit(unit_name, topics, unit_text):
    """
    Generate a balanced set of questions for a unit
    
    Args:
        unit_name: Name of the unit (e.g., "Unit 1")
        topics: List of key topics in the unit
        unit_text: Full text of the unit
        
    Returns:
        List of question dictionaries
    """
    questions = []
    
    if not topics:
        # If no topics extracted, create generic questions
        topics = ["the concepts covered", "the key principles", "the main topics"]
    
    # Target: Generate 8-12 questions per unit with varied marks and Bloom's levels
    marks_distribution = [2, 2, 5, 5, 5, 10, 10, 10]
    random.shuffle(marks_distribution)
    
    # Ensure we have enough topics
    while len(topics) < len(marks_distribution):
        topics.extend(topics[:len(marks_distribution) - len(topics)])
    
    # Shuffle topics for variety
    random.shuffle(topics)
    
    # Generate questions
    for i, marks in enumerate(marks_distribution[:min(len(topics), 10)]):
        topic = topics[i]
        
        # Select appropriate Bloom's level based on marks
        if marks == 2:
            bloom_options = ['Remember', 'Understand']
        elif marks == 5:
            bloom_options = ['Understand', 'Apply']
        else:  # 10 marks
            bloom_options = ['Apply', 'Analyze', 'Evaluate', 'Create']
        
        bloom_level = random.choice(bloom_options)
        
        # Generate question text
        template = random.choice(QUESTION_TEMPLATES[bloom_level])
        question_text = template.replace('{topic}', topic)
        
        questions.append({
            'unit': unit_name,
            'question': question_text,
            'marks': marks,
            'bloom_level': bloom_level  # Will be re-classified by blooms_classifier
        })
    
    return questions


def balance_question_distribution(questions):
    """
    Ensure balanced distribution across units, marks, and Bloom's levels
    
    Args:
        questions: List of generated questions
        
    Returns:
        Balanced list of questions
    """
    # Count questions per unit
    unit_counts = {}
    for q in questions:
        unit_counts[q['unit']] = unit_counts.get(q['unit'], 0) + 1
    
    # If one unit has significantly more questions, trim it
    max_per_unit = max(unit_counts.values()) if unit_counts else 0
    min_per_unit = min(unit_counts.values()) if unit_counts else 0
    
    if max_per_unit > min_per_unit * 2:
        balanced = []
        target_per_unit = max(8, min_per_unit + 2)
        
        for unit in unit_counts.keys():
            unit_questions = [q for q in questions if q['unit'] == unit]
            balanced.extend(unit_questions[:target_per_unit])
        
        questions = balanced
    
    return questions


def generate_contextual_question(text_snippet, marks):
    """
    Generate a question based on a specific text snippet
    
    Args:
        text_snippet: Short excerpt from the document
        marks: Target marks for the question
        
    Returns:
        Question dictionary
    """
    # Extract key phrases from snippet
    sentences = re.split(r'[.!?]+', text_snippet)
    if not sentences:
        return None
    
    main_sentence = sentences[0].strip()
    
    # Create question based on marks
    if marks <= 2:
        question = f"What is mentioned about {main_sentence[:50]}?"
    elif marks <= 5:
        question = f"Explain the concept described in: '{main_sentence[:80]}...'"
    else:
        question = f"Analyze and discuss: '{main_sentence[:80]}...'"
    
    return {
        'question': question,
        'marks': marks,
        'context': text_snippet[:200]
    }
