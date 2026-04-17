import re
from typing import Dict, List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import spacy
from config import config
from services.generator import generate_email

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, download it
    import os
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def extract_skills(text: str) -> List[str]:
    """
    Extract potential skills from text using NER and pattern matching.
    """
    doc = nlp(text)
    skills = set()
    
    # Extract named entities that might be skills
    for ent in doc.ents:
        if ent.label_ in ["ORG", "PRODUCT", "LANGUAGE"]:
            skills.add(ent.text.lower())
    
    # Common skill-related patterns
    skill_patterns = [
        r'\b[A-Za-z+#]+(?:\.[A-Za-z+]+)*\b',  # Programming languages/tools
        r'\b[A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*\b',  # Capitalized terms
        r'\b(?:proficient|experienced|skilled)\s+in\s+([^,.]+)'  # Skill statements
    ]
    
    for pattern in skill_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        skills.update(match.group().lower() for match in matches)
    
    # Filter out common words and short terms
    return [skill for skill in skills if len(skill) > 2 and skill not in stop_words]

def clean_text(text: str) -> str:
    """
    Advanced text cleaning with lemmatization and specialized token handling.
    """
    # Basic cleaning
    text = text.lower()
    text = re.sub(r'[^\w\s-]', ' ', text)  # Keep hyphens for compound words
    
    # Tokenize and lemmatize
    tokens = word_tokenize(text)
    cleaned_tokens = []
    
    for token in tokens:
        if token not in stop_words and len(token) > 2:
            # Preserve technical terms and compound words
            if '-' in token or token.isupper():
                cleaned_tokens.append(token)
            else:
                lemma = lemmatizer.lemmatize(token)
                cleaned_tokens.append(lemma)
    
    return ' '.join(cleaned_tokens)

def analyze_requirements(job_description: str) -> Dict[str, List[str]]:
    """
    Analyze job description to extract key requirements.
    """
    doc = nlp(job_description)
    requirements = {
        'required_skills': [],
        'preferred_skills': [],
        'experience': [],
        'education': []
    }
    
    # Extract requirements by category
    for sent in doc.sents:
        text = sent.text.lower()
        if any(word in text for word in ['required', 'must have', 'essential']):
            requirements['required_skills'].extend(extract_skills(sent.text))
        elif any(word in text for word in ['preferred', 'desired', 'plus']):
            requirements['preferred_skills'].extend(extract_skills(sent.text))
        elif any(word in text for word in ['experience', 'year']):
            requirements['experience'].append(sent.text.strip())
        elif any(word in text for word in ['degree', 'education', 'certification']):
            requirements['education'].append(sent.text.strip())
    
    return requirements

def compute_match_score(resume_text: str, job_description: str) -> Tuple[int, Dict[str, float]]:
    """
    Compute detailed match scores between resume and job description.
    
    Returns:
        Tuple[int, Dict[str, float]]: Overall score and detailed category scores
    """
    # Clean texts
    resume_clean = clean_text(resume_text)
    job_clean = clean_text(job_description)
    
    # Extract skills and requirements
    resume_skills = set(extract_skills(resume_text))
    job_reqs = analyze_requirements(job_description)
    required_skills = set(job_reqs['required_skills'])
    preferred_skills = set(job_reqs['preferred_skills'])
    
    # Calculate skill match scores
    required_match = len(resume_skills & required_skills) / len(required_skills) if required_skills else 1.0
    preferred_match = len(resume_skills & preferred_skills) / len(preferred_skills) if preferred_skills else 1.0
    
    # Calculate overall content similarity using TF-IDF
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_clean, job_clean])
    content_similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    
    # Weight the scores (adjust weights as needed)
    weights = {
        'required_skills': 0.4,
        'preferred_skills': 0.2,
        'content_similarity': 0.4
    }
    
    detailed_scores = {
        'required_skills': required_match * 100,
        'preferred_skills': preferred_match * 100,
        'content_similarity': content_similarity * 100
    }
    
    overall_score = sum(score * weights[category] 
                       for category, score in detailed_scores.items())
    
    return int(overall_score), detailed_scores

def get_missing_requirements(resume_text: str, job_description: str) -> Dict[str, List[str]]:
    """
    Identify missing requirements from the resume.
    """
    resume_skills = set(extract_skills(resume_text))
    job_reqs = analyze_requirements(job_description)
    
    missing = {
        'required': [skill for skill in job_reqs['required_skills'] 
                    if skill not in resume_skills],
        'preferred': [skill for skill in job_reqs['preferred_skills'] 
                     if skill not in resume_skills]
    }
    
    return missing

def generate_application_email(
    resume_text: str,
    job_description: str,
    tone: str = "Formal",
    include_match_info: bool = False
) -> Tuple[str, Dict[str, any]]:
    """
    Generate a tailored job application email with optional match analysis.
    
    Returns:
        Tuple[str, Dict]: Email content and match analysis data
    """
    # Analyze match
    overall_score, detailed_scores = compute_match_score(resume_text, job_description)
    missing_reqs = get_missing_requirements(resume_text, job_description)
    
    # Prepare context for email generation
    skills_to_highlight = extract_skills(resume_text)
    job_reqs = analyze_requirements(job_description)
    
    prompt_context = (
        f"Resume Skills:\n{', '.join(skills_to_highlight)}\n\n"
        f"Job Requirements:\n"
        f"Required: {', '.join(job_reqs['required_skills'])}\n"
        f"Preferred: {', '.join(job_reqs['preferred_skills'])}\n\n"
        f"Match Score: {overall_score}%\n\n"
        f"Write a {tone.lower()} job application email that:\n"
        f"1. Highlights matching skills\n"
        f"2. Addresses any missing requirements positively\n"
        f"3. Shows enthusiasm and relevant experience"
    )
    
    email_content = generate_email("Job Application", prompt_context, tone)
    
    analysis_data = {
        'match_score': overall_score,
        'detailed_scores': detailed_scores,
        'missing_requirements': missing_reqs,
        'skills_found': list(skills_to_highlight)
    }
    
    return email_content, analysis_data