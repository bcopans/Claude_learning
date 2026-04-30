"""
Lesson 5: Streaming responses.

Streaming lets you display tokens as they arrive instead of waiting for
the full response. Essential for any chat UI.

Job relevance: every user-facing LLM product streams.
"""

import anthropic

client = anthropic.Anthropic()

print("Streaming response (tokens arrive progressively):\n")

with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[
        {"role": "user", "content": "Explain transformer attention in 3 bullet points."}
    ],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

print("\n\n--- Stream finished ---")

# You can also get the final message object after streaming
# final_message = stream.get_final_message()
# print("Total tokens:", final_message.usage)
