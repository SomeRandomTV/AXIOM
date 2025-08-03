import logging
import coloredlogs
import spacy
from typing import Dict, Any
from spacy.matcher import Matcher

# --- Function mapping ---
FUNCTION_MAP = {
    "get_weather": {"location"},
    "get_news": {"topic"},
    "get_stock": {"stock_name"},
    "schedule_event": {"user", "event", "time"},
    "get_schedule": {"time", "event", "user"},
    "notify": {"recipient", "message"},
    "create_resident": {"name", "weight", "height"},
    "create_staff": {"name", "weight", "height", "temp"},
    "create_visitor": {"name", "purpose"}
}

# Supported user types
SUPPORTED_TYPES = {"staff", "resident", "visitor"}

# --- SpaCy Patterns ---
SPACY_PATTERNS = {
    "get_weather": [
        [{"LOWER": {"IN": ["what", "show", "how", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "weather"}],
        [{"LOWER": "weather"}, {"LOWER": "in"}]
    ],
    "get_news": [
        [{"LOWER": {"IN": ["what", "show", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "news"}],
        [{"LOWER": "news"}, {"LOWER": "in"}]
    ],
    "schedule_event": [
        [
            {"LEMMA": "schedule"},
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},
            {"POS": "NOUN"},
            {"LOWER": "for", "OP": "?"},
            {"POS": "PROPN"},
            {"LOWER": "at", "OP": "?"},
            {"ENT_TYPE": "DATE", "OP": "?"}
        ],
        [
            {"LEMMA": "schedule"},
            {"POS": "PROPN"},
            {"LOWER": "for", "OP": "?"},
            {"LOWER": {"IN": ["a", "an"]}, "OP": "?"},
            {"POS": "NOUN"},
            {"LOWER": "at", "OP": "?"},
            {"ENT_TYPE": "DATE", "OP": "?"}
        ]
    ],
    "get_schedule": [
        [
            {"LOWER": {"IN": ["what", "when", "is", "are"]}},
            {"POS": "PROPN"},
            {"LOWER": "for", "OP": "?"},
            {"POS": "NOUN"},
            {"ENT_TYPE": "DATE", "OP": "?"}
        ],
        [
            {"LOWER": {"IN": ["what", "when"]}}, {"LOWER": {"IN": ["is", "are", "s"]}, "OP": "?"},
            {"LOWER": "the", "OP": "?"},
            {"POS": "NOUN"},
            {"LOWER": "for"},
            {"POS": "PROPN"},
            {"ENT_TYPE": "DATE", "OP": "?"}
        ]
    ]
}


class NLPHandler:
    """
    NLPHandler parses and dispatches structured commands using SpaCy.
    It matches patterns to identify intent and extracts semantic parameters.
    """

    def __init__(self, log_level: int = logging.INFO) -> None:
        
        """
        Initializes the NLPHandler with SpaCy model and matcher.
        
        Args:
            log_level (int): Logging level for the handler. Defaults to logging.INFO.
        """
        self.logger = self._set_up_logger(log_level)
        self.nlp = spacy.load("en_core_web_md")
        self.matcher = Matcher(self.nlp.vocab)
        self._add_matching_rules()
        self.function_call = {"function_name": None, "function_params": {}}

    @staticmethod
    def _set_up_logger(log_level: int) -> logging.Logger:
        logger = logging.getLogger("CommandHandler")
        coloredlogs.install(
            level=log_level,
            logger=logger,
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        return logger

    def _add_matching_rules(self) -> None:
        for intent_name, patterns in SPACY_PATTERNS.items():
            self.matcher.add(intent_name, patterns)
        self.logger.info("SpaCy matcher rules loaded.")

    def _parse_command(self, raw_command: str) -> Dict[str, Any]:
        self.logger.debug(f"Parsing command: '{raw_command}'")
        doc = self.nlp(raw_command)
        matches = self.matcher(doc)
        self.logger.debug(f"Raw matches: {matches}")

        if not matches:
            self.logger.warning("No intent matched for the command.")
            return {"function_name": None, "function_params": {}}

        match_id, start, end = matches[0]
        intent = self.nlp.vocab.strings[match_id]
        matched_span = doc[start:end]
        self.logger.info(f"Intent detected: '{intent}' (Matched text: '{matched_span.text}')")

        params = self._extract_params(intent, doc, matched_span)

        if intent in FUNCTION_MAP:
            required = FUNCTION_MAP[intent]
            if not all(p in params for p in required if p not in {"time", "event"}):
                self.logger.warning(
                    f"Missing required parameters for '{intent}'. "
                    f"Expected: {required}, Found: {params.keys()}"
                )

        return {"function_name": intent, "function_params": params}

    def _extract_params(self, intent: str, doc: spacy.tokens.Doc, matched_span: spacy.tokens.Span) -> Dict[str, Any]:
        params = {}

        for ent in doc.ents:
            self.logger.debug(f"Entity found: '{ent.text}' ({ent.label_})")
            if ent.label_ == "GPE":
                if intent == "get_weather":
                    params["location"] = ent.text
                elif intent == "get_news":
                    params["topic"] = ent.text
            elif ent.label_ in {"ORG", "NORP"}:
                if intent == "get_news":
                    params["topic"] = ent.text
            elif ent.label_ in {"DATE", "TIME"}:
                params["time"] = ent.text
            elif ent.label_ == "PERSON":
                params["person"] = ent.text

        if intent in {"schedule_event", "get_schedule"}:
            if "person" in params:
                params["user"] = params.pop("person")

            event_candidates = [
                token.text for token in matched_span if token.pos_ == "NOUN"
            ]

            if "event" not in params:
                for i, token in enumerate(doc):
                    if token.lemma_ == "schedule" and i + 1 < len(doc):
                        if doc[i + 1].pos_ == "NOUN":
                            params["event"] = doc[i + 1].text
                            break
                    elif token.lower_ == "for" and i + 1 < len(doc):
                        if doc[i + 1].pos_ == "NOUN":
                            params["event"] = doc[i + 1].text
                            break

                if "event" not in params:
                    for token in doc:
                        if token.lower_ in {
                            "flight", "meeting", "call", "appointment", "presentation", "medication"
                        }:
                            params["event"] = token.text
                            break

        if "person" in params:
            value = params.pop("person")
            if intent in {"create_resident", "create_staff", "create_visitor"}:
                params["name"] = value
            elif intent == "notify":
                params["recipient"] = value

        self.logger.debug(f"Extracted parameters: {params}")
        return params

    def set_command(self, raw_command: str) -> None:
        print(f"\n[INPUT]: {raw_command}")
        self.function_call = self._parse_command(raw_command)
        print("[PARSED]:", self.function_call)

    def dispatch(self) -> None:
        if self.function_call["function_name"]:
            self.logger.info(
                f"Dispatching function: {self.function_call['function_name']} "
                f"with params: {self.function_call['function_params']}"
            )
            # TODO: Actual function call logic
        else:
            self.logger.info("No function to dispatch.")


def main():
    nlp_handler = NLPHandler(log_level=logging.DEBUG)

    test_commands = [
        "Schedule a meeting for John tomorrow at 2.",
        "Schedule a flight for John tomorrow.",
        "What john for flight tomorrow",
        "When is Sarah's meeting next Tuesday?",
        "Schedule Bob a call",
        "What's the news in London?",
        "Tell me the weather in New York",
        "Schedule a presentation for Emily next Monday"
    ]

    for cmd in test_commands:
        nlp_handler.set_command(cmd)


if __name__ == "__main__":
    main()
