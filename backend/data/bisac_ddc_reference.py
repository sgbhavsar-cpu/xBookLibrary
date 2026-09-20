"""Standard BISAC and Dewey Decimal Classification (DDC) reference tables and matcher."""

import re
from typing import Dict, List, Optional, Tuple

# Mapping: BISAC Code -> (Heading, Associated Keywords, Default DDC Code)
BISAC_REFERENCE: Dict[str, Tuple[str, List[str], str]] = {
    # Computers & Technology
    "COM051260": (
        "COMPUTERS / Artificial Intelligence / Machine Learning",
        [
            "artificial intelligence",
            "machine learning",
            "neural network",
            "deep learning",
            "nlp",
            "llm",
            "rag",
            "transformer",
        ],
        "006.3",
    ),
    "COM051010": (
        "COMPUTERS / Programming / Software Development",
        [
            "programming",
            "python",
            "javascript",
            "rust",
            "c++",
            "software engineering",
            "coding",
            "clean code",
            "compiler",
        ],
        "005.1",
    ),
    "COM014000": (
        "COMPUTERS / Database Management / General",
        [
            "database",
            "sql",
            "nosql",
            "postgres",
            "sqlite",
            "distributed systems",
            "data-intensive",
            "acid",
            "relational",
        ],
        "005.74",
    ),
    "COM046000": (
        "COMPUTERS / Operating Systems / General",
        [
            "operating systems",
            "linux",
            "kernel",
            "unix",
            "posix",
            "processes",
            "threads",
            "memory management",
        ],
        "005.43",
    ),
    "COM060000": (
        "COMPUTERS / Web / Web Services & APIs",
        [
            "web development",
            "fastapi",
            "rest api",
            "html",
            "css",
            "react",
            "http",
            "backend",
            "frontend",
        ],
        "006.7",
    ),
    "COM079000": (
        "COMPUTERS / Security / General",
        [
            "cybersecurity",
            "cryptography",
            "infosec",
            "encryption",
            "hacking",
            "penetration testing",
            "vulnerabilities",
        ],
        "005.8",
    ),
    "COM021000": (
        "COMPUTERS / Computer Science",
        [
            "algorithms",
            "data structures",
            "computational complexity",
            "turing",
            "automata",
            "discrete math",
        ],
        "004.0151",
    ),
    # Science Fiction & Fantasy
    "FIC028000": (
        "FICTION / Science Fiction / General",
        [
            "science fiction",
            "sci-fi",
            "space opera",
            "cyberpunk",
            "time travel",
            "dune",
            "alien",
            "galaxy",
            "interstellar",
        ],
        "813.54",
    ),
    "FIC009000": (
        "FICTION / Fantasy / General",
        [
            "fantasy",
            "magic",
            "sword",
            "wizards",
            "dragons",
            "epic fantasy",
            "tolkien",
            "mythology",
            "sorcery",
        ],
        "813.54",
    ),
    "FIC022000": (
        "FICTION / Mystery & Detective / General",
        ["mystery", "detective", "crime", "murder", "sherlock", "whodunit", "investigation"],
        "813.54",
    ),
    "FIC031000": (
        "FICTION / Thrillers / General",
        ["thriller", "suspense", "espionage", "spy", "conspiracy", "action"],
        "813.54",
    ),
    "FIC019000": (
        "FICTION / Literary",
        ["literary fiction", "contemporary novel", "classic novel", "pulitzer", "booker", "drama"],
        "813.54",
    ),
    # Science & Mathematics
    "SCI055000": (
        "SCIENCE / Physics / General",
        [
            "physics",
            "quantum",
            "relativity",
            "gravity",
            "thermodynamics",
            "mechanics",
            "astrophysics",
        ],
        "530",
    ),
    "SCI015000": (
        "SCIENCE / Cosmology",
        ["cosmology", "astronomy", "universe", "black holes", "stars", "big bang", "galaxies"],
        "523.1",
    ),
    "SCI008000": (
        "SCIENCE / Life Sciences / Biology",
        [
            "biology",
            "genetics",
            "evolution",
            "dna",
            "ecology",
            "molecular biology",
            "cells",
            "darwin",
        ],
        "570",
    ),
    "SCI040000": (
        "SCIENCE / Mathematics / General",
        [
            "mathematics",
            "calculus",
            "algebra",
            "geometry",
            "linear algebra",
            "statistics",
            "probability",
        ],
        "510",
    ),
    # Philosophy & Psychology
    "PHI005000": (
        "PHILOSOPHY / Ethics & Moral Philosophy",
        ["ethics", "moral", "utilitarianism", "kant", "virtue", "justice", "morality"],
        "170",
    ),
    "PHI015000": (
        "PHILOSOPHY / History & Surveys / General",
        [
            "philosophy",
            "stoicism",
            "existentialism",
            "epistemology",
            "metaphysics",
            "plato",
            "aristotle",
            "nietzsche",
        ],
        "100",
    ),
    "PSY008000": (
        "PSYCHOLOGY / Cognitive Psychology & Cognition",
        [
            "psychology",
            "cognitive science",
            "memory",
            "thinking",
            "decision making",
            "behavioral",
            "bias",
            "perception",
        ],
        "153",
    ),
    # Business & Economics
    "BUS041000": (
        "BUSINESS & ECONOMICS / Economics / General",
        [
            "economics",
            "macroeconomics",
            "microeconomics",
            "capitalism",
            "trade",
            "inflation",
            "market",
        ],
        "330",
    ),
    "BUS070000": (
        "BUSINESS & ECONOMICS / Management",
        [
            "management",
            "leadership",
            "organization",
            "strategy",
            "productivity",
            "startups",
            "entrepreneurship",
        ],
        "658",
    ),
    "BUS027000": (
        "BUSINESS & ECONOMICS / Finance / General",
        [
            "finance",
            "investing",
            "stocks",
            "wall street",
            "banking",
            "venture capital",
            "cryptocurrency",
        ],
        "332",
    ),
    # History & Biography
    "HIS037000": (
        "HISTORY / World",
        [
            "history",
            "world history",
            "war",
            "civilization",
            "empire",
            "revolution",
            "medieval",
            "ancient history",
        ],
        "909",
    ),
    "BIO000000": (
        "BIOGRAPHY & AUTOBIOGRAPHY / General",
        ["biography", "autobiography", "memoir", "letters", "diaries", "life story"],
        "920",
    ),
}

# DDC Top-Level & Division Mapping
DDC_DIVISIONS: Dict[str, str] = {
    "004": "Computer science",
    "005": "Computer programming, software, data",
    "006": "Special computer methods (AI, multimedia)",
    "100": "Philosophy",
    "150": "Psychology",
    "170": "Ethics",
    "330": "Economics",
    "510": "Mathematics",
    "520": "Astronomy & allied sciences",
    "530": "Physics",
    "570": "Biology",
    "658": "General management",
    "813": "American fiction in English",
    "823": "English fiction",
    "909": "World history",
    "920": "Biography, genealogy",
}


def classify_heuristically(
    title: str,
    author: Optional[str] = None,
    tags: Optional[List[str]] = None,
    description: Optional[str] = None,
) -> Tuple[str, str, str, float]:
    """Offline heuristic classifier matching book tokens against curated BISAC/DDC reference.

    Returns:
        Tuple of (bisac_code, bisac_heading, ddc_code, confidence)
    """
    search_text = " ".join(
        [
            title or "",
            author or "",
            " ".join(tags or []),
            description or "",
        ]
    ).lower()

    tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\+]{2,}\b", search_text))

    best_code: Optional[str] = None
    best_score = 0

    for bisac_code, (heading, keywords, _ddc) in BISAC_REFERENCE.items():
        score = 0
        for kw in keywords:
            kw_lower = kw.lower()
            if " " in kw_lower:
                if kw_lower in search_text:
                    score += 3
            elif kw_lower in tokens:
                score += 2

        if score > best_score:
            best_score = score
            best_code = bisac_code

    if best_code and best_score >= 2:
        heading, _, ddc = BISAC_REFERENCE[best_code]
        # Calculate confidence from score capped at 0.88 for heuristic matching
        confidence = min(0.65 + (best_score * 0.04), 0.88)
        return best_code, heading, ddc, round(confidence, 2)

    # Fallback to General / Non-Classifiable
    return "GEN000000", "GENERAL / Non-Classifiable", "000", 0.40
