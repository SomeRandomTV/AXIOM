import io
import os
from dotenv import load_dotenv
from elevenlabs import ElevenLabs, play
import numpy as np
import soundfile as sf
from pydub import AudioSegment

class TTS_Engine:
    def __init__(self, model_name: str = None, voice_id: str = None,sample_rate: int = 44100) -> None:
        """
        Initialize the ElevenLabs TTS engine

        :param model_name: ElevenLabs model ID (falls back to DEFAULT_MODEL env var).
        :param voice_id: ElevenLabs voice ID (falls back to DEFAULT_VOICE_ID env var).
        :param sample_rate: output sample rate for WAV files & playback.
        """
        load_dotenv()

        self.xi_api_key = os.getenv("XI_API_KEY")
        if not self.xi_api_key:
            raise ValueError("XI_API_KEY not set in environment")

        self.client = ElevenLabs(api_key=self.xi_api_key)
        self.model_name = model_name or os.getenv("DEFAULT_MODEL")
        self.voice_id = voice_id or os.getenv("DEFAULT_VOICE_ID")
        self.sample_rate = sample_rate

        if not self.model_name:
            raise ValueError("Model ID not set (pass one or set DEFAULT_MODEL)")
        if not self.voice_id:
            raise ValueError("Voice ID not set (pass one or set DEFAULT_VOICE_ID)")

    def list_speakers(self) -> list[str]:
        """
        Return list of available ElevenLabs voice IDs
        :return: list of voice IDs
        """
        resp = self.client.voices.search(include_total_count=True)
        return [v.voice_id for v in resp.voices]

    def generate_speech(self, text: str, speaker: str = None) -> np.ndarray:
        """
        Synthesize speech from text, returning a NumPy array of floats in [-1,1].

        :param text: text to synthesize.
        :param speaker: overrides default voice ID for this utterance.
        :return: float32 numpy array of audio samples.
        """
        spk = speaker or self.voice_id

        # generate MP3 audio using ElevenLabs
        stream = self.client.text_to_speech.convert(
            voice_id=spk,
            model_id=self.model_name,
            text=text,
            output_format="mp3_44100_128"
        )

        # join chunks if needed
        audio_bytes = b"".join(stream) if not isinstance(stream, (bytes, bytearray)) else stream

        # decode MP3 bytes to AudioSegment
        audio_seg = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        # set sample rate
        self.sample_rate = audio_seg.frame_rate

        # PCM -> float32
        pcm_int16 = np.frombuffer(audio_seg.raw_data, dtype=np.int16)
        # normalize to [-1,1]
        wav = pcm_int16.astype(np.float32) / np.iinfo(np.int16).max
        # return wav
        return wav

    def write_audio(self, wav: np.ndarray, path: str = "out.wav") -> None:
        """
        Save the audio array to a WAV file

        :param wav: float32 numpy array of audio samples.
        :param path: output file path (e.g. "out.wav").
        """
        sf.write(path, wav, self.sample_rate)

    def speak(self, text: str, speaker: str = None) -> None:
        """
        Synthesize and play text through speakers using ElevenLabs built-in play().
        :param text:    Text to speak.
        :param speaker: Overrides default voice ID for this utterance.
        """
        spk = speaker or self.voice_id
        stream = self.client.text_to_speech.convert(
            voice_id=spk,
            model_id=self.model_name,
            text=text,
            output_format="mp3_44100_128",
        )
        # play the audio
        play(stream)


def main():
    tts = TTS_Engine()
    print(tts.list_speakers())

if __name__ == "__main__":
    main()
