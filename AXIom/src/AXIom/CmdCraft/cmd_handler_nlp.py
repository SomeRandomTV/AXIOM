import logging
import coloredlogs
import spacy
from typing import Dict, Any, List
from spacy.matcher import Matcher

# --- Configuration ---
FUNCTION_MAP = {
    "get_weather": {"location"},
    "get_news": {"topic"},
    "get_stock": {"stock_name"},
    "schedule_event": {"user", "event", "time"},  # Renamed 'schedule' to 'schedule_event' for clarity
    "get_schedule": {"time", "event", "user"},  # New function for inquiries
    "notify": {"recipient", "message"},
    "create_resident": {"name", "weight", "height"},
    "create_staff": {"name", "weight", "height", "temp"},
    "create_visitor": {"name", "purpose"}
}

SUPPORTED_TYPES = {
    "staff",
    "resident",
    "visitor"
}

# --- SpaCy Patterns ---
# Define patterns clearly for each intent
SPACY_PATTERNS = {
    "get_weather": [
        [{"LOWER": {"IN": ["what", "show", "how", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "weather"}],
        [{"LOWER": "weather"}, {"LOWER": "in"}]
    ],
    "get_news": [
        [{"LOWER": {"IN": ["what", "show", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "news"}],
        [{"LOWER": "news"}, {"LOWER": "in"}]
    ],
    "schedule_event": [  # Patterns for commanding to schedule something
        # Pattern 1: schedule (a/an) <event> (for) <person> (at) <time>
        [
            {"LEMMA": "schedule"},
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},  # 'a/an' is optional
            {"POS": "NOUN"},  # Event (e.g., meeting, flight)
            {"LOWER": "for", "OP": "?"},  # 'for' is optional
            {"POS": "PROPN"},  # Person (e.g., John, Sarah)
            {"LOWER": "at", "OP": "?"},  # 'at' is optional
            {"ENT_TYPE": "DATE", "OP": "?"}  # Date/Time (e.g., tomorrow, 3pm), optional
        ],
        # Pattern 2: schedule <person> (for) (a/an) <event> (at) <time>
        [
            {"LEMMA": "schedule"},
            {"POS": "PROPN"},  # Person
            {"LOWER": "for", "OP": "?"},  # 'for' is optional
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},  # 'a/an' is optional
            {"POS": "NOUN"},  # Event
            {"LOWER": "at", "OP": "?"},  # 'at' is optional
            {"ENT_TYPE": "DATE", "OP": "?"}  # Date/Time, optional
        ],
    ],
    "get_schedule": [  # Patterns for inquiring about a schedule
        # Pattern 1: What/When/Is [person] (for) [event] [time]
        [
            {"LOWER": {"IN": ["what", "when", "is", "are"]}},
            {"POS": "PROPN"},  # Person
            {"LOWER": "for", "OP": "?"},  # Optional "for"
            {"POS": "NOUN"},  # Event (e.g., flight, meeting)
            {"ENT_TYPE": "DATE", "OP": "?"}  # Optional Date/Time
        ],
        # Pattern 2: What's the [event] for [person] [time]
        [
            {"LOWER": {"IN": ["what", "when"]}}, {"LOWER": {"IN": ["is", "are", "s"]}, "OP": "?"},
            {"LOWER": "the", "OP": "?"},
            {"POS": "NOUN"},  # Event
            {"LOWER": "for"},
            {"POS": "PROPN"},  # Person
            {"ENT_TYPE": "DATE", "OP": "?"}  # Optional Date/Time
        ]
    ]
}


# --- NLP Handler Class ---
class NLPHandler:
    def __init__(self, log_level: int = logging.INFO) -> None:
        self.logger = self._set_up_logger(log_level)
        self.nlp = spacy.load("en_core_web_md")  # Use a larger model for better NER, e.g., en_core_web_md
        self.matcher = Matcher(self.nlp.vocab)
        self._add_matching_rules()

    @staticmethod
    def _set_up_logger(log_level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger('CommandHandler')
        coloredlogs.install(level=log_level, logger=logger,
                            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        return logger

    def _add_matching_rules(self) -> None:
        """Adds all defined patterns to the SpaCy matcher."""
        for intent_name, patterns in SPACY_PATTERNS.items():
            self.matcher.add(intent_name, patterns)
        self.logger.info("SpaCy matcher rules loaded.")

    def _parse_command(self, raw_command: str) -> Dict[str, Any]:
        """Parses the raw command to identify intent and extract parameters."""
        self.logger.debug(f"Parsing command: '{raw_command}'")
        doc = self.nlp(raw_command)
        matches = self.matcher(doc)
        self.logger.debug(f"Raw matches: {matches}")

        if not matches:
            self.logger.warning("No intent matched for the command.")
            return {"function_name": None, "function_params": {}}

        # Prioritize more specific matches if needed, but for now take the first
        match_id, start, end = matches[0]
        intent = self.nlp.vocab.strings[match_id]
        matched_span = doc[start:end]
        self.logger.info(f"Intent detected: '{intent}' (Matched text: '{matched_span.text}')")

        params = self._extract_params(intent, doc, matched_span)

        # Validate extracted parameters against expected parameters for the function
        if intent in FUNCTION_MAP:
            required_params = FUNCTION_MAP[intent]
            if not all(p in params for p in required_params if
                       p != "time" and p != "event"):  # Time and event can be optional in some contexts
                self.logger.warning(
                    f"Missing required parameters for intent '{intent}'. Expected: {required_params}, Found: {params.keys()}")
                # Optionally, you could return None for function_name here if strict validation is needed

        return {
            "function_name": intent,
            "function_params": params
        }

    def _extract_params(self, intent: str, doc: spacy.tokens.Doc, matched_span: spacy.tokens.Span) -> Dict[str, Any]:
        """Extracts parameters based on the detected intent and entity types."""
        params = {}

        # General entity extraction first
        for ent in doc.ents:
            self.logger.debug(f"Entity found: '{ent.text}' (Label: '{ent.label_}')")
            if ent.label_ == "GPE":  # Geo-Political Entity (cities, countries)
                if intent == "get_weather":
                    params["location"] = ent.text
                elif intent == "get_news":
                    params["topic"] = ent.text
            elif ent.label_ in {"ORG", "NORP"}:  # Organization, Nationalities/Religious/Political groups
                if intent == "get_news":
                    params["topic"] = ent.text
            elif ent.label_ == "DATE" or ent.label_ == "TIME":
                params["time"] = ent.text
            elif ent.label_ == "PERSON":
                params["person"] = ent.text  # Use 'person' as a generic key for users/recipients

        # Intent-specific parameter extraction and mapping to FUNCTION_MAP keys
        if intent in ["schedule_event", "get_schedule"]:
            # Prioritize PERSON entities for 'person'
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    params["person"] = ent.text
                    break  # Assuming one main person per command

            # For 'event', look for Nouns in the matched span or near "schedule" / "for"
            # This is a bit heuristic, a more robust way might use dependency parsing
            event_candidates = []
            for token in matched_span:
                if token.pos_ == "NOUN" and token.lemma_ not in ["schedule", "flight", "meeting",
                                                                 "call"]:  # Avoid common intent words if they aren't the event
                    event_candidates.append(token.text)

            # If no event from NER or explicit noun is found within matched span,
            # try to infer from common scheduling nouns
            if "event" not in params:
                # Look for a NOUN that is not "flight", "meeting", "call" directly after "schedule" or "for"
                for i, token in enumerate(doc):
                    if token.lemma_ == "schedule" and i + 1 < len(doc) and doc[i + 1].pos_ == "NOUN":
                        params["event"] = doc[i + 1].text
                        break
                    elif token.lower_ == "for" and i + 1 < len(doc) and doc[i + 1].pos_ == "NOUN":
                        params["event"] = doc[i + 1].text
                        break
                # Last resort for events not captured by stricter rules (e.g., 'flight' in "What John for flight")
                # This should be handled by better SpaCy patterns for nouns in specific positions
                if "event" not in params:
                    # Look for specific event words
                    for token in doc:
                        if token.lower_ in ["flight", "meeting", "call", "appointment", "presentation"]:
                            params["event"] = token.text
                            break

        # Map 'person' to the correct function-specific parameter name
        if "person" in params:
            person_value = params["person"]
            if intent in ["schedule_event", "get_schedule"]:  # Now explicitly handle both
                params["user"] = person_value
            elif intent == "notify":
                params["recipient"] = person_value
            elif intent in ["create_resident", "create_staff", "create_visitor"]:
                params["name"] = person_value
            del params["person"]  # Remove the temporary 'person' key

        self.logger.debug(f"Extracted parameters: {params}")
        return params

    def set_command(self, raw_command: str) -> None:
        """Sets the raw command and triggers parsing."""
        print(f"\n[INPUT]: {raw_command}")
        self.function_call = self._parse_command(raw_command)
        print("[PARSED]:", self.function_call)

    def dispatch(self) -> None:
        """Example method to simulate dispatching the command."""
        if self.function_call["function_name"]:
            self.logger.info(
                f"Dispatching function: {self.function_call['function_name']} with params: {self.function_call['function_params']}")
            # Here you would call the actual function based on self.function_call
            # e.g., getattr(self.command_executor, self.function_call["function_name"])(**self.function_call["function_params"])
        else:
            self.logger.info("No function to dispatch.")


# --- Main Execution ---
def main():
    nlp_handler = NLPHandler(log_level=logging.DEBUG)

    nlp_handler.set_command("Schedule a meeting for John tomorrow at 2.")
    nlp_handler.set_command("Schedule a flight for John tomorrow.")
    nlp_handler.set_command("What john for flight tomorrow")
    nlp_handler.set_command("When is Sarah's meeting next Tuesday?")  # New test case for inquiry
    nlp_handler.set_command("schedule Bob a call")  # More flexible schedule command
    nlp_handler.set_command("What's the news in London?")
    nlp_handler.set_command("tell me the weather in New York")
    nlp_handler.set_command("schedule a presentation for Emily next monday")


if __name__ == "__main__":
    main()
