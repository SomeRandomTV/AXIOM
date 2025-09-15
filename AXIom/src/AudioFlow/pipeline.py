# audioflow/pipeline.py
from ..CmdCraft.command_processor import CommandProcessor

class AudioPipeline:
    """
    Handles full loop: mic -> transcription -> CmdCraft -> TTS.
    """

    def __init__(self, mic, transcriber, tts, cmd_processor: CommandProcessor):
        self.mic = mic
        self.transcriber = transcriber
        self.tts = tts
        self.cmd_processor = cmd_processor

    def run(self):
        """
        Run continuous pipeline loop.
        """
        while True:
            # 1. Get audio input
            audio = self.mic.buffer.get()  # TODO: implement mic streaming

            # 2. Transcribe
            text = self.transcriber.transcribe(audio)
            if not text:
                continue

            # 3. Process command
            response = self.cmd_processor.process(text)

            # 4. Speak response
            self.tts.speak(response)
