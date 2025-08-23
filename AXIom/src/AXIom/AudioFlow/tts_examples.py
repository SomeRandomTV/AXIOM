#!/usr/bin/env python3
"""
Enhanced TTS Examples (Python 3.12 Compatible)
Demonstrates the enhanced TTS capabilities with cloud synthesis and real-time streaming.
"""

import time
import threading
from tts_handler import TTSHandler


def demo_basic_tts():
    """Demonstrate basic TTS functionality."""
    print("\n=== Basic TTS Demo ===")
    
    tts = TTSHandler(streaming=False, timeout=15.0)
    
    # Test basic synthesis
    print("Testing TTS synthesis...")
    tts.speak("Hello! This is ARA using enhanced cloud TTS with timeout protection.")
    
    # Test file output
    print("Testing TTS file output...")
    file_path = tts.synthesize_to_file("This audio was generated using enhanced gTTS.")
    print(f"Audio saved to: {file_path}")
    
    # Cleanup
    tts.cleanup()


def demo_streaming_tts():
    """Demonstrate real-time streaming TTS functionality."""
    print("\n=== Streaming TTS Demo ===")
    
    tts = TTSHandler(streaming=True, timeout=20.0)
    
    # Test streaming with different chunk sizes
    print("Testing streaming TTS with 30-character chunks...")
    tts.stream_speak(
        "This is a demonstration of real-time streaming text-to-speech. "
        "Each chunk of text is processed and synthesized as it becomes available, "
        "providing a more responsive and natural speaking experience. "
        "The system can handle long texts efficiently by breaking them into manageable pieces.",
        chunk_size=30
    )
    
    # Wait for streaming to complete
    time.sleep(3)
    
    # Test streaming with sentence-based chunks
    print("Testing streaming TTS with sentence-based chunks...")
    tts.stream_speak(
        "Sentence one. Sentence two. Sentence three. "
        "Each sentence is processed independently for optimal streaming performance.",
        chunk_size=100
    )
    
    # Wait for streaming to complete
    time.sleep(3)
    
    # Cleanup
    tts.cleanup()


def demo_audio_methods():
    """Demonstrate different audio playback methods."""
    print("\n=== Audio Methods Demo ===")
    
    tts = TTSHandler(streaming=False, timeout=10.0)
    
    # Show available audio methods
    audio_info = tts.get_audio_info()
    print(f"Available audio methods: {tts.audio_methods}")
    print(f"Audio info: {audio_info}")
    
    # Test each audio method
    for method in tts.audio_methods:
        print(f"\nTesting {method} audio method...")
        try:
            if method == 'pyaudio':
                # Test PyAudio directly
                if tts.test_audio():
                    print(f"✓ {method} test passed")
                else:
                    print(f"✗ {method} test failed")
            else:
                # Test with TTS
                tts.speak(f"Testing {method} audio playback method.", timeout=5.0)
                print(f"✓ {method} test completed")
        except Exception as e:
            print(f"✗ {method} test failed: {e}")
    
    tts.cleanup()


def demo_timeout_protection():
    """Demonstrate timeout protection and fallback mechanisms."""
    print("\n=== Timeout Protection Demo ===")
    
    tts = TTSHandler(streaming=False, timeout=5.0)  # Short timeout
    
    # Test with short timeout
    print("Testing with 5-second timeout...")
    try:
        tts.speak("This should complete within the timeout period.", timeout=5.0)
        print("✓ Short timeout test passed")
    except Exception as e:
        print(f"⚠ Short timeout test: {e}")
    
    # Test fallback mechanisms
    print("\nTesting fallback mechanisms...")
    try:
        tts.speak("Testing fallback audio playback methods.")
        print("✓ Fallback test completed")
    except Exception as e:
        print(f"✗ Fallback test failed: {e}")
    
    tts.cleanup()


def demo_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    print("\n=== Performance Monitoring Demo ===")
    
    tts = TTSHandler(streaming=False, timeout=15.0)
    
    # Perform several TTS operations
    test_texts = [
        "First test message for performance monitoring.",
        "Second test message to measure synthesis time.",
        "Third test message to calculate average performance."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"Processing message {i}...")
        tts.speak(text, timeout=10.0)
        time.sleep(1)
    
    # Show performance stats
    stats = tts.get_performance_stats()
    print(f"\nPerformance Statistics:")
    print(f"  Total syntheses: {stats['total_syntheses']}")
    print(f"  Average synthesis time: {stats['avg_synthesis_time']:.2f}s")
    print(f"  Available audio methods: {stats['available_audio_methods']}")
    print(f"  PyAudio available: {stats['pyaudio_available']}")
    
    tts.cleanup()


def demo_error_handling():
    """Demonstrate error handling and fallback mechanisms."""
    print("\n=== Error Handling Demo ===")
    
    tts = TTSHandler(streaming=False, timeout=10.0)
    
    # Test with invalid text
    try:
        tts.speak("")  # This should raise an error
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")
    
    # Test with very long text (might trigger timeout)
    long_text = "This is a very long text that might take a while to process. " * 10
    try:
        tts.speak(long_text, timeout=15.0)
        print("✓ Long text test completed")
    except Exception as e:
        print(f"⚠ Long text test: {e}")
    
    # Test with valid text
    try:
        tts.speak("Testing error handling with valid text.")
        print("✓ Valid text test completed")
    except Exception as e:
        print(f"✗ Valid text test failed: {e}")
    
    tts.cleanup()


def demo_hybrid_approach():
    """Demonstrate hybrid approach with multiple audio methods."""
    print("\n=== Hybrid Audio Methods Demo ===")
    
    tts = TTSHandler(streaming=True, timeout=20.0)
    
    # Test streaming with hybrid audio methods
    print("Testing streaming with hybrid audio approach...")
    try:
        tts.stream_speak(
            "This test demonstrates how the system automatically tries different audio methods "
            "in priority order: PyAudio first, then ffplay, then afplay, and finally file-based playback. "
            "Each method is tried until one succeeds, ensuring reliable audio playback.",
            chunk_size=80
        )
        print("✓ Hybrid streaming test completed")
    except Exception as e:
        print(f"✗ Hybrid streaming test failed: {e}")
    
    # Wait for completion
    time.sleep(3)
    
    tts.cleanup()


def main():
    """Run all TTS demos."""
    print("Enhanced TTS Handler Demo Suite (Python 3.12 Compatible)")
    print("=" * 60)
    
    # Check system capabilities
    from tts_handler import PYAUDIO_AVAILABLE
    
    print(f"System Capabilities:")
    print(f"  PyAudio: {'Available' if PYAUDIO_AVAILABLE else 'Not Available'}")
    print()
    
    if not PYAUDIO_AVAILABLE:
        print("Note: PyAudio not available. Install with: pip install pyaudio")
        print("On macOS: brew install portaudio\n")
    
    # Run demos
    try:
        demo_basic_tts()
        time.sleep(1)
        
        demo_audio_methods()
        time.sleep(1)
        
        demo_timeout_protection()
        time.sleep(1)
        
        demo_performance_monitoring()
        time.sleep(1)
        
        demo_error_handling()
        time.sleep(1)
        
        demo_streaming_tts()
        time.sleep(1)
        
        demo_hybrid_approach()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
    
    print("\nDemo suite completed!")


if __name__ == "__main__":
    main() 