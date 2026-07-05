import os
import re
import json
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CVAnalyzerEngine:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.taxonomy_path = os.path.join(self.script_dir, "..", "datasets", "skills_taxonomy.json")
        self.taxonomy = self.load_taxonomy()
        
    def load_taxonomy(self):
        """Loads the skills taxonomy JSON file or falls back to basic defaults."""
        if os.path.exists(self.taxonomy_path):
            try:
                with open(self.taxonomy_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[!] Error loading taxonomy: {e}. Using defaults.")
        
        # Hardcoded fallback list if file doesn't exist yet
        return {
            "programming_languages": ["Python", "JavaScript", "TypeScript", "Go", "Golang", "Java", "C++", "C#", "PHP", "HTML", "CSS", "SQL"],
            "frameworks": ["React", "React.js", "Next.js", "Vue.js", "Express", "Laravel", "Spring Boot", "Flutter", "React Native", "Tailwind CSS"],
            "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Firebase"],
            "cloud": ["AWS", "Google Cloud", "GCP", "Azure", "Docker", "Kubernetes"],
            "languages": ["Indonesian", "English"],
            "general_skills": ["UI/UX", "Figma", "Git", "GitHub", "REST API", "CI/CD", "Node.js"]
        }

    def extract_text_from_pdf(self, pdf_file_path):
        """Extracts raw text from a PDF file using pypdf."""
        try:
            reader = PdfReader(pdf_file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Failed to read PDF: {str(e)}")

    def clean_text(self, text):
        """Cleans and normalizes text for NLP processing."""
        if not text:
            return ""
        # Lowecase, remove excess whitespace
        cleaned = text.lower()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def extract_contact_info(self, text):
        """Extracts email and phone numbers using regex."""
        # Simple email regex
        email_match = re.search(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", text)
        email = email_match.group(0) if email_match else "Unknown"

        # Indonesian & International phone regex
        phone_match = re.search(r"(\+?62|0)[8][0-9]{8,11}\b|\+?[0-9]{8,15}\b", text)
        phone = phone_match.group(0) if phone_match else "Unknown"

        return {"email": email, "phone": phone}

    def extract_name(self, text):
        """Heuristic name extractor from CV text."""
        # Split text into lines, clean them
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Check first 5 lines for a potential name
        for line in lines[:5]:
            # Exclude lines that look like email, website, phone, or standard header keywords
            lower_line = line.lower()
            if any(k in lower_line for k in ["curriculum", "vitae", "resume", "page", "email", "phone", "contact", "address", "alamat", "telepon"]):
                continue
            # A valid name should be 2 to 4 words and contain mostly alphabetic chars
            words = line.split()
            if 1 <= len(words) <= 4 and re.match(r"^[a-zA-Z\s\.\,\']+$", line):
                return line
        return "Candidate Name"

    def extract_skills(self, text):
        """Extracts skills from text based on skills_taxonomy.json using safe boundary regex."""
        extracted = {}
        # Pad with spaces to ensure boundary match works on start/end
        text_padded = f" {text.lower()} "
        
        for category, skills in self.taxonomy.items():
            category_extracted = []
            for skill in skills:
                skill_lower = skill.lower()
                # Use a custom boundary regex that handles special chars (C++, C#, .js) safely
                # Ensure the matched skill is not a substring of a larger word
                escaped_skill = re.escape(skill_lower)
                pattern = rf"(?:^|[^a-zA-Z0-9_]){escaped_skill}(?:$|[^a-zA-Z0-9_])"
                if re.search(pattern, text_padded):
                    category_extracted.append(skill)
            if category_extracted:
                extracted[category] = sorted(category_extracted)
        return extracted

    def get_all_skills_flat(self, extracted_skills):
        """Flattens categorised skills dictionary into a list of strings."""
        flat_list = []
        for cat, skills in extracted_skills.items():
            flat_list.extend(skills)
        return list(set(flat_list))

    def analyze_resume(self, text):
        """Full parser: Extracts name, email, phone, and skills from CV text."""
        cleaned_text = self.clean_text(text)
        contact = self.extract_contact_info(text) # Use original text for case sensitivity / regex accuracy
        name = self.extract_name(text)
        skills = self.extract_skills(text)
        
        # Heuristic education level extraction
        education_levels = []
        edu_keywords = {
            "S3 / Doktor (Ph.D)": ["s3", "doktor", "ph.d", "doctorate"],
            "S2 / Magister (Master)": ["s2", "magister", "master degree", "m.sc", "m.t", "m.kom", "master of"],
            "S1 / Sarjana (Bachelor)": ["s1", "sarjana", "bachelor degree", "b.sc", "b.eng", "s.kom", "s.t", "s.si", "bachelor of"],
            "D3 / D4 / Diploma": ["d3", "d4", "diploma", "associate degree"],
            "SMA / SMK / High School": ["sma", "smk", "madrasah aliyah", "high school"]
        }
        for level, keywords in edu_keywords.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", cleaned_text):
                    education_levels.append(level)
                    break
        education_val = education_levels[0] if education_levels else "S1 / Sarjana (Bachelor)" # Default/fallback

        return {
            "name": name,
            "email": contact["email"],
            "phone": contact["phone"],
            "education": education_val,
            "skills": skills,
            "skills_flat": self.get_all_skills_flat(skills)
        }

    def match_cv_to_job(self, cv_data, job_title, job_requirements):
        """Computes matching percentage and qualitative gap analysis feedback."""
        # 1. Extract skills from the job vacancy requirements to know what is needed
        required_skills_dict = self.extract_skills(job_requirements)
        required_skills = self.get_all_skills_flat(required_skills_dict)
        
        # If no specific taxonomy skills were found in job description, search title as well
        if not required_skills:
            required_skills_dict_title = self.extract_skills(job_title)
            required_skills = self.get_all_skills_flat(required_skills_dict_title)

        candidate_skills = cv_data.get("skills_flat", [])

        # 2. Skill overlap calculation
        matched_skills = []
        missing_skills = []
        overlap_score = 0.0

        if required_skills:
            for skill in required_skills:
                if any(skill.lower() == cs.lower() for cs in candidate_skills):
                    matched_skills.append(skill)
                else:
                    missing_skills.append(skill)
            overlap_score = (len(matched_skills) / len(required_skills)) * 100
        else:
            # Fallback if no requirements are parsed (assume 50% overlap base)
            overlap_score = 50.0

        # 3. Semantic similarity calculation using TF-IDF + Cosine Similarity
        cv_text_flat = " ".join(candidate_skills) + " " + cv_data.get("education", "")
        job_text_flat = job_title + " " + job_requirements
        
        try:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([cv_text_flat, job_text_flat])
            semantic_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
        except Exception:
            semantic_score = 50.0 # Fallback if TF-IDF fails

        # 4. Final hybrid match score calculation (weighted: 60% skill overlap, 40% semantic similarity)
        final_score = round((overlap_score * 0.6) + (semantic_score * 0.4))
        # Ensure range is 0 - 100
        final_score = max(0, min(100, final_score))

        # Categorize
        if final_score >= 80:
            category = "Sangat Cocok (Highly Recommended)"
        elif final_score >= 60:
            category = "Cukup Cocok (Recommended)"
        else:
            category = "Kurang Cocok (Not Recommended)"

        # Generate qualitative strengths & recommendations
        strengths = []
        recommendations = []

        if matched_skills:
            strengths.append(f"Memiliki skill utama yang dibutuhkan: {', '.join(matched_skills[:4])}")
        if cv_data.get("education"):
            strengths.append(f"Pendidikan relevan dengan jenjang {cv_data['education']}")

        if missing_skills:
            recommendations.append(f"Disarankan mempelajari skill/tools tambahan: {', '.join(missing_skills[:4])}")
        else:
            recommendations.append("Keahlian sudah sangat sesuai dengan kebutuhan posisi ini.")

        return {
            "match_percentage": final_score,
            "match_category": category,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "strengths": strengths,
            "recommendations": recommendations
        }
