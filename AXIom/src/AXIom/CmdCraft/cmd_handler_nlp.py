# nlp command handler
import logging
import coloredlogs
import spacy
from typing import Dict, Any
from spacy.matcher import Matcher

FUNCTION_MAP = {
    "get_weather": {"location"},
    "get_news": {"topic"},
    "get_stock": {"stock_name"},
    "schedule": {"user", "event", "time"},
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

class NLPHandler:
    def __init__(self, log_level: int = logging.INFO) -> None:
        # setup logger
        self.log_level = log_level
        self.logger= self._set_up_logger(log_level)

        # command related stuff
        self.raw_command = None
        self.command = None
        self.params = None

        # set up the function call
        self.function_call = {
            "function_name": None,
            "function_params": None
        }

        # set up nlp class
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = Matcher(self.nlp.vocab)

        # add matching rules
        self.matcher.add("get_weather", [
            [{"LOWER": {"IN": ["what", "show", "how", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"},
             {"LOWER": "weather"}],
            [{"LOWER": "weather"}, {"LOWER": "in"}]
        ])

        self.matcher.add("get_news", [
            [{"LOWER": {"IN": ["what", "show", "tell"]}}, {"LOWER": "is"}, {"LOWER": "the"},
             {"LOWER": "news"}],
            [{"LOWER": "news"}, {"LOWER": "in"}]
        ])

        self.matcher.add(key="schedule", patterns=[
            [{"LOWER": "schedule"}, {"LOWER": "event"}, {"LOWER": "for"}],
            [{"LOWER": "schedule"}, {"LOWER": "event"}, {"LOWER": "for"}, {"LOWER": "who"}]

        ])

    @staticmethod
    def _set_up_logger(log_level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger('CommandHandler')
        coloredlogs.install(level=log_level, logger=logger,
                            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        return logger

    def set_command(self, raw_command: str) -> None:

        # create command
        self.raw_command = raw_command
        # reset any hanging prev commands
        self.command = None
        self.params = None
        self.function_call = {
            "function_name": None,
            "function_params": None
        }

    def _parse_command(self) -> Dict[str, Any]:
        self.logger.debug("Parsing command...")
        doc = self.nlp(self.raw_command)
        match = Matcher(doc)






def main():
    pass

if __name__ == "__main__":
    main()