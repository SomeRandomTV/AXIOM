import os
import torch
import numpy as np
import pyaudio
from huggingface_hub import snapshot_download
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

class TTSEngine:
    def __init__(
        self,
        model_repo_id: str = "coqui/XTTS-v2",
        repo_type: str = "model",
        speaker_wav: str = "speaker_reference.wav",
        language: str = "en",
        device: str = None,
        cache_dir: str = "./model_cache",
    ):
        # Download the HF model repository (includes config, vocab, merges, checkpoint)
        self.model_path = snapshot_download(
            repo_id=model_repo_id,
            repo_type=repo_type,
            cache_dir=cache_dir,
        )

        # Load XTTS configuration
        config = XttsConfig()
        config_file = os.path.join(self.model_path, "config.json")
        config.load_json(config_file)

        # Ensure tokenizer files point to the downloaded repo
        tok_file = getattr(config.model_args, 'tokenizer_file', None)
        if tok_file:
            config.model_args.tokenizer_file = os.path.join(self.model_path, tok_file)
        merge_file = getattr(config.model_args, 'merge_file', None)
        if merge_file:
            config.model_args.merge_file = os.path.join(self.model_path, merge_file)

        # Initialize XTTS model
        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(config, checkpoint_dir=self.model_path)

        # Move model to device
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(torch.device(self.device))
        self.language = language

        # Precompute speaker and GPT latents from reference audio
        gpt_latent, speaker_embed = self.model.get_conditioning_latents(
            audio_path=[speaker_wav]
        )
        self.gpt_latent = gpt_latent.to(self.device)
        self.speaker_embed = speaker_embed.to(self.device)

        # PyAudio setup (match model sample rate, default 24000 Hz)
        self.pyaudio = pyaudio.PyAudio()
        self.rate = config.audio.output_sample_rate
        self.stream = None

    def stream_speak(self, text: str) -> None:
        # Lazily open the audio stream
        if self.stream is None:
            self.stream = self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.rate,
                output=True,
            )

        # Stream inference chunks as PCM audio
        for chunk in self.model.inference_stream(
            text,
            self.language,
            self.gpt_latent,
            self.speaker_embed,
        ):
            pcm = chunk.cpu().numpy().astype(np.float32)
            self.stream.write(pcm.tobytes())

    def close(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pyaudio.terminate()

# Example usage
if __name__ == "__main__":
    engine = TTSEngine(
        model_repo_id="coqui/XTTS-v2",
        speaker_wav="speech_reference.wav"
    )
    try:
        print("Streaming with proper tokenizer files now.")
        engine.stream_speak("Hello! Streaming with proper tokenizer files now.")
        engine.stream_speak("This is a test of the streaming API and latency.")
    finally:
        engine.close()
