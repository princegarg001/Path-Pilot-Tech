"""
═══════════════════════════════════════════════════════════════
Skill Categories — Maps skills to their domain category
═══════════════════════════════════════════════════════════════
Used by the zero-shot classifier as a fallback/validation layer.
"""

SKILL_CATEGORIES: dict[str, list[str]] = {
    "Frontend": [
        "JavaScript", "TypeScript", "HTML", "CSS", "React", "Vue", "Angular",
        "Next.js", "Nuxt.js", "Svelte", "Tailwind CSS", "Bootstrap", "SASS",
        "LESS", "jQuery", "Webpack", "Vite", "Babel", "Redux", "Zustand",
        "Material UI", "Styled Components", "Responsive Design", "PWA",
        "Web Components", "Accessibility", "SEO", "Web Performance",
    ],
    "Backend": [
        "Python", "Java", "Go", "Rust", "C#", "PHP", "Ruby", "Scala",
        "Node.js", "Express", "Django", "Flask", "FastAPI", "Spring Boot",
        "ASP.NET", "Laravel", "Rails", "REST API", "GraphQL", "gRPC",
        "Microservices", "WebSockets", "OAuth", "JWT", "API Design",
    ],
    "Database": [
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "SQLite", "Firebase", "Supabase",
        "ORM", "Database Design", "Data Modeling", "Indexing",
    ],
    "DevOps & Cloud": [
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "CI/CD",
        "Terraform", "Ansible", "Jenkins", "GitHub Actions", "GitLab CI",
        "Linux", "Nginx", "Apache", "Monitoring", "Prometheus", "Grafana",
        "ELK Stack", "Serverless", "CloudFormation", "Helm",
    ],
    "Data & AI": [
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "Scikit-learn", "Pandas", "NumPy", "Data Analysis", "Statistics",
        "NLP", "Computer Vision", "Data Visualization", "Jupyter",
        "Spark", "Hadoop", "Airflow", "dbt", "Tableau", "Power BI",
        "LLMs", "Hugging Face", "OpenAI", "Data Pipeline",
    ],
    "Mobile": [
        "Flutter", "Dart", "React Native", "Swift", "SwiftUI", "Kotlin",
        "Jetpack Compose", "Android SDK", "iOS", "Xcode", "Firebase",
        "SQLite", "Push Notifications", "App Store",
    ],
    "Tools & Practices": [
        "Git", "GitHub", "GitLab", "Bitbucket", "Agile", "Scrum",
        "Jira", "Confluence", "Testing", "Unit Testing", "TDD", "BDD",
        "Selenium", "Jest", "Pytest", "Design Patterns", "Clean Code",
        "Code Review", "Documentation",
    ],
    "Soft Skills": [
        "Communication", "Leadership", "Team Management", "Problem Solving",
        "Critical Thinking", "Collaboration", "Mentoring", "Presentation",
        "Time Management", "Project Management", "Stakeholder Management",
    ],
}


def categorize_skill(skill_name: str) -> str:
    """
    Categorize a skill name into its domain.
    Returns the category string or 'Other' if not found.
    """
    normalized = skill_name.lower().strip()
    for category, skills in SKILL_CATEGORIES.items():
        for s in skills:
            if s.lower() == normalized or normalized in s.lower() or s.lower() in normalized:
                return category
    return "Other"


# All known skills flattened (for quick lookup)
ALL_KNOWN_SKILLS: set[str] = set()
for skills_list in SKILL_CATEGORIES.values():
    ALL_KNOWN_SKILLS.update(s.lower() for s in skills_list)
