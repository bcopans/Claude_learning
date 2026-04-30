"""
Lesson 4: Prompt caching — massive cost and latency savings.

When you have a long system prompt or large document that stays the same
across many calls, mark it with cache_control. Anthropic caches it server-side.

Cache hits cost ~10% of normal input tokens and are ~5x faster.

Job relevance: knowing about caching separates junior from senior AI engineers.
"""

import anthropic

client = anthropic.Anthropic()

LONG_DOCUMENT = """
[Imagine this is a 10,000-token legal contract, codebase, or knowledge base.
 In production you would load this from a file: open('big_doc.txt').read()]
""" * 50  # repeat to simulate length

def ask_about_document(question: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=[
            {
                "type": "text",
                "text": "You are a helpful assistant. Answer questions about the document below.",
            },
            {
                "type": "text",
                "text": LONG_DOCUMENT,
                "cache_control": {"type": "ephemeral"},  # <-- cache this block
            },
        ],
        messages=[{"role": "user", "content": question}],
    )

    usage = response.usage
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_created = getattr(usage, "cache_creation_input_tokens", 0)
    print(f"  cache_read={cache_read}  cache_created={cache_created}  output={usage.output_tokens}")
    return response.content[0].text


print("First call (cache MISS — cache is being created):")
print(ask_about_document("Summarise the document in one sentence."))

print("\nSecond call (cache HIT — much cheaper and faster):")
print(ask_about_document("Does the document mention any deadlines?"))
