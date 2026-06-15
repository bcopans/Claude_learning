"""
KindPaw — Streaming chat utility.

stream_chat() is a generator that handles the full tool-use loop
and yields SSE-ready (event_type, data) tuples:

  ('tool', 'Checking availability...')   while a tool runs
  ('text', 'Great news! ...')            text chunks as they arrive
  ('done', '')                           stream finished
  ('error', 'message')                   on exception
"""

import json

import anthropic

client = anthropic.Anthropic()

TOOL_LABELS = {
    # Owner tools
    "get_breed_cuts":      "Looking up cut styles",
    "search_groomers":     "Searching groomers",
    "get_groomer_profile": "Loading groomer profile",
    "browse_portfolio":    "Browsing portfolio",
    "check_availability":  "Checking availability",
    "find_owner":          "Looking up your account",
    "register_owner":      "Creating your account",
    "add_dog":             "Adding dog to passport",
    "book_appointment":    "Booking appointment",
    "list_my_bookings":    "Loading your bookings",
    "get_dog_history":     "Loading dog passport",
    "cancel_booking":      "Cancelling booking",
    "leave_review":        "Submitting review",
    # Groomer tools
    "view_my_schedule":    "Loading your schedule",
    "get_dog_card":        "Loading dog card",
    "add_availability":    "Updating calendar",
    "remove_availability": "Updating calendar",
    "complete_booking":    "Recording groom details",
    "add_service":         "Adding service",
    "view_my_reviews":     "Loading reviews",
}


def stream_chat(messages: list, system: str, tools: list, run_tool_fn):
    """
    Drives the tool-use loop with streaming for the final text response.
    Yields (event_type, data) pairs suitable for SSE.
    """
    while True:
        try:
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                tools=tools,
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    if chunk:
                        yield ("text", chunk)

                final = stream.get_final_message()
                messages.append({"role": "assistant", "content": final.content})

                if final.stop_reason != "tool_use":
                    break

                tool_results = []
                for block in final.content:
                    if block.type != "tool_use":
                        continue
                    label = TOOL_LABELS.get(block.name, "Thinking")
                    yield ("tool", f"{label}...")
                    result = run_tool_fn(block.name, block.input)
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     result,
                    })

                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            yield ("error", str(e))
            return

    yield ("done", "")
