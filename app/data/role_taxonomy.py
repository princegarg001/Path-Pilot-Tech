"""
═══════════════════════════════════════════════════════════════
Role Taxonomy — Required skills per role
═══════════════════════════════════════════════════════════════
Used for gap analysis: we compare extracted skills against
the target role's requirements to identify what's missing.
"""

ROLE_REQUIREMENTS: dict[str, dict[str, list[str]]] = {
    # ── Software Engineering ──
    "frontend_developer": {
        "core": ["JavaScript", "HTML", "CSS", "React", "Git"],
        "preferred": ["TypeScript", "Next.js", "Tailwind CSS", "Testing", "REST API"],
        "nice_to_have": ["GraphQL", "Web Performance", "Accessibility", "CI/CD", "Figma"],
    },
    "backend_developer": {
        "core": ["Python", "Java", "SQL", "REST API", "Git"],
        "preferred": ["Docker", "AWS", "PostgreSQL", "Redis", "CI/CD"],
        "nice_to_have": ["Kubernetes", "System Design", "Message Queues", "gRPC", "Monitoring"],
    },
    "full_stack_developer": {
        "core": ["JavaScript", "Python", "HTML", "CSS", "SQL", "Git", "REST API"],
        "preferred": ["React", "Node.js", "Docker", "PostgreSQL", "TypeScript"],
        "nice_to_have": ["AWS", "CI/CD", "GraphQL", "Redis", "System Design"],
    },
    "mobile_developer": {
        "core": ["Dart", "Flutter", "Git", "REST API"],
        "preferred": ["Firebase", "Swift", "Kotlin", "SQLite", "CI/CD"],
        "nice_to_have": ["GraphQL", "Push Notifications", "App Store Optimization", "Riverpod"],
    },
    "android_developer": {
        "core": ["Kotlin", "Java", "Android SDK", "Git", "XML"],
        "preferred": ["Jetpack Compose", "REST API", "Room Database", "MVVM", "Coroutines"],
        "nice_to_have": ["CI/CD", "Firebase", "GraphQL", "Dagger/Hilt", "Unit Testing"],
    },
    "ios_developer": {
        "core": ["Swift", "UIKit", "Xcode", "Git", "REST API"],
        "preferred": ["SwiftUI", "Core Data", "Combine", "MVVM", "CocoaPods"],
        "nice_to_have": ["CI/CD", "Firebase", "ARKit", "Push Notifications", "TestFlight"],
    },

    # ── Data & AI ──
    "data_scientist": {
        "core": ["Python", "SQL", "Machine Learning", "Statistics", "Pandas"],
        "preferred": ["TensorFlow", "Scikit-learn", "Data Visualization", "Jupyter", "NumPy"],
        "nice_to_have": ["Deep Learning", "NLP", "Spark", "Cloud", "A/B Testing"],
    },
    "data_analyst": {
        "core": ["SQL", "Excel", "Python", "Data Visualization", "Statistics"],
        "preferred": ["Tableau", "Power BI", "Pandas", "ETL", "Git"],
        "nice_to_have": ["Machine Learning", "R", "Looker", "Airflow", "dbt"],
    },
    "ml_engineer": {
        "core": ["Python", "Machine Learning", "TensorFlow", "Docker", "SQL"],
        "preferred": ["PyTorch", "MLOps", "Kubernetes", "AWS", "Data Pipeline"],
        "nice_to_have": ["Spark", "Kubeflow", "Model Monitoring", "Feature Store", "LLMs"],
    },
    "ai_engineer": {
        "core": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch"],
        "preferred": ["NLP", "Computer Vision", "LLMs", "Docker", "REST API"],
        "nice_to_have": ["Kubernetes", "MLOps", "ONNX", "Hugging Face", "Vector Databases"],
    },

    # ── DevOps & Cloud ──
    "devops_engineer": {
        "core": ["Docker", "Kubernetes", "CI/CD", "Linux", "Git"],
        "preferred": ["AWS", "Terraform", "Ansible", "Monitoring", "Python"],
        "nice_to_have": ["GCP", "Azure", "Helm", "Service Mesh", "Security"],
    },
    "cloud_engineer": {
        "core": ["AWS", "Docker", "Linux", "Networking", "CI/CD"],
        "preferred": ["Terraform", "Kubernetes", "Python", "Monitoring", "Security"],
        "nice_to_have": ["GCP", "Azure", "Serverless", "Cost Optimization", "Compliance"],
    },
    "sre_engineer": {
        "core": ["Linux", "Docker", "Kubernetes", "Monitoring", "Python"],
        "preferred": ["Terraform", "CI/CD", "Incident Management", "SLO/SLI", "Automation"],
        "nice_to_have": ["Chaos Engineering", "Service Mesh", "eBPF", "Cost Optimization"],
    },

    # ── Specialized ──
    "cybersecurity_analyst": {
        "core": ["Networking", "Linux", "Security Tools", "Firewalls", "SIEM"],
        "preferred": ["Python", "Penetration Testing", "Incident Response", "Cloud Security", "Compliance"],
        "nice_to_have": ["Forensics", "Malware Analysis", "Zero Trust", "DevSecOps", "Certifications"],
    },
    "qa_engineer": {
        "core": ["Testing", "Selenium", "Git", "SQL", "API Testing"],
        "preferred": ["Automation", "CI/CD", "Python", "Performance Testing", "Agile"],
        "nice_to_have": ["Security Testing", "Mobile Testing", "Load Testing", "BDD", "Docker"],
    },
    "game_developer": {
        "core": ["C++", "Unity", "Game Design", "Git", "Mathematics"],
        "preferred": ["Unreal Engine", "C#", "3D Modeling", "Physics", "Shaders"],
        "nice_to_have": ["Networking", "VR/AR", "AI Pathfinding", "Optimization", "Audio"],
    },
    "blockchain_developer": {
        "core": ["Solidity", "Ethereum", "Smart Contracts", "JavaScript", "Git"],
        "preferred": ["Web3.js", "DeFi", "Security Auditing", "Rust", "Testing"],
        "nice_to_have": ["Layer 2", "IPFS", "Tokenomics", "Cross-chain", "ZK Proofs"],
    },

    # ── Management & Design ──
    "product_manager": {
        "core": ["Product Strategy", "User Research", "Agile", "Data Analysis", "Communication"],
        "preferred": ["SQL", "A/B Testing", "Roadmapping", "Stakeholder Management", "Metrics"],
        "nice_to_have": ["Technical Background", "Design Thinking", "Growth", "AI/ML Knowledge"],
    },
    "ui_ux_designer": {
        "core": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems"],
        "preferred": ["Adobe XD", "Usability Testing", "HTML/CSS", "Accessibility", "Interaction Design"],
        "nice_to_have": ["Motion Design", "Design Tokens", "Analytics", "Front-end Basics"],
    },
}


def get_role_requirements(target_role: str) -> dict[str, list[str]]:
    """
    Look up role requirements from taxonomy.
    Fuzzy matches the target_role string to find the best fit.
    Falls back to a generic 'full_stack_developer' if no match.
    """
    normalized = target_role.lower().strip()

    # Direct key match
    for key, reqs in ROLE_REQUIREMENTS.items():
        if key in normalized or normalized in key:
            return reqs

    # Keyword-based fuzzy matching
    keyword_map = {
        "frontend": "frontend_developer",
        "front-end": "frontend_developer",
        "front end": "frontend_developer",
        "react": "frontend_developer",
        "vue": "frontend_developer",
        "angular": "frontend_developer",
        "backend": "backend_developer",
        "back-end": "backend_developer",
        "back end": "backend_developer",
        "server": "backend_developer",
        "full stack": "full_stack_developer",
        "fullstack": "full_stack_developer",
        "full-stack": "full_stack_developer",
        "mobile": "mobile_developer",
        "flutter": "mobile_developer",
        "android": "android_developer",
        "ios": "ios_developer",
        "swift": "ios_developer",
        "data scientist": "data_scientist",
        "data science": "data_scientist",
        "data analyst": "data_analyst",
        "analyst": "data_analyst",
        "machine learning": "ml_engineer",
        "ml ": "ml_engineer",
        "ai ": "ai_engineer",
        "artificial intelligence": "ai_engineer",
        "devops": "devops_engineer",
        "dev ops": "devops_engineer",
        "cloud": "cloud_engineer",
        "aws": "cloud_engineer",
        "sre": "sre_engineer",
        "site reliability": "sre_engineer",
        "security": "cybersecurity_analyst",
        "cyber": "cybersecurity_analyst",
        "qa": "qa_engineer",
        "test": "qa_engineer",
        "quality": "qa_engineer",
        "game": "game_developer",
        "unity": "game_developer",
        "unreal": "game_developer",
        "blockchain": "blockchain_developer",
        "web3": "blockchain_developer",
        "solidity": "blockchain_developer",
        "product manager": "product_manager",
        "product": "product_manager",
        "ui": "ui_ux_designer",
        "ux": "ui_ux_designer",
        "design": "ui_ux_designer",
    }

    for keyword, role_key in keyword_map.items():
        if keyword in normalized:
            return ROLE_REQUIREMENTS[role_key]

    # Default fallback
    return ROLE_REQUIREMENTS["full_stack_developer"]
