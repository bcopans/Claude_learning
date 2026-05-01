import anthropic

client = anthropic.Anthropic()

system = """
You are a job application assistant. Follow these rules:
- Only recommend applying to jobs that are a strong fit for the candidate
- Suggest specific resume changes aligned to the job description
- Keep all responses natural and human — no corporate fluff
- Always check with the human before taking any action on their behalf
"""

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    system=system,
    messages=[
        {"role": "user", "content": "I saw a job for a data scientist requiring 5 years of ML experience and a PhD. I have 1 year of experience and no degree. Should I apply?"}
    ]
)

print(response.content[0].text)
print(f"\nTokens used — input: {response.usage.input_tokens}, output: {response.usage.output_tokens}")

