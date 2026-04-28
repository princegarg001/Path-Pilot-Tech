"""
═══════════════════════════════════════════════════════════════
Learning Resources — Curated free resources by skill
═══════════════════════════════════════════════════════════════
Used to enrich plan tasks with specific learning links.
"""

LEARNING_RESOURCES: dict[str, list[str]] = {
    # ── Languages ──
    "Python": [
        "https://docs.python.org/3/tutorial/",
        "https://www.learnpython.org/",
        "https://realpython.com/",
    ],
    "JavaScript": [
        "https://javascript.info/",
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/",
    ],
    "TypeScript": [
        "https://www.typescriptlang.org/docs/handbook/",
        "https://www.totaltypescript.com/tutorials",
    ],
    "Java": [
        "https://dev.java/learn/",
        "https://www.baeldung.com/",
    ],
    "Go": [
        "https://go.dev/tour/",
        "https://gobyexample.com/",
    ],

    # ── Frontend ──
    "React": [
        "https://react.dev/learn",
        "https://www.freecodecamp.org/news/react-course/",
    ],
    "Next.js": [
        "https://nextjs.org/learn",
    ],
    "HTML": [
        "https://developer.mozilla.org/en-US/docs/Learn/HTML",
    ],
    "CSS": [
        "https://web.dev/learn/css/",
        "https://css-tricks.com/",
    ],

    # ── Backend ──
    "Django": [
        "https://docs.djangoproject.com/en/5.0/intro/tutorial01/",
        "https://www.djangoproject.com/start/",
    ],
    "Flask": [
        "https://flask.palletsprojects.com/en/3.0.x/tutorial/",
    ],
    "FastAPI": [
        "https://fastapi.tiangolo.com/tutorial/",
    ],
    "Node.js": [
        "https://nodejs.org/en/learn",
        "https://www.freecodecamp.org/news/get-started-with-nodejs/",
    ],
    "REST API": [
        "https://restfulapi.net/",
        "https://www.freecodecamp.org/news/rest-api-tutorial/",
    ],

    # ── DevOps ──
    "Docker": [
        "https://docs.docker.com/get-started/",
        "https://www.freecodecamp.org/news/the-docker-handbook/",
    ],
    "Kubernetes": [
        "https://kubernetes.io/docs/tutorials/",
        "https://www.freecodecamp.org/news/learn-kubernetes-in-under-3-hours/",
    ],
    "CI/CD": [
        "https://docs.github.com/en/actions/quickstart",
        "https://www.freecodecamp.org/news/what-is-ci-cd/",
    ],
    "AWS": [
        "https://aws.amazon.com/getting-started/",
        "https://www.freecodecamp.org/news/aws-certified-cloud-practitioner-study-course/",
    ],
    "Linux": [
        "https://linuxjourney.com/",
        "https://www.freecodecamp.org/news/the-linux-commands-handbook/",
    ],
    "Terraform": [
        "https://developer.hashicorp.com/terraform/tutorials",
    ],

    # ── Data ──
    "SQL": [
        "https://www.w3schools.com/sql/",
        "https://sqlbolt.com/",
        "https://mode.com/sql-tutorial/",
    ],
    "PostgreSQL": [
        "https://www.postgresqltutorial.com/",
    ],
    "MongoDB": [
        "https://www.mongodb.com/docs/manual/tutorial/",
    ],

    # ── AI/ML ──
    "Machine Learning": [
        "https://www.coursera.org/learn/machine-learning (Andrew Ng)",
        "https://www.freecodecamp.org/news/machine-learning-for-everybody/",
    ],
    "TensorFlow": [
        "https://www.tensorflow.org/tutorials",
    ],
    "PyTorch": [
        "https://pytorch.org/tutorials/",
    ],

    # ── Mobile ──
    "Flutter": [
        "https://docs.flutter.dev/get-started/codelab",
        "https://www.freecodecamp.org/news/learn-flutter-full-course/",
    ],
    "Kotlin": [
        "https://kotlinlang.org/docs/getting-started.html",
    ],
    "Swift": [
        "https://docs.swift.org/swift-book/documentation/the-swift-programming-language/",
    ],

    # ── Practices ──
    "System Design": [
        "https://github.com/donnemartin/system-design-primer",
        "https://www.freecodecamp.org/news/systems-design-for-interviews/",
    ],
    "Data Structures": [
        "https://www.freecodecamp.org/news/data-structures-101/",
        "https://neetcode.io/",
    ],
    "Git": [
        "https://learngitbranching.js.org/",
        "https://www.freecodecamp.org/news/git-and-github-for-beginners/",
    ],
    "Testing": [
        "https://www.freecodecamp.org/news/software-testing-for-beginners/",
    ],
    "Agile": [
        "https://www.atlassian.com/agile",
    ],
}


def get_resources_for_skill(skill_name: str) -> list[str]:
    """Get learning resources for a given skill. Returns empty list if none found."""
    # Direct match
    if skill_name in LEARNING_RESOURCES:
        return LEARNING_RESOURCES[skill_name]

    # Case-insensitive match
    normalized = skill_name.lower().strip()
    for key, resources in LEARNING_RESOURCES.items():
        if key.lower() == normalized:
            return resources

    return []
