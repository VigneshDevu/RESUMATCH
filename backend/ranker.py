'''
import os
import re
import pdfplumber
import csv
import spacy
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CSV_FILE = "database/candidates.csv"
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("database", exist_ok=True)

nlp = spacy.load("en_core_web_md")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
    except Exception as e:
        print("❌ Error extracting text:", e)
    return text.strip()

def extract_resume_details(text):
    """Extracts structured information from resume text."""
    details = {
        "Name": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
        "Education": "Not Found",
        "Experience": "Not Found",
        "Skills": "Not Found",
        "Certifications": "Not Found",
        "FullText": text.replace("\n", " ")  # Ensure FullText is a single line
    }
    
    lines = text.split("\n")
    details["Name"] = lines[0].strip() if len(lines) > 0 else "Not Found"
    
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        details["Email"] = email_match.group()
    
    phone_match = re.search(r"\b\d{10}\b", text)
    if phone_match:
        details["Phone"] = phone_match.group()
    
    education_keywords = ["Bachelor", "Master", "B.Tech", "M.Tech", "BSc", "MSc", "PhD", "university", "college"]
    details["Education"] = " | ".join([line for line in lines if any(word in line for word in education_keywords)])
    
    experience_keywords = ["experience", "worked at", "internship", "years", "projects"]
    details["Experience"] = " | ".join([line for line in lines if any(word.lower() in line.lower() for word in experience_keywords)])
    
    skills_keywords = ["Python", "Java", "SQL", "Machine Learning", "Deep Learning", "Cloud", "C++", "Verilog", "Xilinx","Skills","Technical"]
    details["Skills"] = ", ".join([word for word in skills_keywords if word in text])
    
    cert_keywords = ["certification", "certified", "course", "diploma"]
    details["Certifications"] = " | ".join([line for line in lines if any(word.lower() in line.lower() for word in cert_keywords)])
    
    return details

def save_to_csv(data):
    """Saves extracted resume details to a CSV file with headers automatically."""
    headers = ["Name", "Email", "Phone", "Skills", "Experience", "Education", "Certifications", "FullText"]
    file_exists = os.path.isfile(CSV_FILE)
    
    if not file_exists or os.stat(CSV_FILE).st_size == 0:
        with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
    
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writerow(data)

def semantic_match(job_description, resume_text):
    """Computes similarity between job description and resume using NLP."""
    job_doc = nlp(job_description.lower())
    resume_doc = nlp(resume_text.lower())
    return job_doc.similarity(resume_doc)

def rank_resumes(job_description):
    """Ranks resumes based on job description match."""
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        return []
    
    df = pd.read_csv(CSV_FILE, encoding='utf-8')
    ranked_candidates = []
    for _, row in df.iterrows():
        resume_text = str(row.get("FullText", "")).strip()
        if resume_text:
            score = semantic_match(job_description, resume_text)
            matched_info = {
                "Technical Skills": row.get("Skills", "").split(", "),
                "Certifications": row.get("Certifications", "").split(" | "),
                "Projects": str(row.get("Experience", "")).split(" | ")
            }
            ranked_candidates.append({
                "name": row["Name"],
                "email": row["Email"],
                "phone": row["Phone"],
                "score": round(score, 2),
                "matched_info": matched_info
            })
    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
    return ranked_candidates

@app.route('/match', methods=['POST'])
def match_resumes():
    """Ranks resumes based on job description and returns sorted candidates."""
    data = request.get_json()
    if "job_description" not in data:
        return jsonify({"message": "Job description is required"}), 400
    
    ranked_candidates = rank_resumes(data["job_description"])
    return jsonify({"message": "Resumes ranked successfully!", "candidates": ranked_candidates}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles resume upload, extracts details, and saves to CSV."""
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        text = extract_text_from_pdf(filepath)
        if not text.strip():
            return jsonify({'message': 'Failed to extract resume text!'}), 400
        
        data = extract_resume_details(text)
        save_to_csv(data)
        return jsonify({'message': 'File uploaded successfully!', 'details': data}), 200

if __name__ == "__main__":
    app.run(debug=True)

'''

import os
import re
import pdfplumber
import csv
import spacy
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CSV_FILE = "database/candidates.csv"
ALLOWED_EXTENSIONS = {'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("database", exist_ok=True)

nlp = spacy.load("en_core_web_md")
bert_model = SentenceTransformer('all-MiniLM-L6-v2')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + " \n"
    except Exception as e:
        print("❌ Error extracting text:", e)
    return text.strip()

def extract_resume_details(text):
    details = {
        "Name": "Not Found",
        "Email": "Not Found",
        "Phone": "Not Found",
        "Education": "Not Found",
        "Experience": "Not Found",
        "Skills": "Not Found",
        "Certifications": "Not Found",
        "FullText": text.replace("\n", " ")
    }
    
    lines = text.split("\n")
    details["Name"] = lines[0].strip() if len(lines) > 0 else "Not Found"
    
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    if email_match:
        details["Email"] = email_match.group()
    
    phone_match = re.search(r"\b\d{10}\b", text)
    if phone_match:
        details["Phone"] = phone_match.group()
    
    education_keywords = ["Bachelor", "Master", "B.Tech", "M.Tech", "BSc", "MSc", "PhD", "university", "college"]
    details["Education"] = " | ".join([line for line in lines if any(word in line for word in education_keywords)])
    
    experience_keywords = ["experience", "worked at", "internship", "years", "projects"]
    details["Experience"] = " | ".join([line for line in lines if any(word.lower() in line.lower() and len(line.split()) > 3 for word in experience_keywords)])
    
    skills_keywords = ["Python", "Java", "SQL", "HTML", "CSS", "Cloud Computing", "Machine Learning", "Deep Learning", "C++", "Verilog", "Xilinx", "Digital Circuit Design", "Analog Circuit Design"]
    details["Skills"] = ", ".join(set([word for word in skills_keywords if word in text]))
    
    cert_keywords = ["certification", "certified", "course", "diploma", "Udemy", "NPTEL", "WIPRO"]
    details["Certifications"] = " | ".join([line for line in lines if any(word.lower() in line.lower() for word in cert_keywords)])
    
    return details

def save_to_csv(data):
    df = pd.DataFrame([data])
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
    else:
        df.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding='utf-8')

def bert_match(job_description, resume_text):
    job_embedding = bert_model.encode(job_description, convert_to_tensor=True)
    resume_embedding = bert_model.encode(resume_text, convert_to_tensor=True)
    similarity_score = util.pytorch_cos_sim(job_embedding, resume_embedding).item()
    return similarity_score

def rank_resumes(job_description):
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        return []
    
    df = pd.read_csv(CSV_FILE, encoding='utf-8')
    ranked_candidates = []
    for _, row in df.iterrows():
        skills_text = str(row.get("Skills", ""))
        experience_text = str(row.get("Experience", ""))
        certifications_text = str(row.get("Certifications", ""))
        full_text = str(row.get("FullText", ""))
        
        score = 0.5 * bert_match(job_description, skills_text) + \
                0.3 * bert_match(job_description, experience_text) + \
                0.2 * bert_match(job_description, certifications_text)
        
        matched_info = {
            "Technical Skills": skills_text.split(", "),
            "Certifications": certifications_text.split(" | "),
            "Projects": experience_text.split(" | ")
        }
        
        ranked_candidates.append({
            "name": row["Name"],
            "email": row["Email"],
            "phone": row["Phone"],
            "score": round(score, 2),
            "matched_info": matched_info
        })
    
    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
    return ranked_candidates

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filename)
        resume_text = extract_text_from_pdf(filename)
        resume_data = extract_resume_details(resume_text)
        save_to_csv(resume_data)
        return jsonify({"message": "Resume uploaded successfully!"}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400

@app.route('/match', methods=['POST'])
def match_resumes():
    data = request.get_json()
    job_description = data.get("job_description", "")
    if not job_description:
        return jsonify({"error": "Job description is required"}), 400
    ranked_candidates = rank_resumes(job_description)
    return jsonify({"candidates": ranked_candidates})

if __name__ == "__main__":
    app.run(debug=True)




