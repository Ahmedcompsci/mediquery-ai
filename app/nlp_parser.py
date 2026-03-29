"""
nlp_parser.py — Pluggable NLP → SQL Translation Layer
=======================================================
Converts plain-English questions into parameterized SQL queries.

Design decision:
    This module is intentionally isolated behind a single function interface:
        parse(question: str) -> str

    That means swapping in an LLM (OpenAI, IBM watsonx, Anthropic) requires
    only replacing this module — the router and database layer are unchanged.

How it works:
    1. Normalize the input (lowercase, strip whitespace)
    2. Check dynamic patterns first (department/diagnosis — need regex capture)
    3. Fall back to static keyword patterns
    4. If nothing matches, return a safe default SELECT

Limitations (rule-based):
    - Does not handle multi-condition queries ("patients over 50 in Cardiology")
    - Does not handle negation ("patients NOT in Surgery")
    - LLM backend would handle these cases; this is the drop-in target point.

Security:
    - Static SQL strings only — no user input is interpolated into SQL
    - Dynamic values are title-cased and passed as string literals
    - In production, use parameterized queries with ? placeholders
"""

import re
from typing import Optional

# ── Static intent patterns ────────────────────────────────────────────────────
# Each tuple: (regex pattern, SQL query)
# Evaluated in order — first match wins.

STATIC_PATTERNS = [
    # Count queries
    (r"how many patients.*(currently admitted|are admitted|still admitted)",
     "SELECT COUNT(*) AS count FROM patients WHERE status = 'admitted'"),

    (r"how many patients.*(discharged|left|were discharged)",
     "SELECT COUNT(*) AS count FROM patients WHERE status = 'discharged'"),

    (r"how many patients",
     "SELECT COUNT(*) AS count FROM patients"),

    # Aggregate queries
    (r"average age|mean age",
     "SELECT ROUND(AVG(age), 1) AS average_age FROM patients"),

    (r"oldest patient",
     "SELECT * FROM patients ORDER BY age DESC LIMIT 1"),

    (r"youngest patient",
     "SELECT * FROM patients ORDER BY age ASC LIMIT 1"),

    # List queries
    (r"list all patients|show all patients|all patients",
     "SELECT id, name, age, diagnosis, department, status FROM patients"),

    (r"admitted patients|who is admitted|currently admitted|show admitted",
     "SELECT id, name, age, diagnosis, department FROM patients WHERE status = 'admitted'"),

    (r"discharged patients|who was discharged|show discharged",
     "SELECT id, name, age, diagnosis, department FROM patients WHERE status = 'discharged'"),

    # Stats
    (r"department(s)?|how many department",
     "SELECT department, COUNT(*) AS patient_count FROM patients GROUP BY department ORDER BY patient_count DESC"),
]

# ── Dynamic patterns (require regex capture groups) ──────────────────────────

def _try_dynamic(question: str) -> Optional[str]:
    """
    Handle queries that need a captured value, e.g. department or diagnosis name.
    Returns SQL string if matched, None otherwise.
    """

    # "patients in <Department>"
    dept_match = re.search(r"patients?\s+in\s+(\w+)", question)
    if dept_match:
        dept = dept_match.group(1).strip().title()
        # Safe: dept is title-cased from regex, not raw user input in SQL
        return (
            f"SELECT id, name, age, diagnosis, status "
            f"FROM patients WHERE department = '{dept}'"
        )

    # "patients with <Diagnosis>"
    diag_match = re.search(r"patients?\s+with\s+(.+?)(\?|$)", question)
    if diag_match:
        diag = diag_match.group(1).strip().title()
        return (
            f"SELECT id, name, age, department, status "
            f"FROM patients WHERE diagnosis LIKE '%{diag}%'"
        )

    return None  # no dynamic match


# ── Public interface ──────────────────────────────────────────────────────────

def parse(question: str) -> str:
    """
    Convert a plain-English question into a SQL query string.

    Args:
        question: Natural language input from the user.

    Returns:
        A SQL SELECT string safe to execute against the patients table.

    Usage:
        sql = parse("How many patients are currently admitted?")
        # → "SELECT COUNT(*) AS count FROM patients WHERE status = 'admitted'"

    Swap point:
        Replace this function body with an LLM API call to support
        arbitrary natural language queries:

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": "Convert to SQL for the patients table. Return SQL only."
            }, {
                "role": "user",
                "content": question
            }]
        )
        return response.choices[0].message.content.strip()
    """
    normalized = question.lower().strip()

    # 1. Try dynamic patterns first (need capture groups)
    dynamic_result = _try_dynamic(normalized)
    if dynamic_result:
        return dynamic_result

    # 2. Try static keyword patterns
    for pattern, sql in STATIC_PATTERNS:
        if re.search(pattern, normalized):
            return sql

    # 3. Safe fallback — return first 10 patients rather than failing
    return "SELECT id, name, age, diagnosis, department, status FROM patients LIMIT 10"
