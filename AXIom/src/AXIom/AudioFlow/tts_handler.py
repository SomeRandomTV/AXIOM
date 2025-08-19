import os
import sys
import io
import tempfile
import subprocess
import logging
import shutil
import asyncio
import threading
import queue
import time
from typing import Optional, Callable, Union
from gtts import gTTS

# Try to import Coqui TTS for local synthesis
try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    TTS = None

# Try to import audio playback libraries
try:
    import pyaudio
    import numpy as np
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None
    np = None

"""
Enhanced Module: TTSHandler
Provides fast, flexible text-to-speech synthesis using multiple engines:
- Coqui TTS for high-quality local synthesis with streaming
- gTTS for cloud-based synthesis as fallback
- Real-time audio streaming capabilities
- Cross-platform audio playback
"""
class TTSHandler:
    def __init__(self, 
                 lang: str = 'en', 
                 slow: bool = False, 
                 log_level: int = logging.INFO,
                 use_local: bool = True,
                 streaming: bool = True,
                 voice_model: str = None):
        """
        Initialize enhanced TTSHandler with local and streaming capabilities.

        Args:
            lang (str): Language code (default 'en').
            slow (bool): Use slower speech speed (default False).
            log_level (int): Logging level (default logging.INFO).
            use_local (bool): Prioritize local TTS over cloud (default True).
            streaming (bool): Enable real-time streaming (default True).
            voice_model (str): Specific Coqui TTS model to use.
        """
        self.lang = lang
        self.slow = slow
        self.use_local = use_local
        self.streaming = streaming
        self.voice_model = voice_model
        self.logger = self._setup_logger(log_level)
        
        # Initialize TTS engines
        self._init_tts_engines()
        
        # Streaming components
        self.audio_queue = queue.Queue()
        self.is_streaming = False
        self.stream_thread = None
        self.audio_stream = None
        
        # Performance metrics
        self.synthesis_times = []
        self.streaming_latency = []

    def _init_tts_engines(self):
        """Initialize available TTS engines."""
        self.coqui_tts = None
        self.available_models = []
        
        if COQUI_AVAILABLE:
            try:
                # Get available models
                self.available_models = TTS.list_models()
                self.logger.info(f"Available Coqui TTS models: {len(self.available_models)}")
                
                # Select appropriate model
                if self.voice_model:
                    if self.voice_model in self.available_models:
                        model_name = self.voice_model
                    else:
                        self.logger.warning(f"Specified model {self.voice_model} not found, using default")
                        model_name = self._get_default_model()
                else:
                    model_name = self._get_default_model()
                
                # Initialize Coqui TTS
                self.coqui_tts = TTS(model_name=model_name)
                self.logger.info(f"Initialized Coqui TTS with model: {model_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Coqui TTS: {e}")
                self.coqui_tts = None
        
        if not self.coqui_tts:
            self.logger.info("Coqui TTS not available, will use gTTS fallback")

    def _get_default_model(self) -> str:
        """Get the best default model for the specified language."""
        # Priority order for English models
        english_models = [
            "tts_models/en/ljspeech/tacotron2-DDC",
            "tts_models/en/ljspeech/fast_pitch",
            "tts_models/en/vctk/vits",
            "tts_models/en/ljspeech/glow-tts"
        ]
        
        # Check for available English models
        for model in english_models:
            if model in self.available_models:
                return model
        
        # Fallback to first available model
        if self.available_models:
            return self.available_models[0]
        
        return "tts_models/en/ljspeech/tacotron2-DDC"

    def _setup_logger(self, level: int) -> logging.Logger:
        """
        Set up and return a logger for the TTSHandler.

        Args:
            level (int): Logging level.

        Returns:
            logging.Logger: Configured logger.
        """
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=level
        )
        return logging.getLogger('EnhancedTTSHandler')

    def synthesize_to_file(self, text: str, output_path: str = None, use_local: bool = None) -> str:
        """
        Convert text to speech and save as an audio file using best available engine.

        Args:
            text (str): Text to convert.
            output_path (str, optional): Path to save the file. Defaults to system temp.
            use_local (bool, optional): Force local or cloud TTS. Defaults to instance setting.

        Raises:
            ValueError: If text is empty.

        Returns:
            str: Path to the saved audio file.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        use_local = use_local if use_local is not None else self.use_local
        
        start_time = time.time()
        
        try:
            if use_local and self.coqui_tts:
                # Use Coqui TTS for local synthesis
                if output_path is None:
                    output_path = os.path.join(tempfile.gettempdir(), 'tts_local.wav')
                
                self.coqui_tts.tts_to_file(text=text, file_path=output_path)
                self.logger.info(f"Local TTS synthesis completed in {time.time() - start_time:.2f}s")
                
            else:
                # Fallback to gTTS
                if output_path is None:
                    output_path = os.path.join(tempfile.gettempdir(), 'tts_cloud.mp3')
                
                tts = gTTS(text=text, lang=self.lang, slow=self.slow)
                tts.save(output_path)
                self.logger.info(f"Cloud TTS synthesis completed in {time.time() - start_time:.2f}s")
            
            synthesis_time = time.time() - start_time
            self.synthesis_times.append(synthesis_time)
            
            self.logger.info(f"Saved TTS audio to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"TTS synthesis failed: {e}")
            # Fallback to gTTS if local fails
            if use_local and self.coqui_tts:
                self.logger.info("Falling back to gTTS...")
                return self.synthesize_to_file(text, output_path, use_local=False)
            raise

    def synthesize_to_bytes(self, text: str, use_local: bool = None) -> bytes:
        """
        Convert text to speech and return audio data as bytes.

        Args:
            text (str): Text to convert.
            use_local (bool, optional): Force local or cloud TTS. Defaults to instance setting.

        Raises:
            ValueError: If text is empty.

        Returns:
            bytes: Audio data in memory.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        use_local = use_local if use_local is not None else self.use_local
        
        try:
            if use_local and self.coqui_tts:
                # Use Coqui TTS for local synthesis
                audio_data = self.coqui_tts.tts(text=text)
                
                # Convert numpy array to bytes
                if np is not None:
                    audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                else:
                    # Fallback conversion
                    audio_bytes = audio_data.tobytes()
                
                self.logger.info("Local TTS synthesis to memory completed")
                return audio_bytes
                
            else:
                # Fallback to gTTS
                tts = gTTS(text=text, lang=self.lang, slow=self.slow)
                buffer = io.BytesIO()
                tts.write_to_fp(buffer)
                self.logger.info("Cloud TTS synthesis to memory completed")
                return buffer.getvalue()
                
        except Exception as e:
            self.logger.error(f"TTS synthesis to memory failed: {e}")
            # Fallback to gTTS if local fails
            if use_local and self.coqui_tts:
                self.logger.info("Falling back to gTTS...")
                return self.synthesize_to_bytes(text, use_local=False)
            raise

    def stream_speak(self, text: str, chunk_size: int = 50, use_local: bool = None) -> None:
        """
        Stream text-to-speech in real-time by processing text in chunks.

        Args:
            text (str): Text to speak.
            chunk_size (int): Number of characters per chunk for streaming.
            use_local (bool, optional): Force local or cloud TTS. Defaults to instance setting.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        if not self.streaming:
            self.logger.warning("Streaming not enabled, falling back to regular speak")
            return self.speak(text)

        use_local = use_local if use_local is not None else self.use_local
        
        # Split text into chunks for streaming
        text_chunks = self._chunk_text(text, chunk_size)
        
        print(f"ARA: {text}")
        self.logger.info(f"Starting streaming TTS with {len(text_chunks)} chunks")
        
        # Start streaming thread
        self.is_streaming = True
        self.stream_thread = threading.Thread(
            target=self._stream_audio_chunks,
            args=(text_chunks, use_local)
        )
        self.stream_thread.start()

    def _chunk_text(self, text: str, chunk_size: int) -> list:
        """Split text into chunks for streaming synthesis."""
        chunks = []
        current_chunk = ""
        
        for char in text:
            current_chunk += char
            
            # Break on sentence boundaries or chunk size
            if (char in '.!?' and len(current_chunk) >= chunk_size // 2) or \
               len(current_chunk) >= chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        # Add remaining text
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _stream_audio_chunks(self, text_chunks: list, use_local: bool):
        """Stream audio chunks in real-time."""
        try:
            for i, chunk in enumerate(text_chunks):
                if not self.is_streaming:
                    break
                
                start_time = time.time()
                
                # Synthesize chunk
                try:
                    if use_local and self.coqui_tts:
                        audio_data = self.coqui_tts.tts(text=chunk)
                        if np is not None:
                            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
                        else:
                            audio_bytes = audio_data.tobytes()
                    else:
                        # Fallback to gTTS for chunks
                        tts = gTTS(text=chunk, lang=self.lang, slow=self.slow)
                        buffer = io.BytesIO()
                        tts.write_to_fp(buffer)
                        audio_bytes = buffer.getvalue()
                    
                    # Queue audio for playback
                    self.audio_queue.put((i, audio_bytes))
                    
                    synthesis_time = time.time() - start_time
                    self.synthesis_times.append(synthesis_time)
                    
                    self.logger.debug(f"Chunk {i+1}/{len(text_chunks)} synthesized in {synthesis_time:.2f}s")
                    
                except Exception as e:
                    self.logger.error(f"Failed to synthesize chunk {i+1}: {e}")
                    continue
                
                # Small delay between chunks for natural flow
                time.sleep(0.1)
            
            # Signal end of streaming
            self.audio_queue.put((None, None))
            
        except Exception as e:
            self.logger.error(f"Streaming failed: {e}")
        finally:
            self.is_streaming = False

    def _start_audio_stream(self):
        """Start audio playback stream."""
        if not PYAUDIO_AVAILABLE:
            self.logger.warning("PyAudio not available, cannot start audio stream")
            return False
        
        try:
            self.audio_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=22050,  # Standard rate for TTS
                output=True
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")
            return False

    def _play_audio_stream(self):
        """Play audio from the queue in real-time."""
        if not self._start_audio_stream():
            return
        
        try:
            while self.is_streaming or not self.audio_queue.empty():
                try:
                    chunk_id, audio_data = self.audio_queue.get(timeout=0.1)
                    
                    if chunk_id is None:  # End signal
                        break
                    
                    if audio_data:
                        start_time = time.time()
                        
                        # Play audio chunk
                        self.audio_stream.write(audio_data)
                        
                        playback_time = time.time() - start_time
                        self.streaming_latency.append(playback_time)
                        
                        self.logger.debug(f"Chunk {chunk_id+1} played in {playback_time:.2f}s")
                
                except queue.Empty:
                    continue
                except Exception as e:
                    self.logger.error(f"Failed to play audio chunk: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Audio streaming failed: {e}")
        finally:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

    def speak(self, text: str, use_local: bool = None) -> None:
        """
        Speak text using available playback method with enhanced engine selection.

        Args:
            text (str): Text to speak.
            use_local (bool, optional): Force local or cloud TTS. Defaults to instance setting.
        """
        if not text:
            raise ValueError("Text must not be empty. ARA must say something.")

        use_local = use_local if use_local is not None else self.use_local
        
        print(f"ARA: {text}")
        
        try:
            # Try local TTS first if available and requested
            if use_local and self.coqui_tts:
                self.logger.info("Using local Coqui TTS")
                self._speak_local(text)
            else:
                self.logger.info("Using cloud gTTS")
                self._speak_cloud(text)
                
        except Exception as e:
            self.logger.error(f"TTS failed: {e}")
            # Fallback to cloud TTS
            try:
                self._speak_cloud(text)
            except Exception as fallback_error:
                self.logger.error(f"Fallback TTS also failed: {fallback_error}")

    def _speak_local(self, text: str):
        """Speak using local Coqui TTS."""
        try:
            # Synthesize to memory first
            audio_data = self.coqui_tts.tts(text=text)
            
            # Try to play directly if PyAudio is available
            if PYAUDIO_AVAILABLE:
                self._play_audio_direct(audio_data)
            else:
                # Fallback to file-based playback
                self._fallback_speak(text, use_local=True)
                
        except Exception as e:
            self.logger.error(f"Local TTS failed: {e}")
            raise

    def _speak_cloud(self, text: str):
        """Speak using cloud gTTS with existing fallback methods."""
        try:
            ffplay = shutil.which('ffplay')
            afplay = shutil.which('afplay') if sys.platform == "darwin" else None

            if ffplay:
                self._speak_ffplay(text, ffplay)
            elif afplay:
                self._speak_afplay(text, afplay)
            else:
                self._fallback_speak(text, use_local=False)
        except Exception as e:
            self.logger.error(f"Cloud TTS failed: {e}")
            raise

    def _play_audio_direct(self, audio_data):
        """Play audio data directly using PyAudio."""
        try:
            if np is not None:
                # Convert to proper format
                audio_int16 = (audio_data * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
            else:
                audio_bytes = audio_data.tobytes()
            
            # Create temporary audio stream
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=22050,
                output=True
            )
            
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            self.logger.info("Audio played directly using PyAudio")
            
        except Exception as e:
            self.logger.error(f"Direct audio playback failed: {e}")
            raise

    def _fallback_speak(self, text: str, use_local: bool = False):
        """Fallback to saving audio to a file and using default system playback."""
        path = self.synthesize_to_file(text, use_local=use_local)
        try:
            self.logger.info("Trying to fallback to file playback...")
            self.play_audio(path)
        except Exception as e:
            self.logger.warning(f"Fallback to file playback failed ({e})")
        finally:
            if os.path.exists(path):
                os.remove(path)
                self.logger.info(f"Removed temporary TTS audio file {path}")

    def play_audio(self, file_path: str) -> None:
        """
        Play an audio file using the system default opener.

        Args:
            file_path (str): Path to the audio file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        opener = 'start' if os.name == 'nt' else ('open' if sys.platform == 'darwin' else 'xdg-open')
        os.system(f"{opener} '{file_path}'")

    def _speak_ffplay(self, text: str, ffplay_path: str) -> None:
        """
        Play streamed audio in memory using ffplay.

        Args:
            text (str): Text to convert and speak.
            ffplay_path (str): Path to ffplay binary.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using ffplay...")
            proc = subprocess.Popen(
                [ffplay_path, '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],
                stdin=subprocess.PIPE
            )
            proc.communicate(audio_bytes)
        except Exception as e:
            self.logger.warning(f"ffplay failed ({e})")
        finally:
            self.logger.info("Done speaking (ffplay).")

    def _speak_afplay(self, text: str, afplay_path: str) -> None:
        """
        Play streamed audio in memory using afplay (macOS).

        Args:
            text (str): Text to convert and speak.
            afplay_path (str): Path to afplay binary.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using afplay...")
            proc = subprocess.Popen([afplay_path, '-'], stdin=subprocess.PIPE)
            proc.communicate(audio_bytes)
        except Exception as e:
            self.logger.warning(f"afplay in-memory failed ({e}), will fallback to file")
        finally:
            self.logger.info("Done speaking (afplay).")

    def get_performance_stats(self) -> dict:
        """Get performance statistics for TTS operations."""
        stats = {
            'total_syntheses': len(self.synthesis_times),
            'avg_synthesis_time': 0,
            'total_streaming_operations': len(self.streaming_latency),
            'avg_streaming_latency': 0,
            'local_tts_available': self.coqui_tts is not None,
            'streaming_enabled': self.streaming,
            'available_models': len(self.available_models) if self.available_models else 0
        }
        
        if self.synthesis_times:
            stats['avg_synthesis_time'] = sum(self.synthesis_times) / len(self.synthesis_times)
        
        if self.streaming_latency:
            stats['avg_streaming_latency'] = sum(self.streaming_latency) / len(self.streaming_latency)
        
        return stats

    def stop_streaming(self):
        """Stop current streaming operation."""
        self.is_streaming = False
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)
        
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None

    def cleanup(self):
        """Clean up resources."""
        self.stop_streaming()
        # Clear queues
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break


def main():
    # Test the enhanced TTS handler
    tts = TTSHandler(use_local=True, streaming=True)
    
    print("Testing Enhanced TTS Handler...")
    print(f"Coqui TTS available: {COQUI_AVAILABLE}")
    print(f"PyAudio available: {PYAUDIO_AVAILABLE}")
    
    # Test regular speech
    tts.speak("Hello, this is ARA, the adaptive real-time assistant. Testing enhanced local TTS capabilities.")
    
    # Test streaming (if enabled)
    if tts.streaming:
        print("\nTesting streaming TTS...")
        tts.stream_speak("This is a test of real-time streaming text-to-speech. Each chunk should be processed and played as it becomes available.")
    
    # Show performance stats
    stats = tts.get_performance_stats()
    print(f"\nPerformance Stats: {stats}")
    
    # Cleanup
    tts.cleanup()


if __name__ == "__main__":
    main()




