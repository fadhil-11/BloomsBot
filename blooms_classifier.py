"""
Bloom's Taxonomy Classification Module for BLOOMS BOT
Classifies questions by Bloom's level and difficulty
"""

import re


# Keywords associated with each Bloom's level
BLOOM_KEYWORDS = {
    'Remember': [
        'define', 'list', 'state', 'identify', 'name', 'label', 'recall',
        'recognize', 'select', 'what is', 'who', 'when', 'where', 'match',
        'choose', 'find', 'show', 'spell', 'tell', 'write'
    ],
    'Understand': [
        'explain', 'describe', 'summarize', 'discuss', 'interpret', 'paraphrase',
        'illustrate', 'classify', 'compare', 'translate', 'outline', 'review',
        'restate', 'express', 'locate', 'report', 'recognize', 'give example'
    ],
    'Apply': [
        'apply', 'demonstrate', 'use', 'implement', 'solve', 'show', 'execute',
        'construct', 'compute', 'modify', 'operate', 'prepare', 'produce',
        'relate', 'develop', 'organize', 'utilize', 'sketch', 'calculate'
    ],
    'Analyze': [
        'analyze', 'examine', 'compare', 'contrast', 'distinguish', 'differentiate',
        'investigate', 'categorize', 'breakdown', 'separate', 'infer', 'arrange',
        'classify', 'order', 'connect', 'divide', 'select', 'survey', 'inspect'
    ],
    'Evaluate': [
        'evaluate', 'assess', 'judge', 'critique', 'justify', 'argue', 'defend',
        'support', 'rate', 'prioritize', 'recommend', 'conclude', 'predict',
        'criticize', 'weigh', 'measure', 'validate', 'prove', 'disprove'
    ],
    'Create': [
        'create', 'design', 'develop', 'construct', 'plan', 'produce', 'invent',
        'formulate', 'propose', 'compose', 'generate', 'derive', 'modify',
        'assemble', 'set up', 'devise', 'imagine', 'integrate', 'synthesize'
    ]
}


def classify_question(question_text, marks):
    """
    Classify a question according to Bloom's Taxonomy and difficulty level
    
    Args:
        question_text: The question to classify
        marks: Marks allocated to the question
        
    Returns:
        Dictionary with bloom_level and difficulty
    """
    # Determine Bloom's level based on question text
    bloom_level = determine_bloom_level(question_text)
    
    # Determine difficulty based on both Bloom's level and marks
    difficulty = determine_difficulty(bloom_level, marks)
    
    return {
        'bloom_level': bloom_level,
        'difficulty': difficulty
    }


def determine_bloom_level(question_text):
    """
    Determine Bloom's Taxonomy level based on question keywords
    
    Args:
        question_text: The question text
        
    Returns:
        Bloom's level (Remember/Understand/Apply/Analyze/Evaluate/Create)
    """
    question_lower = question_text.lower()
    
    # Count keyword matches for each level
    level_scores = {level: 0 for level in BLOOM_KEYWORDS.keys()}
    
    for level, keywords in BLOOM_KEYWORDS.items():
        for keyword in keywords:
            # Check if keyword appears in question
            if re.search(r'\b' + re.escape(keyword) + r'\b', question_lower):
                level_scores[level] += 1
    
    # If no keywords matched, use heuristics
    if max(level_scores.values()) == 0:
        return classify_by_heuristics(question_text)
    
    # Return level with highest score
    return max(level_scores, key=level_scores.get)


def classify_by_heuristics(question_text):
    """
    Fallback classification using question structure and patterns
    
    Args:
        question_text: The question text
        
    Returns:
        Bloom's level
    """
    question_lower = question_text.lower()
    
    # Simple questions typically start with what/who/when/where
    if re.match(r'^(what|who|when|where)\s', question_lower):
        return 'Remember'
    
    # Questions with 'how' could be Understand or Apply
    if re.match(r'^how\s', question_lower):
        if 'work' in question_lower or 'implement' in question_lower:
            return 'Apply'
        return 'Understand'
    
    # Questions with 'why' typically require understanding or analysis
    if re.match(r'^why\s', question_lower):
        if len(question_text) > 100:  # Longer questions suggest deeper analysis
            return 'Analyze'
        return 'Understand'
    
    # Questions ending with '?' and requesting explanation
    if 'explain' in question_lower or 'describe' in question_lower:
        return 'Understand'
    
    # Questions about comparison or differences
    if 'compare' in question_lower or 'contrast' in question_lower or 'difference' in question_lower:
        return 'Analyze'
    
    # Questions requesting design or creation
    if 'design' in question_lower or 'create' in question_lower or 'develop' in question_lower:
        return 'Create'
    
    # Default to Understand for ambiguous cases
    return 'Understand'


def determine_difficulty(bloom_level, marks):
    """
    Determine difficulty level based on Bloom's level and marks
    
    Args:
        bloom_level: Bloom's Taxonomy level
        marks: Marks allocated to question
        
    Returns:
        Difficulty level (Easy/Medium/Hard)
    """
    # Base difficulty score from Bloom's level
    bloom_difficulty = {
        'Remember': 1,
        'Understand': 2,
        'Apply': 3,
        'Analyze': 4,
        'Evaluate': 5,
        'Create': 6
    }
    
    bloom_score = bloom_difficulty.get(bloom_level, 2)
    
    # Marks-based difficulty
    if marks <= 2:
        marks_score = 1
    elif marks <= 5:
        marks_score = 2
    else:
        marks_score = 3
    
    # Combined score (weighted average)
    combined_score = (bloom_score * 0.6) + (marks_score * 0.4)
    
    # Map to difficulty categories
    if combined_score <= 2.5:
        return 'Easy'
    elif combined_score <= 4.5:
        return 'Medium'
    else:
        return 'Hard'


def get_bloom_description(bloom_level):
    """
    Get a description of what each Bloom's level entails
    
    Args:
        bloom_level: Bloom's Taxonomy level
        
    Returns:
        Description string
    """
    descriptions = {
        'Remember': 'Recall facts and basic concepts',
        'Understand': 'Explain ideas or concepts',
        'Apply': 'Use information in new situations',
        'Analyze': 'Draw connections among ideas',
        'Evaluate': 'Justify a stand or decision',
        'Create': 'Produce new or original work'
    }
    
    return descriptions.get(bloom_level, 'Unknown level')


def validate_bloom_distribution(questions, target_distribution):
    """
    Check if a set of questions meets the target Bloom's distribution
    
    Args:
        questions: List of question dictionaries
        target_distribution: Dict mapping Bloom levels to percentages
        
    Returns:
        Boolean indicating if distribution is met
    """
    if not questions:
        return False
    
    # Count actual distribution
    actual_counts = {}
    for q in questions:
        level = q.get('bloom_level', 'Understand')
        actual_counts[level] = actual_counts.get(level, 0) + 1
    
    # Calculate percentages
    total = len(questions)
    actual_percentages = {level: (count / total * 100) for level, count in actual_counts.items()}
    
    # Check if within acceptable range (±10%)
    for level, target_pct in target_distribution.items():
        actual_pct = actual_percentages.get(level, 0)
        if abs(actual_pct - target_pct) > 10:
            return False
    
    return True


def suggest_bloom_distribution(total_marks):
    """
    Suggest a balanced Bloom's distribution for given total marks
    
    Args:
        total_marks: Total marks for the paper
        
    Returns:
        Dictionary with suggested percentages for each level
    """
    # Standard academic distribution
    if total_marks <= 50:
        # Shorter exam - focus on lower levels
        return {
            'Remember': 20,
            'Understand': 30,
            'Apply': 25,
            'Analyze': 15,
            'Evaluate': 10,
            'Create': 0
        }
    else:
        # Full exam - balanced distribution
        return {
            'Remember': 15,
            'Understand': 25,
            'Apply': 25,
            'Analyze': 20,
            'Evaluate': 10,
            'Create': 5
        }
