"""
Lesson 1: Your first Claude API call.

What you'll learn:
  - How to authenticate with the Anthropic SDK
  - How to send a message and read the response
  - The basic request/response structure

Run:
  pip install anthropic
  export ANTHROPIC_API_KEY="sk-ant-..."
  python hello_claude.py
"""

import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    messages=[
        {"role": "user", "content": "Hello! In one sentence, what is Claude?"}
    ],
)

print(message.content[0].text)

# Key things to notice:
#   message.model        -> which model was used
#   message.usage        -> input + output token counts (affects cost)
#   message.stop_reason  -> "end_turn" | "max_tokens" | "stop_sequence"
print(f"\nTokens used — input: {message.usage.input_tokens}, output: {message.usage.output_tokens}")
