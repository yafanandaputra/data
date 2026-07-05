import os
import pandas as pd
import json
import ast
import re

def clean_skill_name(name):
    if not name or not isinstance(name, str):
        return ""
    name = name.strip()
    # Remove placeholders
    if name.lower() in ["unknown", "not provided", "none", "nan", ""]:
        return ""
    # Strip some characters but keep versioning if any
    return name

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    datasets_dir = os.path.join(script_dir, "..", "datasets")
    csv_path = os.path.join(datasets_dir, "resume_dataset_parsed.csv")
    output_path = os.path.join(datasets_dir, "skills_taxonomy.json")

    print(f"[*] Reading dataset from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"[x] Error: Dataset file not found at {csv_path}")
        return

    # Categories to extract
    taxonomy = {
        "programming_languages": set(),
        "frameworks": set(),
        "databases": set(),
        "cloud": set(),
        "languages": set(),
        "general_skills": set()
    }

    # Add default core skills to ensure modern internship requirements are covered
    defaults = {
        "programming_languages": ["Python", "JavaScript", "TypeScript", "Go", "Golang", "Java", "C++", "C#", "PHP", "Ruby", "Kotlin", "Swift", "Dart", "HTML", "CSS", "R", "SQL"],
        "frameworks": ["React", "React.js", "Next.js", "Vue.js", "Angular", "Express.js", "Express", "NestJS", "Django", "Flask", "FastAPI", "Laravel", "Spring Boot", "Flutter", "React Native", "Tailwind CSS", "Bootstrap", "jQuery"],
        "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "MariaDB", "Firebase", "Oracle", "Microsoft SQL Server", "Elasticsearch"],
        "cloud": ["AWS", "Amazon Web Services", "Google Cloud", "GCP", "Microsoft Azure", "Azure", "Docker", "Kubernetes", "Netlify", "Vercel", "Heroku"],
        "languages": ["Indonesian", "English", "Japanese", "Mandarin", "German", "French"],
        "general_skills": ["UI/UX", "Figma", "Git", "GitHub", "GitLab", "CI/CD", "REST API", "GraphQL", "Agile", "Scrum", "Data Analysis", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Tableau", "Power BI", "Excel", "Project Management", "UI Design", "UX Research", "Postman", "Linux", "Node.js"]
    }

    for cat, items in defaults.items():
        for item in items:
            taxonomy[cat].add(item)

    try:
        # Load the CSV. Using chunksize just in case it is extremely large, but 16MB fits fine in memory.
        df = pd.read_csv(csv_path)
        print(f"[+] Loaded {len(df)} rows. Processing skills...")
        
        for idx, row in df.iterrows():
            skills_str = row.get("skills")
            if pd.isna(skills_str) or not isinstance(skills_str, str):
                continue
            
            try:
                # Safely parse python dict string representation
                skills_dict = ast.literal_eval(skills_str)
                if not isinstance(skills_dict, dict):
                    continue
                
                # Extract technical sub-skills
                tech = skills_dict.get("technical", {})
                if isinstance(tech, dict):
                    # 1. Programming languages
                    for item in tech.get("programming_languages", []):
                        if isinstance(item, dict) and "name" in item:
                            cleaned = clean_skill_name(item["name"])
                            if cleaned: taxonomy["programming_languages"].add(cleaned)
                            
                    # 2. Frameworks
                    for item in tech.get("frameworks", []):
                        if isinstance(item, dict) and "name" in item:
                            cleaned = clean_skill_name(item["name"])
                            if cleaned: taxonomy["frameworks"].add(cleaned)
                            
                    # 3. Databases
                    for item in tech.get("databases", []):
                        if isinstance(item, dict) and "name" in item:
                            cleaned = clean_skill_name(item["name"])
                            if cleaned: taxonomy["databases"].add(cleaned)
                            
                    # 4. Cloud
                    for item in tech.get("cloud", []):
                        if isinstance(item, dict) and "name" in item:
                            cleaned = clean_skill_name(item["name"])
                            if cleaned: taxonomy["cloud"].add(cleaned)

                # Extract languages
                langs = skills_dict.get("languages", [])
                if isinstance(langs, list):
                    for item in langs:
                        if isinstance(item, dict) and "name" in item:
                            cleaned = clean_skill_name(item["name"])
                            if cleaned: taxonomy["languages"].add(cleaned)
                            
            except Exception as e:
                # Silently skip malformed rows
                continue

    except Exception as e:
        print(f"[x] Error during processing: {e}")

    # Convert sets to sorted lists with case-insensitive deduplication, preferring properly capitalized versions
    serialized_taxonomy = {}
    for cat, items in taxonomy.items():
        case_map = {}
        for item in items:
            item_cleaned = item.strip()
            item_lower = item_cleaned.lower()
            if not item_lower:
                continue
            if item_lower not in case_map:
                case_map[item_lower] = item_cleaned
            else:
                # Prefer version with more capital letters (e.g. JavaScript over javascript)
                old_val = case_map[item_lower]
                old_caps = sum(1 for c in old_val if c.isupper())
                new_caps = sum(1 for c in item_cleaned if c.isupper())
                if new_caps > old_caps:
                    case_map[item_lower] = item_cleaned
        
        serialized_taxonomy[cat] = sorted(list(case_map.values()))
    
    # Let's print out the stats
    print("\n--- Taxonomy Statistics ---")
    for cat, items in serialized_taxonomy.items():
        print(f"  {cat}: {len(items)} unique skills")

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serialized_taxonomy, f, indent=4, ensure_ascii=False)
        
    print(f"\n[+] Successfully saved skills taxonomy to: {output_path}")

if __name__ == "__main__":
    main()
