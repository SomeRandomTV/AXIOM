# NLP Command Handler

This module handles parsing of natural language commands into structured function calls using **SpaCy** and predefined **intent patterns**.

For example:

> *"Schedule John for team meeting tomorrow."*
> Is parsed into:

```json
{
  "function_name": "schedule_event",
  "function_params": {
    "user": "John",
    "event": "team meeting",
    "time": "tomorrow"
  }
}
```

---

## Command Types

There are currently **four supported intents**, each mapping to a backend function:

| Intent           | Purpose                              | Example Input                                      |
| ---------------- | ------------------------------------ | -------------------------------------------------- |
| `get_weather`    | Retrieve weather data                | "What’s the weather in Austin?"                    |
| `get_news`       | Fetch news by location/topic         | "Show me the news in Tokyo."                       |
| `schedule_event` | Schedule an event for a user         | "Schedule John for a dentist appointment at 10am." |
| `get_schedule`   | Inquire about existing events        | "When is Sarah's dentist appointment?"             |
| `notify`         | Send a message to a user             | "Notify Jerry about his dentist tomorrow."         |
| `create_*`       | Create users (resident, staff, etc.) | "Add a new resident Jerry Smith, height 6'4"."     |

---

## Input Structure

Raw commands are parsed into:

```json
{
  "function_name": "<matched_intent>",
  "function_params": {
    "<param1>": "<value1>"
  }
}
```

If no intent is matched, the output will be:

```json
{
  "function_name": null,
  "function_params": {}
}
```

---

## Function Map

Maps supported function names to the required keys in `function_params`.

```python
FUNCTION_MAP = {
  "get_weather": {"location"},
  "get_news": {"topic"},
  "get_stock": {"stock_name"},
  "schedule_event": {"user", "event", "time"},
  "get_schedule": {"user", "event", "time"},
  "notify": {"recipient", "message"},
  "create_resident": {"name", "height", "weight"},
  "create_staff": {"name", "height", "weight", "temp"},
  "create_visitor": {"name", "purpose"}
}
```

---

## SpaCy Intent Patterns

Each intent has one or more **matching patterns** using SpaCy’s `Matcher`.
Patterns are designed to extract intent and key argument types (`PERSON`, `DATE`, `GPE`, etc.).

Example:

```python
SPACY_PATTERNS = {
  "get_weather": [
    [{"LOWER": "weather"}, {"LOWER": "in"}],
    [{"LOWER": {"IN": ["what", "show", "how", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "weather"}]
  ]
}
```

---

## Parameter Extraction

Parameters are extracted via two mechanisms:

1. **Named Entities** (e.g., GPE for location, DATE/TIME, PERSON)
2. **Positional heuristics** from matched tokens (e.g., `NOUN` following "schedule")

Example:

> "Schedule John for dentist at 3pm"

Extracted:

```json
{
  "user": "John",
  "event": "dentist",
  "time": "3pm"
}
```

---

## Core Class: `NLPHandler`

```python
handler = NLPHandler()
handler.set_command("Schedule Sarah for dentist tomorrow at 9am.")
handler.dispatch()
```

Prints:
**INPUT**: Schedule Sarah for dentist tomorrow at 9am.
**PARSED**: 
```json {
  "function_name": "schedule_event",
  "function_params": {
    "user": "Sarah",
    "event": "dentist",
    "time": "tomorrow at 9am"
  }
}
```

---

## Dispatch Logic

If `function_name` is valid, dispatch to your executor:

```python
getattr(command_executor, function_name)(**function_params)
```

If no intent matched, fallback to LLM or return:

```json
{
  "function_name": null,
  "function_params": {}
}
```

---

## Future Plans

* Robust date parsing (e.g., "next Thursday", "in two hours")
* Cancel/confirm scheduling via negation ("cancel John's appointment")
* Improve event inference with dependency parsing
