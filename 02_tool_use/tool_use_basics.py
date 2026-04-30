"""
Lesson 3: Tool use (function calling).

Tool use lets Claude call functions you define — the model decides WHEN
and HOW to call them based on the conversation.

This is how Claude agents browse the web, query databases, run code, etc.

Job relevance: tool use / function calling is in almost every AI eng job posting.
"""

import json
import anthropic

client = anthropic.Anthropic()

# 1. Define tools as JSON schemas
tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. 'London'"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "Temperature unit"},
            },
            "required": ["city"],
        },
    }
]

# 2. First turn — model may decide to call a tool
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather like in Tokyo right now?"}],
)

print("Stop reason:", response.stop_reason)  # "tool_use" when a tool is called

# 3. Handle tool calls
if response.stop_reason == "tool_use":
    tool_call = next(b for b in response.content if b.type == "tool_use")
    print(f"\nClaude wants to call: {tool_call.name}")
    print(f"With inputs: {json.dumps(tool_call.input, indent=2)}")

    # 4. Execute the tool (your real code goes here)
    def get_weather(city: str, unit: str = "celsius") -> dict:
        # Stub — replace with a real weather API call
        return {"city": city, "temperature": 22, "unit": unit, "condition": "Partly cloudy"}

    result = get_weather(**tool_call.input)

    # 5. Send the result back so Claude can form a final answer
    final = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        tools=tools,
        messages=[
            {"role": "user", "content": "What's the weather like in Tokyo right now?"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                ],
            },
        ],
    )
    print("\nFinal answer:", final.content[0].text)
