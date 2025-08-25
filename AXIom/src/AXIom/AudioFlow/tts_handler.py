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
Enhanced Module: TTSHandler (Python 3.12 Compatible)
Provides fast, flexible text-to-speech synthesis using:
- gTTS for cloud-based synthesis (primary)
- Real-time audio streaming capabilities
- Cross-platform audio playback with timeout protection
- Enhanced fallback mechanisms
"""


class TTSHandler:
    def __init__(self,
                 lang: str = 'en',
                 slow: bool = False,
                 log_level: int = logging.INFO,
                 streaming: bool = True,
                 timeout: float = 10.0):
        """
        Initialize enhanced TTSHandler with cloud TTS and streaming capabilities.

        Args:
            lang (str): Language code (default 'en').
            slow (bool): Use slower speech speed (default False).
            log_level (int): Logging level (default logging.INFO).
            streaming (bool): Enable real-time streaming (default True).
            timeout (float): Default timeout for TTS operations (default 10.0).
        """
        self.lang = lang
        self.slow = slow
        self.streaming = streaming
        self.default_timeout = timeout
        self.logger = self._setup_logger(log_level)

        # Streaming components
        self.audio_queue = queue.Queue()
        self.is_streaming = False
        self.stream_thread = None
        self.audio_stream = None

        # Performance metrics
        self.synthesis_times = []
        self.streaming_latency = []

        # Audio playback method priority
        self._init_audio_methods()

    def _init_audio_methods(self):
        """Initialize available audio playback methods."""
        self.audio_methods = []

        # Check system players first (better MP3 compatibility)
        ffplay = shutil.which('ffplay')
        if ffplay:
            self.audio_methods.append('ffplay')

        if sys.platform == "darwin":
            afplay = shutil.which('afplay')
            if afplay:
                self.audio_methods.append('afplay')

        # Check PyAudio (good for WAV, problematic for MP3)
        if PYAUDIO_AVAILABLE:
            self.audio_methods.append('pyaudio')

        # Always available fallback
        self.audio_methods.append('file')

        self.logger.info(f"Available audio methods: {self.audio_methods}")

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

    def synthesize_to_file(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech and save as an MP3 file using gTTS.

        Args:
            text (str): Text to convert.
            output_path (str, optional): Path to save the file. Defaults to system temp.

        Raises:
            ValueError: If text is empty.

        Returns:
            str: Path to the saved MP3 file.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        start_time = time.time()

        try:
            tts = gTTS(text=text, lang=self.lang, slow=self.slow)
            if output_path is None:
                output_path = os.path.join(tempfile.gettempdir(), 'tts_cloud.mp3')
            tts.save(output_path)

            synthesis_time = time.time() - start_time
            self.synthesis_times.append(synthesis_time)

            self.logger.info(f"Cloud TTS synthesis completed in {synthesis_time:.2f}s")
            self.logger.info(f"Saved TTS audio to {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"TTS synthesis failed: {e}")
            raise

    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Convert text to speech and return MP3 data as bytes.

        Args:
            text (str): Text to convert.

        Raises:
            ValueError: If text is empty.

        Returns:
            bytes: MP3 audio data in memory.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        start_time = time.time()

        try:
            tts = gTTS(text=text, lang=self.lang, slow=self.slow)
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)

            synthesis_time = time.time() - start_time
            self.synthesis_times.append(synthesis_time)

            self.logger.info(f"Cloud TTS synthesis to memory completed in {synthesis_time:.2f}s")
            return buffer.getvalue()

        except Exception as e:
            self.logger.error(f"TTS synthesis to memory failed: {e}")
            raise

    def stream_speak(self, text: str, chunk_size: int = 50, timeout: float = None) -> None:
        """
        Stream text-to-speech in real-time by processing text in chunks.

        Args:
            text (str): Text to speak.
            chunk_size (int): Number of characters per chunk for streaming.
            timeout (float): Timeout for each chunk synthesis.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        if not self.streaming:
            self.logger.warning("Streaming not enabled, falling back to regular speak")
            return self.speak(text, timeout=timeout)

        timeout = timeout or self.default_timeout

        # Split text into chunks for streaming
        text_chunks = self._chunk_text(text, chunk_size)

        print(f"ARA: {text}")
        self.logger.info(f"Starting streaming TTS with {len(text_chunks)} chunks")

        # Start streaming thread
        self.is_streaming = True
        self.stream_thread = threading.Thread(
            target=self._stream_audio_chunks,
            args=(text_chunks, timeout)
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

    def _stream_audio_chunks(self, text_chunks: list, timeout: float):
        """Stream text-to-speech in real-time by processing text in chunks."""
        try:
            # Process all chunks first, then play them sequentially
            audio_chunks = []

            for i, chunk in enumerate(text_chunks):
                if not self.is_streaming:
                    break

                start_time = time.time()

                # Synthesize chunk with timeout
                try:
                    audio_bytes = self.synthesize_to_bytes(chunk)

                    # Store chunk with its data
                    audio_chunks.append((i, audio_bytes))

                    synthesis_time = time.time() - start_time
                    self.synthesis_times.append(synthesis_time)

                    self.logger.debug(f"Chunk {i + 1}/{len(text_chunks)} synthesized in {synthesis_time:.2f}s")

                except Exception as e:
                    self.logger.error(f"Failed to synthesize chunk {i + 1}: {e}")
                    continue

                # Small delay between synthesis to prevent overwhelming
                time.sleep(0.1)

            # Now play all chunks sequentially
            if audio_chunks:
                self.logger.info(f"Playing {len(audio_chunks)} audio chunks sequentially...")
                self._play_chunks_sequentially(audio_chunks)

        except Exception as e:
            self.logger.error(f"Streaming failed: {e}")
        finally:
            self.is_streaming = False

    def _play_chunks_sequentially(self, audio_chunks):
        """Play audio chunks one after another without overlap."""
        try:
            for i, (chunk_id, audio_data) in enumerate(audio_chunks):
                if not self.is_streaming:
                    break

                self.logger.debug(f"Playing chunk {chunk_id + 1}/{len(audio_chunks)}")

                # Play this chunk using the best available method
                start_time = time.time()
                self._play_audio_chunk(audio_data)

                playback_time = time.time() - start_time
                self.streaming_latency.append(playback_time)

                self.logger.debug(f"Chunk {chunk_id + 1} played in {playback_time:.2f}s")

                # Wait for this chunk to finish before playing the next
                # This prevents overlap and ensures sequential playback
                time.sleep(0.5)  # Buffer time between chunks

        except Exception as e:
            self.logger.error(f"Sequential chunk playback failed: {e}")

    def _play_audio_chunk(self, audio_bytes):
        """Play a single audio chunk using the best available method."""
        # Try different audio methods in priority order
        for method in self.audio_methods:
            try:
                if method == 'ffplay':
                    self._play_chunk_with_ffplay(audio_bytes)
                    return
                elif method == 'afplay':
                    self._play_chunk_with_afplay(audio_bytes)
                    return
                elif method == 'file':
                    self._play_chunk_with_file(audio_bytes)
                    return
                # Skip PyAudio for streaming as it has format issues
            except Exception as e:
                self.logger.debug(f"Audio method {method} failed for chunk: {e}")
                continue

        # If all methods failed, log the error
        self.logger.warning("All audio methods failed for chunk playback")

    def _play_chunk_with_ffplay(self, audio_bytes):
        """Play audio chunk using ffplay with proper completion detection."""
        try:
            # Use ffplay with autoexit to ensure it completes
            proc = subprocess.Popen(
                ['ffplay', '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Send audio data and wait for completion
            proc.communicate(audio_bytes, timeout=10.0)

            # Ensure process is completely finished
            if proc.poll() is None:
                proc.terminate()
                proc.wait()

        except subprocess.TimeoutExpired:
            self.logger.warning("ffplay chunk playback timed out, killing process")
            proc.kill()
            proc.wait()
            raise Exception("ffplay chunk playback timed out")
        except Exception as e:
            raise Exception(f"ffplay chunk playback failed: {e}")

    def _play_chunk_with_afplay(self, audio_bytes):
        """Play audio chunk using afplay with proper completion detection."""
        try:
            # Convert MP3 to WAV for afplay
            import tempfile
            import subprocess

            mp3_temp = os.path.join(tempfile.gettempdir(), f'chunk_{time.time()}.mp3')
            wav_temp = os.path.join(tempfile.gettempdir(), f'chunk_{time.time()}.wav')

            # Save MP3 bytes
            with open(mp3_temp, 'wb') as f:
                f.write(audio_bytes)

            # Convert to WAV
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', mp3_temp, '-f', 'wav', wav_temp
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=5.0)

            if os.path.exists(wav_temp):
                # Play WAV file and wait for completion
                result = subprocess.run(['afplay', wav_temp], timeout=10.0)

                # Clean up
                try:
                    os.remove(mp3_temp)
                    os.remove(wav_temp)
                except:
                    pass
            else:
                raise Exception("WAV conversion failed")

        except Exception as e:
            raise Exception(f"afplay chunk playback failed: {e}")

    def _play_chunk_with_file(self, audio_bytes):
        """Play audio chunk by saving to file and using system player."""
        try:
            import tempfile

            # Save to temporary MP3 file
            temp_file = os.path.join(tempfile.gettempdir(), f'chunk_{time.time()}.mp3')
            with open(temp_file, 'wb') as f:
                f.write(audio_bytes)

            # Play using system player
            self.play_audio(temp_file)

            # Wait for playback to complete (estimate based on file size)
            # Rough estimate: 1 second per 10KB of audio data
            estimated_duration = max(1, len(audio_bytes) / 10000)
            time.sleep(estimated_duration)

            # Clean up
            try:
                os.remove(temp_file)
            except:
                pass

        except Exception as e:
            raise Exception(f"File chunk playback failed: {e}")

    def speak(self, text: str, timeout: float = None) -> None:
        """
        Speak text using available playback method with timeout protection.

        Args:
            text (str): Text to speak.
            timeout (float): Maximum time to wait for TTS completion in seconds.
        """
        if not text:
            raise ValueError("Text must not be empty. ARA must say something.")

        timeout = timeout or self.default_timeout

        print(f"ARA: {text}")

        # Use threading with timeout to prevent hanging
        result_queue = queue.Queue()
        error_queue = queue.Queue()

        def _speak_worker():
            try:
                # Try different audio methods in priority order
                for method in self.audio_methods:
                    try:
                        if method == 'pyaudio':
                            self._speak_with_pyaudio(text)
                        elif method == 'ffplay':
                            self._speak_ffplay(text)
                        elif method == 'afplay':
                            self._speak_afplay(text)
                        elif method == 'file':
                            self._fallback_speak(text)

                        result_queue.put("success")
                        return

                    except Exception as e:
                        self.logger.warning(f"Audio method '{method}' failed: {e}")
                        continue

                # If all methods failed
                error_queue.put(Exception("All audio methods failed"))

            except Exception as e:
                error_queue.put(e)

        # Start TTS in separate thread
        tts_thread = threading.Thread(target=_speak_worker)
        tts_thread.daemon = True
        tts_thread.start()

        # Wait for completion with timeout
        try:
            tts_thread.join(timeout=timeout)

            if tts_thread.is_alive():
                self.logger.warning(f"TTS operation timed out after {timeout}s")
                # Force fallback
                try:
                    self._fallback_speak(text)
                except Exception as fallback_error:
                    self.logger.error(f"Fallback TTS also failed: {fallback_error}")
            else:
                # Check for errors
                try:
                    error = error_queue.get_nowait()
                    self.logger.error(f"TTS failed: {error}")
                    # Try fallback
                    try:
                        self._fallback_speak(text)
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback TTS also failed: {fallback_error}")
                except queue.Empty:
                    # No errors, success
                    pass

        except Exception as e:
            self.logger.error(f"Unexpected error in TTS: {e}")
            # Final fallback attempt
            try:
                self._fallback_speak(text)
            except Exception as final_error:
                self.logger.error(f"All TTS methods failed: {final_error}")

    def _speak_with_pyaudio(self, text: str):
        """Speak using PyAudio for direct playback."""
        if not PYAUDIO_AVAILABLE:
            raise Exception("PyAudio not available")

        audio_bytes = self.synthesize_to_bytes(text)

        # Create temporary audio stream with proper settings
        audio = pyaudio.PyAudio()

        # Try to determine audio format from the MP3 data
        # For MP3 from gTTS, we need to convert to proper format
        try:
            # Use ffmpeg to convert MP3 to WAV for better PyAudio compatibility
            import subprocess
            import tempfile

            # Create temporary files
            mp3_temp = os.path.join(tempfile.gettempdir(), 'tts_temp.mp3')
            wav_temp = os.path.join(tempfile.gettempdir(), 'tts_temp.wav')

            # Save MP3 bytes to temp file
            with open(mp3_temp, 'wb') as f:
                f.write(audio_bytes)

            # Convert MP3 to WAV using ffmpeg
            ffmpeg_cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', mp3_temp,  # Input MP3
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '22050',  # Sample rate
                '-ac', '1',  # Mono
                wav_temp  # Output WAV
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True, timeout=10.0)

            if result.returncode == 0 and os.path.exists(wav_temp):
                # Read WAV file and play with PyAudio
                with open(wav_temp, 'rb') as f:
                    wav_data = f.read()

                # Skip WAV header (44 bytes) to get raw PCM data
                pcm_data = wav_data[44:]

                # Create PyAudio stream
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,
                    output=True,
                    frames_per_buffer=1024
                )

                # Play audio
                stream.write(pcm_data)
                stream.stop_stream()
                stream.close()
                audio.terminate()

                self.logger.info("Audio played directly using PyAudio (converted)")

                # Clean up temp files
                try:
                    os.remove(mp3_temp)
                    os.remove(wav_temp)
                except:
                    pass

            else:
                raise Exception("FFmpeg conversion failed")

        except Exception as e:
            self.logger.warning(f"PyAudio conversion failed: {e}, falling back to direct playback")

            # Fallback: try direct MP3 playback (might not work well)
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,
                    output=True,
                    frames_per_buffer=1024
                )

                # Convert MP3 bytes to something PyAudio can handle
                # This is a basic conversion that might not work perfectly
                import struct
                # Try to extract some audio data (this is a simplified approach)
                audio_data = audio_bytes[1000:10000]  # Skip header, take some data
                if len(audio_data) > 0:
                    # Convert to 16-bit PCM (this is very basic)
                    pcm_data = struct.pack('h' * (len(audio_data) // 2),
                                           *[int(b) * 256 for b in audio_data[::2]])
                    stream.write(pcm_data)

                stream.stop_stream()
                stream.close()
                audio.terminate()

                self.logger.info("Audio played with basic PyAudio fallback")

            except Exception as fallback_error:
                self.logger.error(f"PyAudio fallback also failed: {fallback_error}")
                audio.terminate()
                raise

    def _speak_ffplay(self, text: str) -> None:
        """
        Play streamed audio in memory using ffplay.

        Args:
            text (str): Text to convert and speak.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using ffplay...")
            proc = subprocess.Popen(
                ['ffplay', '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.communicate(audio_bytes, timeout=10.0)
        except subprocess.TimeoutExpired:
            self.logger.warning("ffplay timed out, killing process")
            proc.kill()
            raise Exception("ffplay timed out")
        except Exception as e:
            self.logger.warning(f"ffplay failed ({e})")
            raise
        finally:
            self.logger.info("Done speaking (ffplay).")

    def _speak_afplay(self, text: str) -> None:
        """
        Play streamed audio in memory using afplay (macOS).

        Args:
            text (str): Text to convert and speak.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using afplay...")
            # afplay doesn't support stdin, so we need to save to temp file first
            temp_file = os.path.join(tempfile.gettempdir(), 'tts_afplay_temp.wav')

            # Convert MP3 bytes to WAV format for afplay
            try:
                # Try to use ffmpeg to convert MP3 to WAV
                import subprocess
                ffmpeg_proc = subprocess.Popen(
                    ['ffmpeg', '-f', 'mp3', '-i', '-', '-f', 'wav', temp_file],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                ffmpeg_proc.communicate(audio_bytes, timeout=10.0)

                if os.path.exists(temp_file):
                    # Play the WAV file with afplay
                    proc = subprocess.run(['afplay', temp_file], timeout=10.0)
                    self.logger.info("Done speaking (afplay).")
                else:
                    raise Exception("Failed to create WAV file")

            except Exception as e:
                self.logger.warning(f"afplay conversion failed ({e}), falling back to direct playback")
                # Fallback: try to play MP3 directly (might not work)
                proc = subprocess.Popen(['afplay', '-'], stdin=subprocess.PIPE)
                proc.communicate(audio_bytes, timeout=10.0)
                self.logger.info("Done speaking (afplay fallback).")

        except subprocess.TimeoutExpired:
            self.logger.warning("afplay timed out, killing process")
            if 'proc' in locals():
                proc.kill()
            raise Exception("afplay timed out")
        except Exception as e:
            self.logger.warning(f"afplay in-memory failed ({e})")
            raise
        finally:
            # Clean up temp file
            if 'temp_file' in locals() and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def _fallback_speak(self, text: str) -> None:
        """Fallback to saving audio to a file and using default system playback."""
        path = self.synthesize_to_file(text)
        try:
            self.logger.info("Trying to fallback to file playback...")
            self.play_audio(path)
            # Wait for playback to complete
            time.sleep(2)
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

    def get_performance_stats(self) -> dict:
        """Get performance statistics for TTS operations."""
        stats = {
            'total_syntheses': len(self.synthesis_times),
            'avg_synthesis_time': 0,
            'total_streaming_operations': len(self.streaming_latency),
            'avg_streaming_latency': 0,
            'streaming_enabled': self.streaming,
            'available_audio_methods': self.audio_methods,
            'pyaudio_available': PYAUDIO_AVAILABLE
        }

        if self.synthesis_times:
            stats['avg_synthesis_time'] = sum(self.synthesis_times) / len(self.synthesis_times)

        if self.streaming_latency:
            stats['avg_streaming_latency'] = sum(self.streaming_latency) / len(self.streaming_latency)

        return stats

    def test_audio(self) -> bool:
        """Test audio playback capabilities and return success status."""
        self.logger.info("Testing audio playback capabilities...")

        # Test PyAudio if available
        if PYAUDIO_AVAILABLE:
            try:
                audio = pyaudio.PyAudio()
                device_count = audio.get_device_count()
                self.logger.info(f"PyAudio: {device_count} audio devices found")

                # Test basic audio stream creation
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,
                    output=True,
                    frames_per_buffer=1024
                )
                stream.close()
                audio.terminate()

                self.logger.info("PyAudio test: SUCCESS")
                return True

            except Exception as e:
                self.logger.error(f"PyAudio test: FAILED - {e}")
                return False
        else:
            self.logger.info("PyAudio not available")
            return False

    def get_audio_info(self) -> dict:
        """Get information about available audio capabilities."""
        info = {
            'pyaudio_available': PYAUDIO_AVAILABLE,
            'system_audio_players': {}
        }

        # Check system audio players
        ffplay = shutil.which('ffplay')
        afplay = shutil.which('afplay') if sys.platform == "darwin" else None

        info['system_audio_players']['ffplay'] = ffplay is not None
        info['system_audio_players']['afplay'] = afplay is not None

        # Check PyAudio details if available
        if PYAUDIO_AVAILABLE:
            try:
                audio = pyaudio.PyAudio()
                info['pyaudio_devices'] = audio.get_device_count()
                info['pyaudio_default_output'] = audio.get_default_output_device_info()
                audio.terminate()
            except Exception as e:
                info['pyaudio_error'] = str(e)

        return info

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

    def wait_for_completion(self, timeout: float = 30.0) -> bool:
        """
        Wait for TTS operations to complete.

        Args:
            timeout (float): Maximum time to wait in seconds.

        Returns:
            bool: True if completed, False if timed out.
        """
        start_time = time.time()

        # Wait for streaming to complete
        while self.is_streaming and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        # Wait for audio queue to empty
        while not self.audio_queue.empty() and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        # Additional buffer time for audio playback
        time.sleep(0.5)

        if self.is_streaming:
            self.logger.warning("TTS completion timeout, forcing stop")
            self.stop_streaming()
            return False

        return True
