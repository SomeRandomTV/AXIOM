import os
import sys
import signal
import logging

from AudioFlow import TTSHandler
from AudioFlow import MicHandler

from CmdCraft import CommandHandler
from CmdCraft import PromptHandler

from helpers.ollama_manager import OllamaManager

SYSTEM_PROMPT = "You are a helpful AI assistant. Keep responses short and friendly."

tts = None
mic = None
p_handler = None
c_handler = None
o_manager = None


def speak_and_wait(text: str, timeout: float = 15.0) -> None:
    """
    Helper function to speak text and wait for completion.

    Args:
        text (str): Text to speak
        timeout (float): Maximum time to wait for completion
    """
    global tts
    if tts:
        tts.speak(text, timeout=timeout)
        # Wait for completion with timeout
        tts.wait_for_completion(timeout=timeout)


def initialize_stuff() -> tuple[TTSHandler, MicHandler, PromptHandler, CommandHandler, OllamaManager]:
    """Initialize stuff like TTS and mic, command prompt, etc."""

    global tts, mic, p_handler, c_handler, o_manager

    print(f"{'=' * 15} Initializing the AXIom {'=' * 15}")

    try:
        # Initialize Ollama manager
        pid_file = os.path.join(os.path.dirname(__file__), "ollama.pid")
        o_manager = OllamaManager(pid_file)

        print("Checking Ollama status...")
        # Use the comprehensive check instead of basic check
        status = o_manager.check_ollama_comprehensive()

        if status['status'] == 0:
            serve_processes = [p for p in status['processes'] if p['is_serve']]
            if serve_processes:
                print(f"Ollama is already running ({len(serve_processes)} serve process(es)).")
            else:
                print("Ollama processes found but no 'serve' processes. Starting Ollama...")
                start_result = o_manager.start_ollama()
                if start_result == 0:
                    print("Ollama service started.")
                else:
                    print(f"Failed to start Ollama service (code: {start_result})")
                    raise Exception(f"Ollama startup failed with code: {start_result}")
        else:
            print("No Ollama processes found. Starting Ollama service...")
            start_result = o_manager.start_ollama()
            if start_result == 0:
                print("Ollama service started.")
            else:
                print(f"Failed to start Ollama service (code: {start_result})")
                # Show diagnosis for troubleshooting
                print("Ollama diagnosis:")
                o_manager.print_diagnosis()
                raise Exception(f"Ollama startup failed with code: {start_result}")

        # Initialize TTS with proper settings
        print("Initializing TTS handler...")
        tts = TTSHandler(
            lang="en",
            streaming=False,  # Disable streaming for more reliable speech
            timeout=15.0,  # Increase timeout for longer responses
            log_level=logging.INFO
        )

        # Test TTS immediately after initialization
        print("Testing TTS functionality...")
        test_result = tts.test_audio()
        if not test_result:
            print("Warning: Audio test failed, but continuing...")

        # Get audio info for diagnostics
        audio_info = tts.get_audio_info()
        print(f"Audio capabilities: {audio_info}")

        # Initialize other components
        mic = MicHandler()
        p_handler = PromptHandler(system_prompt=SYSTEM_PROMPT)
        c_handler = CommandHandler()

        print(f"{'=' * 15} Initializing stuff complete {'=' * 15}")

        # Use proper TTS method
        speak_and_wait("Initializing stuff complete. Ready to chat.")

        return tts, mic, p_handler, c_handler, o_manager

    except Exception as e:
        print(f"Error initializing stuff: {e}")

        # If initialization fails, show comprehensive Ollama diagnosis
        if o_manager:
            print("\nOllama diagnostic information:")
            o_manager.print_diagnosis()

        # Clean up any partially initialized components
        cleanup()
        sys.exit(1)


def cleanup():
    """Cleanup stuff like TTS and mic, command prompt, etc."""

    global tts, mic, p_handler, c_handler, o_manager

    print(f"\n{'=' * 15} Cleaning up AXIom {'=' * 15}")

    try:
        # Cleanup TTS with proper method
        if tts:
            print("Cleaning up TTS handler...")
            try:
                # Use the actual cleanup method from TTSHandler
                tts.cleanup()
                print("TTS handler cleaned up.")
            except Exception as e:
                print(f"Warning: Could not cleanup TTS: {e}")

        # Cleanup Microphone
        if mic:
            print("Cleaning up microphone handler...")
            try:
                if hasattr(mic, 'cleanup'):
                    mic.cleanup()
                elif hasattr(mic, 'stop'):
                    mic.stop()
                elif hasattr(mic, 'close'):
                    mic.close()
                print("Microphone handler cleaned up.")
            except Exception as e:
                print(f"Warning: Could not cleanup microphone: {e}")

        # Cleanup Command Handler
        if c_handler:
            print("Cleaning up command handler...")
            try:
                if hasattr(c_handler, 'cleanup'):
                    c_handler.cleanup()
                print("Command handler cleaned up.")
            except Exception as e:
                print(f"Warning: Could not cleanup command handler: {e}")

        # Cleanup Prompt Handler
        if p_handler:
            print("Cleaning up prompt handler...")
            try:
                if hasattr(p_handler, 'cleanup'):
                    p_handler.cleanup()
                print("Prompt handler cleaned up.")
            except Exception as e:
                print(f"Warning: Could not cleanup prompt handler: {e}")

        # Enhanced Ollama cleanup
        if o_manager:
            print("Stopping Ollama service...")
            try:
                # Check if there are multiple processes or untracked processes
                diagnosis = o_manager.diagnose_ollama_status()

                if diagnosis['total_processes'] > 1:
                    print(f"Found {diagnosis['total_processes']} Ollama processes. Using force stop to clean up all.")
                    stop_result = o_manager.force_stop_all_ollama()
                else:
                    # Use normal stop for single tracked process
                    stop_result = o_manager.stop_ollama()

                if stop_result == 0:
                    print("Ollama service stopped.")
                else:
                    print(f"Warning: Ollama stop returned code: {stop_result}")
                    # Try force stop as fallback
                    print("Attempting force stop as fallback...")
                    force_result = o_manager.force_stop_all_ollama()
                    if force_result == 0:
                        print("Force stop successful.")
                    else:
                        print("Force stop also failed. Some processes may still be running.")

            except Exception as e:
                print(f"Warning: Could not stop Ollama service: {e}")
                # Last resort: try force stop
                try:
                    print("Attempting emergency force stop...")
                    o_manager.force_stop_all_ollama()
                except Exception as force_e:
                    print(f"Emergency force stop failed: {force_e}")

        print(f"{'=' * 15} Cleanup complete {'=' * 15}")

    except Exception as e:
        print(f"Error during cleanup: {e}")


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    cleanup()
    sys.exit(0)


def main():
    """Main application loop"""

    global tts, mic, p_handler, c_handler, o_manager

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Initialize components
        tts, mic, p_handler, c_handler, o_manager = initialize_stuff()

        # Test TTS functionality with proper method
        print("\nTesting TTS functionality...")
        speak_and_wait("Hello! I am AURA, your Adaptive Real-time Assistant. How can I help you today?")

        # Main application loop
        print("\nStarting main application loop...")
        print("Say 'bye' or 'exit' to quit, or press Ctrl+C")
        print("For debugging, you can also say 'ollama status' to check Ollama processes")

        while True:
            try:
                # Get user input
                print("\n" + "=" * 50)
                user_input = mic.set_mic_input()
                print(f"User input: {user_input}")

                if not user_input:
                    speak_and_wait("Sorry, I didn't get that. Please try again.")
                    continue

                # Check for exit commands
                if user_input.lower() in ['bye', 'exit', 'quit', 'stop', 'goodbye']:
                    print("Goodbye! Shutting down ARA...")
                    speak_and_wait("Goodbye! Shutting down ARA.")
                    break

                # Debug command to check Ollama status
                if user_input.lower() in ['ollama status', 'check ollama', 'ollama debug']:
                    print("\n=== Ollama Status Debug ===")
                    o_manager.print_diagnosis()
                    speak_and_wait("Ollama status information printed to console.")
                    continue

                # Special command for TTS performance stats
                if user_input.lower() in ['tts stats', 'audio stats', 'performance stats']:
                    stats = tts.get_performance_stats()
                    print(f"\n=== TTS Performance Stats ===")
                    for key, value in stats.items():
                        print(f"{key}: {value}")
                    speak_and_wait("TTS performance statistics printed to console.")
                    continue

                # Process the command
                print("Processing your request...")

                # Get response from Ollama
                response = p_handler.chat(user_input)

                # Speak the response using proper method
                if response and response.strip():
                    print(f"ARA: {response}")  # Show response in terminal too

                    # Choose TTS method based on response length
                    if len(response) > 200 and tts.streaming:
                        # Use streaming for longer responses
                        print("Using streaming TTS for long response...")
                        tts.stream_speak(response, chunk_size=100, timeout=20.0)
                        # Wait for streaming to complete
                        tts.wait_for_completion(timeout=30.0)
                    else:
                        # Use regular speech for shorter responses
                        speak_and_wait(response, timeout=20.0)

                    print("Response complete. Ready for next command.")
                else:
                    print("No response received.")
                    # Check if Ollama is still running
                    status = o_manager.check_ollama_comprehensive()
                    if status['status'] != 0:
                        print("Warning: Ollama may have stopped. Attempting to restart...")
                        speak_and_wait("Connection issue detected. Attempting to restart service.")
                        start_result = o_manager.start_ollama()
                        if start_result == 0:
                            speak_and_wait("Service restarted. Please try again.")
                        else:
                            speak_and_wait("Service restart failed. Please check the system.")
                    else:
                        speak_and_wait("I'm sorry, I didn't get a response. Please try again.")

            except KeyboardInterrupt:
                print("\nInterrupted by user...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                if tts:
                    speak_and_wait("I encountered an error. Please try again.")

    except Exception as e:
        print(f"Fatal error in main: {e}")
        if tts:
            speak_and_wait("A fatal error occurred. Shutting down.")

    finally:
        cleanup()


# Additional utility function for manual debugging
def debug_ollama():
    """Standalone function to debug Ollama issues"""
    pid_file = os.path.join(os.path.dirname(__file__), "ollama.pid")
    manager = OllamaManager(pid_file)
    manager.interactive_management()


if __name__ == "__main__":
    # Check if running in debug mode
    if len(sys.argv) > 1 and sys.argv[1] == "--debug-ollama":
        debug_ollama()
    else:
        main()