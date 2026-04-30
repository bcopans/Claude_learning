"""
Lesson 2: System prompts — giving Claude a persona and constraints.

System prompts are the #1 tool for shaping Claude's behaviour.
They run before the conversation and are cached automatically.

Job relevance: almost every production AI product uses a system prompt.
"""

import anthropic

client = anthropic.Anthropic()

SYSTEM = """
You are a senior software engineer conducting a technical interview.
Ask ONE concise follow-up question per turn.
Keep responses under 100 words.
Do not reveal the answer — only guide the candidate.
"""

conversation = [
    {"role": "user", "content": "Can you explain what a hash table is?"}
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    system=SYSTEM,
    messages=conversation,
)

reply = response.content[0].text
print("Interviewer:", reply)

# To continue the conversation, append both turns and call again
conversation.append({"role": "assistant", "content": reply})
conversation.append({"role": "user", "content": "It's like a dictionary that maps keys to values using a hash function."})

response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    system=SYSTEM,
    messages=conversation,
)
print("\nInterviewer (follow-up):", response2.content[0].text)
