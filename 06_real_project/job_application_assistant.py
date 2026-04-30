"""
Lesson 7: Capstone — AI-powered job application assistant.

Combines everything:
  - System prompts
  - Tool use
  - Structured output
  - Multi-turn conversation
  - Prompt caching (for the resume)

Usage:
  python job_application_assistant.py
"""

import json
import anthropic

client = anthropic.Anthropic()

# --- Your resume (in production, load from a file) ---
YOUR_RESUME = """
Name: Alex Chen
Email: alex@example.com

Experience:
  - Software Engineer at Acme Corp (2022–present)
    Built REST APIs with FastAPI, deployed on AWS ECS
    Reduced API latency by 40% through caching and query optimization
  - Junior Developer at Startup XYZ (2020–2022)
    React frontend, Node.js backend, PostgreSQL

Skills: Python, JavaScript, React, FastAPI, Node.js, PostgreSQL, AWS, Docker

Education: B.S. Computer Science, State University, 2020
"""

tools = [
    {
        "name": "analyse_job_fit",
        "description": "Analyse how well the candidate fits a job and return a structured assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "fit_score": {"type": "integer", "description": "1–10 fit score"},
                "matching_skills": {"type": "array", "items": {"type": "string"}},
                "missing_skills": {"type": "array", "items": {"type": "string"}},
                "talking_points": {"type": "array", "items": {"type": "string"}, "description": "3 strongest points to highlight in cover letter"},
                "cover_letter_opening": {"type": "string", "description": "A compelling first paragraph for the cover letter"},
            },
            "required": ["fit_score", "matching_skills", "missing_skills", "talking_points", "cover_letter_opening"],
        },
    }
]

SYSTEM = [
    {
        "type": "text",
        "text": (
            "You are an expert career coach and technical recruiter. "
            "Analyse job postings against the candidate's resume and provide honest, actionable advice. "
            "Be direct — point out gaps as well as strengths."
        ),
    },
    {
        "type": "text",
        "text": f"## Candidate Resume\n\n{YOUR_RESUME}",
        "cache_control": {"type": "ephemeral"},  # cache the resume across all calls
    },
]


def analyse_job(job_posting: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        tools=tools,
        tool_choice={"type": "any"},
        messages=[
            {"role": "user", "content": f"Analyse this job posting for me:\n\n{job_posting}"}
        ],
    )

    tool_call = next(b for b in response.content if b.type == "tool_use")
    return tool_call.input


def interview_prep(job_posting: str, assessment: dict) -> str:
    """Generate interview questions based on the job and gaps."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Based on this job posting:\n{job_posting}\n\n"
                    f"And this assessment (fit score {assessment['fit_score']}/10), "
                    f"give me the 3 most likely tough interview questions and brief talking points for each."
                ),
            }
        ],
    )
    return response.content[0].text


# --- Demo ---
SAMPLE_JOB = """
Senior Backend Engineer — FinTech Startup
Stack: Python, FastAPI, PostgreSQL, AWS, Kubernetes
5+ years experience required. Must have experience with payment systems.
Nice to have: Rust, Kafka, ML pipeline experience.
Remote, $160k–$200k.
"""

print("=== Job Application Assistant ===\n")
print("Analysing job fit...")
assessment = analyse_job(SAMPLE_JOB)

print(f"\nFit Score: {assessment['fit_score']}/10")
print(f"\nMatching skills: {', '.join(assessment['matching_skills'])}")
print(f"Missing skills:  {', '.join(assessment['missing_skills'])}")
print("\nTop talking points for cover letter:")
for i, point in enumerate(assessment["talking_points"], 1):
    print(f"  {i}. {point}")
print(f"\nCover letter opening:\n  {assessment['cover_letter_opening']}")

print("\n--- Interview Prep ---")
print(interview_prep(SAMPLE_JOB, assessment))
