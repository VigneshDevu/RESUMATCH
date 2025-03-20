import os
import re
import csv
import fitz  # PyMuPDF
import spacy
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
CSV_FILE = "database/candidates.csv"
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists("database"):
    os.makedirs("database")

nlp = spacy.load("en_core_web_sm")

# ✅ Allowed File Type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                text += page.get_text() + "\n"
    except Exception as e:
        print("❌ Error extracting text:", e)
    return text.strip()

# ✅ Extract Name
def extract_name(text):
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Not Found"

# ✅ Extract Email & Phone
def extract_email(text):
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else "Not Found"

def extract_phone(text):
    match = re.search(r"\b\d{10}\b", text)
    return match.group(0) if match else "Not Found"

# ✅ Extract Sections Based on Meaning
def extract_section_data(text, section_keywords):
    doc = nlp(text)
    extracted_data = []
    
    for sentence in doc.sents:
        words = sentence.text.lower().split()
        if any(keyword in words for keyword in section_keywords):  
            extracted_data.append(sentence.text.strip())

    return ", ".join(extracted_data) if extracted_data else "Not Found"

# ✅ Save to CSV
def save_to_csv(name, email, phone, skills, experience, degree, university, cgpa, full_text):
    """Save extracted resume details to CSV properly formatted."""
    file_exists = os.path.isfile(CSV_FILE)

    if file_exists:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        if "Name,Email,Phone,Skills,Experience,Degree,University,CGPA,FullText" not in first_line:
            print("⚠ CSV file corrupted! Resetting...")
            file_exists = False

    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Email", "Phone", "Skills", "Experience", "Degree", "University", "CGPA", "FullText"])
        writer.writerow([name, email, phone, skills, experience, degree, university, cgpa, full_text.replace("\n", " ")])

    print("✅ Resume data saved successfully!")

# ✅ API Route: Upload Resume
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = extract_text_from_pdf(filepath)
        name = extract_name(text)
        email = extract_email(text)
        phone = extract_phone(text)
        skills = extract_section_data(text, ["skills", "programming", "technical skills"])
        experience = extract_section_data(text, ["experience", "internship", "projects", "certifications"])
        degree = extract_section_data(text, ["bachelor", "master", "phd", "education"])
        university = extract_section_data(text, ["university", "college", "institute"])
        cgpa = extract_section_data(text, ["cgpa", "gpa", "percentage"])

        save_to_csv(name, email, phone, skills, experience, degree, university, cgpa, text)

        return jsonify({
            'message': 'File uploaded successfully!',
            'name': name, 'email': email, 'phone': phone,
            'skills': skills, 'experience': experience,
            'degree': degree, 'university': university, 'cgpa': cgpa
        }), 200

# ✅ NLP-based Resume Ranking
def process_job_description(job_description):
    doc = nlp(job_description.lower())
    extracted_skills, qualifications, experience = [], [], 0

    for token in doc:
        if token.pos_ in {"NOUN", "PROPN"}:
            extracted_skills.append(token.text)
        if token.text.isdigit():
            years = int(token.text)
            if 0 < years < 40:
                experience = years
    print("Extracted Job Keywords:", extracted_skills)
    return extracted_skills, experience, qualifications

# ✅ Rank Resumes Based on Job Description
def rank_resumes(job_description):
    if not os.path.exists(CSV_FILE) or os.stat(CSV_FILE).st_size == 0:
        print("⚠ CSV file is empty or missing!")
        return []

    df = pd.read_csv(CSV_FILE)

    if df.empty:
        print("⚠ No data found in CSV file!")
        return []

    job_keywords, min_experience, qualifications = process_job_description(job_description)
    ranked_candidates = []

    for i, row in df.iterrows():
        field_match_score = 0
        fields = ["Skills", "Experience", "Degree", "University", "CGPA"]  
        
        for field in fields:
            resume_field = str(row[field]).lower()  
            field_match_score += sum(1 for word in job_keywords if word in resume_field)

        ranked_candidates.append({
            "name": row["Name"],
            "email": row["Email"],
            "phone": row["Phone"],
            "skills": row["Skills"],
            "experience": row["Experience"],
            "degree": row["Degree"],
            "university": row["University"],
            "cgpa": row["CGPA"],
            "score": field_match_score
        })

    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
    return ranked_candidates

# ✅ API Route: Match Resumes to Job Description
@app.route('/match', methods=['POST'])
def match_resumes():
    data = request.get_json()
    if "job_description" not in data:
        return jsonify({"message": "Job description is required"}), 400

    ranked_candidates = rank_resumes(data["job_description"])
    return jsonify({"message": "Resumes ranked successfully!", "candidates": ranked_candidates}), 200

if __name__ == "__main__":
    app.run(debug=True)



<!--
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Filter AI</title>
</head>
<body>
    <h1>Upload Resume</h1>
    <form id="upload-form" enctype="multipart/form-data">
        <input type="file" id="file-input" name="file" required />
        <button type="submit">Upload</button>
    </form>
    <p id="upload-message"></p>

    <h2>Enter Job Description</h2>
    <textarea id="job-description" rows="4" cols="50" placeholder="Enter job description here..."></textarea>
    <button onclick="matchResumes()">Find Best Candidates</button>

    <h3>Ranked Candidates</h3>
    <div id="results"></div>

    <script src="app.js"></script>
</body>
</html>
-->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Ranker</title>
    <script>
        function uploadResume() {
            let fileInput = document.getElementById("resumeInput");
            let uploadResult = document.getElementById("uploadResult");

            if (fileInput.files.length === 0) {
                uploadResult.innerText = "❌ Please select a file!";
                return;
            }

            let formData = new FormData();
            formData.append("file", fileInput.files[0]);

            fetch("http://127.0.0.1:5000/upload", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                uploadResult.innerText = "✅ " + data.message;
            })
            .catch(error => {
                console.error("Error:", error);
                uploadResult.innerText = "❌ Upload failed. Try again!";
            });
        }

        function matchResumes() {
            let jobDescription = document.getElementById("jobInput").value;
            let resultDiv = document.getElementById("matchResult");

            if (jobDescription.trim() === "") {
                resultDiv.innerHTML = "<p style='color:red;'>❌ Please enter a job description!</p>";
                return;
            }

            fetch("http://127.0.0.1:5000/match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_description: jobDescription })
            })
            .then(response => response.json())
            .then(data => {
                resultDiv.innerHTML = "<h3>Ranked Candidates:</h3>";
                if (data.candidates.length === 0) {
                    resultDiv.innerHTML += "<p>No matching candidates found.</p>";
                } else {
                    data.candidates.forEach(candidate => {
                        resultDiv.innerHTML += `
                            <p><strong>${candidate.name}</strong> - Score: ${(candidate.score || 0).toFixed(2)}</p>
                            <p>Email: ${candidate.email} | Phone: ${candidate.phone}</p>
                            <p>Skills: ${candidate.skills}</p>
                            <p>Experience: ${candidate.experience}</p>
                            <p>Degree: ${candidate.degree}</p>
                            <p>University: ${candidate.university}</p>
                            <p>CGPA: ${candidate.cgpa}</p>
                            <hr>
                        `;
                    });
                }
            })
            .catch(error => {
                console.error("Error:", error);
                resultDiv.innerHTML = "<p style='color:red;'>❌ Error fetching candidates!</p>";
            });
        }
    </script>
</head>
<body>
    <h1>Resume Ranker</h1>

    <h2>Upload Resume</h2>
    <input type="file" id="resumeInput">
    <button onclick="uploadResume()">Upload</button>
    <p id="uploadResult"></p>

    <h2>Job Matching</h2>
    <input type="text" id="jobInput" placeholder="Enter job description">
    <button onclick="matchResumes()">Find Candidates</button>
    
    <div id="matchResult"></div>
</body>
</html>
