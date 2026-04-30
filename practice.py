import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=150,
    messages=[
        {"role": "user", "content": "What jobs can I get if I learn the Claude API?"}
    ]
)

print(response.content[0].text)
print(f"\nTokens used — input: {response.usage.input_tokens}, output: {response.usage.output_tokens}")
