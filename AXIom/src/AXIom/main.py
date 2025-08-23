# main.py
"""
Main function
All external files will be called here
"""
import os
import time
import sys
from CmdCraft import cmd_handler as ch
from CmdCraft import prompt_handler as ph
from AudioFlow import tts_handler as te
from AudioFlow import mic_handler as se
from dotenv import load_dotenv

load_dotenv()

# Test TTS import immediately
print("Testing TTS import...")
try:
    print(f"TTS module imported: {te}")
    print(f"TTSHandler class: {te.TTSHandler}")
    print("✓ TTS import successful")
except Exception as e:
    print(f"✗ TTS import failed: {e}")
    import traceback
    traceback.print_exc()

SYSTEM_PROMPT = "Your name is ARA(Adaptive real-time assistant, you are to keep your answers 1-3 sentences"

def initialize_tts():
    """Initialize TTS with enhanced capabilities and error handling."""
    try:
        print("🔊 Initializing TTS system...")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}...")  # Show first 3 paths
        
        # Initialize enhanced TTS handler with timeout protection
        print("Creating TTSHandler instance...")
        tts = te.TTSHandler(
            lang='en',
            streaming=True,  # Enable real-time streaming
            timeout=15.0,    # 15 second timeout for TTS operations
            log_level=te.logging.INFO
        )
        print("✓ TTSHandler instance created")
        
        # Test TTS functionality with explicit error handling
        print("Testing TTS system...")
        try:
            print("Attempting to speak test message...")
            tts.speak("TTS system initialized successfully.", timeout=10.0)
            print("✓ TTS test speech completed")
        except Exception as speech_error:
            print(f"⚠ TTS test speech failed: {speech_error}")
            import traceback
            traceback.print_exc()
            # Continue anyway, TTS might still work for other operations
        
        # Show available audio methods
        audio_info = tts.get_audio_info()
        print(f"✓ TTS initialized with audio methods: {tts.audio_methods}")
        print(f"Audio info: {audio_info}")
        
        return tts
        
    except Exception as e:
        print(f"✗ TTS initialization failed: {e}")
        import traceback
        traceback.print_exc()
        print("Falling back to basic TTS...")
        try:
            # Fallback to basic TTS
            tts = te.TTSHandler(streaming=False, timeout=10.0)
            print("Testing fallback TTS...")
            tts.speak("Basic TTS fallback initialized.", timeout=10.0)
            print("✓ Fallback TTS working")
            return tts
        except Exception as fallback_error:
            print(f"✗ TTS fallback also failed: {fallback_error}")
            import traceback
            traceback.print_exc()
            print("⚠ No TTS functionality available")
            return None

def initialize_ollama_service():
    """Initialize and start Ollama service once at startup."""
    try:
        print("🤖 Initializing Ollama service...")
        
        # Import here to avoid circular imports
        from CmdCraft.prompt_handler import OllamaManager
        
        # Create manager with the same PID file path
        pid_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ollama.pid")
        manager = OllamaManager(pid_file)
        
        # First check if Ollama is already responding to API calls
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                print("✓ Ollama service already running and responding")
                return manager
        except:
            pass
        
        # If API check fails, check PID file
        status = manager.check_ollama()
        if status == 0:
            print("✓ Ollama service already running (PID file)")
            return manager
        else:
            print("Starting Ollama service...")
            result = manager.start_ollama()
            if result == 0:
                print("✓ Ollama service started successfully")
                # Wait a moment for service to fully initialize
                time.sleep(2)
                return manager
            else:
                print(f"✗ Failed to start Ollama service: {result}")
                return None
                
    except Exception as e:
        print(f"✗ Ollama service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def shutdown_ollama_service(manager):
    """Shutdown Ollama service gracefully."""
    if manager:
        try:
            print("🛑 Shutting down Ollama service...")
            manager.stop_ollama()
            print("✓ Ollama service stopped")
        except Exception as e:
            print(f"⚠ Ollama shutdown warning: {e}")

def initialize_components():
    """Initialize all system components with error handling."""
    print("Initializing components...")
    
    # Initialize command handler
    try:
        handler = ch.CommandHandler()
        print("✓ Command handler initialized")
    except Exception as e:
        print(f"✗ Command handler failed: {e}")
        return None, None, None, None
    
    # Initialize prompt handler
    try:
        # Use the same PID file path as the main Ollama service
        pid_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "ollama.pid")
        p_handler = ph.PromptHandler(
            model="llama3:latest", 
            system_prompt=SYSTEM_PROMPT,
            pid_file=pid_file
        )
        print("✓ Prompt handler initialized")
    except Exception as e:
        print(f"✗ Prompt handler failed: {e}")
        return handler, None, None, None
    
    # Initialize TTS handler
    tts = initialize_tts()
    if not tts:
        print("⚠ Continuing without TTS functionality")
    
    # Initialize microphone handler
    try:
        mic = se.MicHandler()
        print("✓ Microphone handler initialized")
    except Exception as e:
        print(f"✗ Microphone handler failed: {e}")
        return handler, p_handler, tts, None
    
    print("✓ All components initialized successfully")
    return handler, p_handler, tts, mic

def process_user_input(handler, p_handler, tts, mic, user_input):
    """Process user input with enhanced error handling and TTS feedback."""
    try:
        print(f"User input: {user_input}")
        
        # Set and parse command
        handler.set_command(user_input)
        handler.parse_command()
        
        print("→ Function flag:", handler.function_flag)
        
        if handler.function_flag == 1:
            # Function call path
            print("→ Function call:", handler.function_call_name)
            print("→ Target:", handler.function_params)
            
            if tts:
                try:
                    tts.speak("Calling function...", timeout=5.0)
                    # Wait for audio to complete
                    time.sleep(2)
                except Exception as e:
                    print(f"TTS feedback failed: {e}")
            
        else:
            # LLM path
            print("Going to LLM...")
            
            try:
                result = p_handler.chat(user_input)
                print(f"LLM Response: {result}")
                
                # Use enhanced TTS with streaming for better user experience
                if tts:
                    try:
                        if len(result) > 100:  # Use streaming for long responses
                            print("Using streaming TTS for long response...")
                            tts.stream_speak(result, chunk_size=80, timeout=20.0)
                            # Wait for streaming to complete
                            time.sleep(3)
                        else:
                            print("Using regular TTS for short response...")
                            tts.speak(result, timeout=10.0)
                            # Wait for audio to complete
                            time.sleep(2)
                    except Exception as e:
                        print(f"TTS failed: {e}")
                        # Try fallback
                        try:
                            tts.speak("Response received.", timeout=5.0)
                            time.sleep(2)
                        except:
                            pass
                else:
                    print("TTS not available, response displayed only")
                    
            except Exception as e:
                print(f"✗ LLM processing failed: {e}")
                if tts:
                    try:
                        tts.speak("Sorry, I encountered an error processing your request.", timeout=5.0)
                        time.sleep(2)
                    except:
                        pass
        
        # Get function calls
        command = handler.get_function_calls()
        print(f"\nCommand: {command}")
        
        return True
        
    except ValueError as err:
        print(f"→ Error: {err}")
        if tts:
            try:
                tts.speak("I encountered an error processing your input.", timeout=5.0)
                time.sleep(2)
            except:
                pass
        return False
    except Exception as e:
        print(f"→ Unexpected error: {e}")
        if tts:
            try:
                tts.speak("An unexpected error occurred.", timeout=5.0)
                time.sleep(2)
            except:
                pass
        return False

def wait_for_audio_completion(tts, timeout=30):
    """Wait for TTS audio to complete before proceeding."""
    if not tts:
        return True
    
    try:
        print("Waiting for audio to complete...")
        
        # Use the TTS handler's built-in completion tracking
        if hasattr(tts, 'wait_for_completion'):
            completed = tts.wait_for_completion(timeout)
            if completed:
                print("✓ Audio completed successfully")
            else:
                print("⚠ Audio completion timeout")
        else:
            # Fallback method
            if hasattr(tts, 'is_streaming') and tts.is_streaming:
                print("Waiting for streaming audio to complete...")
                start_time = time.time()
                while tts.is_streaming and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if tts.is_streaming:
                    print("Streaming timeout, forcing stop...")
                    tts.stop_streaming()
                else:
                    print("Streaming completed")
            
            # Additional wait to ensure audio playback is finished
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"Error waiting for audio completion: {e}")
        return False

def prompt_for_next_command(tts):
    """Prompt user for next command after audio completion."""
    if tts:
        try:
            print("\n" + "="*50)
            print("🎯 Ready for next command...")
            tts.speak("Ready for your next command.", timeout=5.0)
            # Wait for prompt audio to complete
            time.sleep(2)
        except Exception as e:
            print(f"TTS prompt failed: {e}")
    else:
        print("\n" + "="*50)
        print("🎯 Ready for next command...")

def test_tts_functionality(tts):
    """Test TTS functionality with multiple methods."""
    if not tts:
        print("❌ No TTS available for testing")
        return False
    
    print("\n🧪 Testing TTS functionality...")
    
    test_messages = [
        "Hello, this is ARA speaking.",
        "Testing audio playback.",
        "System is ready for voice commands."
    ]
    
    for i, message in enumerate(test_messages, 1):
        try:
            print(f"Test {i}: {message}")
            tts.speak(message, timeout=8.0)
            print(f"✓ Test {i} completed")
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"✗ Test {i} failed: {e}")
            return False
    
    print("✅ All TTS tests passed")
    return True

def main():
    """Main application loop with enhanced error handling and TTS integration."""
    print("🚀 Starting AXIom - Adaptive Real-time Assistant")
    print("=" * 50)
    
    # Initialize Ollama service first (stays running)
    ollama_manager = initialize_ollama_service()
    if not ollama_manager:
        print("❌ Critical: Ollama service failed to start. Exiting.")
        return
    
    # Initialize components
    components = initialize_components()
    if not components or not all(components):
        print("❌ Critical component initialization failed. Exiting.")
        shutdown_ollama_service(ollama_manager)
        return
    
    handler, p_handler, tts, mic = components
    
    # Test TTS functionality before proceeding
    if tts:
        tts_working = test_tts_functionality(tts)
        if not tts_working:
            print("⚠ TTS tests failed, but continuing with limited functionality")
    else:
        print("⚠ No TTS available - running in text-only mode")
    
    print("\n🎯 AXIom is ready! Speak or type your commands.")
    print("Type 'exit' or 'quit' to stop the application.")
    print("-" * 50)
    
    # Main application loop
    try:
        while True:
            try:
                # Prompt for next command (after previous audio completion)
                prompt_for_next_command(tts)
                
                # Get microphone input
                print("🎤 Listening...")
                mic.set_mic_input()
                user_input = mic.get_text()
                
                if not user_input or user_input.strip() == "":
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'stop', 'end', 'bye']:
                    if tts:
                        try:
                            tts.speak("Shutting down AXIom. Goodbye!", timeout=5.0)
                            # Wait for shutdown audio to complete
                            time.sleep(3)
                        except:
                            pass
                    print("\n👋 Shutting down AXIom. Goodbye!")
                    break
                
                # Process user input
                success = process_user_input(handler, p_handler, tts, mic, user_input)
                
                if success:
                    print("✓ Command processed successfully")
                else:
                    print("⚠ Command processing had issues")
                
                # Wait for all audio to complete before next iteration
                wait_for_audio_completion(tts)
                
                # Brief pause for system stability
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user")
                if tts:
                    try:
                        tts.speak("Interrupted by user.", timeout=3.0)
                        time.sleep(2)
                    except:
                        pass
                break
            except Exception as e:
                print(f"\n💥 Unexpected error in main loop: {e}")
                if tts:
                    try:
                        tts.speak("System error occurred.", timeout=3.0)
                        time.sleep(2)
                    except:
                        pass
                time.sleep(1)  # Brief pause before continuing
                
    except Exception as e:
        print(f"\n💥 Critical error in main application: {e}")
    finally:
        # Cleanup
        print("\n🧹 Cleaning up resources...")
        if tts:
            try:
                tts.cleanup()
                print("✓ TTS resources cleaned up")
            except:
                print("⚠ TTS cleanup failed")
        
        # Always shutdown Ollama service
        shutdown_ollama_service(ollama_manager)
        
        print("✅ AXIom shutdown complete")

if __name__ == "__main__":
    main()




