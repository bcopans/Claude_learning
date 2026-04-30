"""
Lesson 6: Structured output — getting JSON back reliably.

LLMs output text, but applications need structured data.
Two strategies:
  A) JSON mode via tool use (most reliable)
  B) Instruct in the prompt + parse (simpler, less reliable)

Job relevance: data extraction, classification, and form-filling are
extremely common AI product features.
"""

import json
import anthropic
from dataclasses import dataclass

client = anthropic.Anthropic()


# --- Strategy A: Use a dummy tool to force structured output ---

extraction_tool = {
    "name": "extract_job_info",
    "description": "Extract structured information from a job posting.",
    "input_schema": {
        "type": "object",
        "properties": {
            "job_title": {"type": "string"},
            "company": {"type": "string"},
            "required_skills": {"type": "array", "items": {"type": "string"}},
            "years_experience": {"type": "integer"},
            "remote": {"type": "boolean"},
            "salary_range": {
                "type": "object",
                "properties": {
                    "min": {"type": "integer"},
                    "max": {"type": "integer"},
                    "currency": {"type": "string"},
                },
            },
        },
        "required": ["job_title", "company", "required_skills"],
    },
}

JOB_POSTING = """
Senior ML Engineer at QuantumLeap AI
We're looking for a passionate ML Engineer with 5+ years of experience.
Must know Python, PyTorch, and distributed training. Kubernetes a plus.
Remote-first. Comp: $180k–$240k USD. Apply by June 1.
"""

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    tools=[extraction_tool],
    tool_choice={"type": "any"},  # force Claude to use a tool
    messages=[{"role": "user", "content": f"Extract info from this job posting:\n\n{JOB_POSTING}"}],
)

tool_call = next(b for b in response.content if b.type == "tool_use")
job_data = tool_call.input

print("Extracted job data:")
print(json.dumps(job_data, indent=2))

# Now you can work with it as a Python dict
print(f"\nSkills required: {', '.join(job_data['required_skills'])}")
if "salary_range" in job_data:
    sr = job_data["salary_range"]
    print(f"Salary: {sr.get('currency','$')}{sr.get('min','')}–{sr.get('max','')}")
