import anthropic
import json

client = anthropic.Anthropic()

tools = [
    {
        "name": "search_jobs",
        "description": "Search for job listings when the user asks about finding jobs, roles, or opportunities. Use this whenever you need real job data rather than general advice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_title": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": ["job_title"]
        }
    }
]

messages = [{"role": "user", "content": "Find me junior data scientist jobs in London"}]

# Step 1 - first call
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    tools=tools,
    messages=messages,
)

print("Stop reason:", response.stop_reason)

# Step 2 - Claude wants to use a tool
tool_call = next(b for b in response.content if b.type == "tool_use")
print("Claude wants to call:", tool_call.name)
print("With inputs:", json.dumps(tool_call.input, indent=2))

# Step 3 - fake search results (in reality you'd call a real jobs API here)
fake_results = [
    {"title": "Junior Data Scientist", "company": "FinTech Ltd", "salary": "£45,000", "skills": ["Python", "SQL", "ML basics"]},
    {"title": "Data Scientist (Entry Level)", "company": "NHS Digital", "salary": "£38,000", "skills": ["Python", "R", "Statistics"]},
]

# Step 4 - send Claude's response AND the tool result back
messages.append({"role": "assistant", "content": response.content})
messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": tool_call.id,
            "content": json.dumps(fake_results),
        }
    ],
})

# Step 5 - second call, Claude now has the data and can answer
final = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=300,
    tools=tools,
    messages=messages,
)

print("\nClaude's final answer:")
print(final.content[0].text)
