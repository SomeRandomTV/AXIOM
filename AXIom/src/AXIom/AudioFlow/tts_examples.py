#!/usr/bin/env python3
"""
Enhanced TTS Examples
Demonstrates the new Coqui TTS capabilities for local synthesis and real-time streaming.
"""

import time
import threading
from tts_handler import TTSHandler


def demo_basic_local_tts():
    """Demonstrate basic local TTS functionality."""
    print("\n=== Basic Local TTS Demo ===")
    
    tts = TTSHandler(use_local=True, streaming=False)
    
    # Test local synthesis
    print("Testing local TTS synthesis...")
    tts.speak("Hello! This is ARA using local Coqui TTS for high-quality speech synthesis.")
    
    # Test file output
    print("Testing local TTS file output...")
    file_path = tts.synthesize_to_file("This audio was generated locally using Coqui TTS.")
    print(f"Audio saved to: {file_path}")
    
    # Cleanup
    tts.cleanup()


def demo_streaming_tts():
    """Demonstrate real-time streaming TTS functionality."""
    print("\n=== Streaming TTS Demo ===")
    
    tts = TTSHandler(use_local=True, streaming=True)
    
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
    time.sleep(2)
    
    # Test streaming with sentence-based chunks
    print("Testing streaming TTS with sentence-based chunks...")
    tts.stream_speak(
        "Sentence one. Sentence two. Sentence three. "
        "Each sentence is processed independently for optimal streaming performance.",
        chunk_size=100
    )
    
    # Wait for streaming to complete
    time.sleep(2)
    
    # Cleanup
    tts.cleanup()


def demo_performance_comparison():
    """Compare performance between local and cloud TTS."""
    print("\n=== Performance Comparison Demo ===")
    
    test_text = "This is a performance test comparing local and cloud TTS synthesis capabilities."
    
    # Test local TTS
    print("Testing local TTS performance...")
    local_tts = TTSHandler(use_local=True, streaming=False)
    start_time = time.time()
    local_tts.speak(test_text)
    local_time = time.time() - start_time
    
    # Test cloud TTS
    print("Testing cloud TTS performance...")
    cloud_tts = TTSHandler(use_local=False, streaming=False)
    start_time = time.time()
    cloud_tts.speak(test_text)
    cloud_time = time.time() - start_time
    
    print(f"\nPerformance Results:")
    print(f"Local TTS: {local_time:.2f} seconds")
    print(f"Cloud TTS: {cloud_time:.2f} seconds")
    print(f"Speed improvement: {((cloud_time - local_time) / cloud_time * 100):.1f}%")
    
    # Show detailed stats
    local_stats = local_tts.get_performance_stats()
    cloud_stats = cloud_tts.get_performance_stats()
    
    print(f"\nLocal TTS Stats: {local_stats}")
    print(f"Cloud TTS Stats: {cloud_stats}")
    
    # Cleanup
    local_tts.cleanup()
    cloud_tts.cleanup()


def demo_voice_models():
    """Demonstrate different voice models if available."""
    print("\n=== Voice Models Demo ===")
    
    tts = TTSHandler(use_local=True, streaming=False)
    
    if tts.coqui_tts and tts.available_models:
        print(f"Available voice models: {len(tts.available_models)}")
        
        # Show first few models
        for i, model in enumerate(tts.available_models[:5]):
            print(f"  {i+1}. {model}")
        
        # Test with different model if available
        if len(tts.available_models) > 1:
            print("\nTesting with first available model...")
            tts.speak("Testing voice model variety with Coqui TTS.")
    else:
        print("No Coqui TTS models available.")
    
    tts.cleanup()


def demo_hybrid_approach():
    """Demonstrate hybrid approach with fallback capabilities."""
    print("\n=== Hybrid Approach Demo ===")
    
    tts = TTSHandler(use_local=True, streaming=True)
    
    # Test local first, then fallback to cloud if needed
    print("Testing hybrid approach with local priority...")
    
    try:
        tts.speak("This should use local TTS if available.")
    except Exception as e:
        print(f"Local TTS failed: {e}")
        print("Falling back to cloud TTS...")
        tts.speak("This is using cloud TTS as fallback.")
    
    # Test streaming with hybrid approach
    print("Testing streaming with hybrid approach...")
    try:
        tts.stream_speak("Testing streaming with local TTS priority and cloud fallback.")
    except Exception as e:
        print(f"Streaming failed: {e}")
    
    # Cleanup
    tts.cleanup()


def demo_error_handling():
    """Demonstrate error handling and fallback mechanisms."""
    print("\n=== Error Handling Demo ===")
    
    # Test with invalid text
    tts = TTSHandler(use_local=True, streaming=False)
    
    try:
        tts.speak("")  # This should raise an error
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    try:
        tts.speak("Testing error handling with valid text.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    tts.cleanup()


def main():
    """Run all TTS demos."""
    print("Enhanced TTS Handler Demo Suite")
    print("=" * 50)
    
    # Check system capabilities
    from tts_handler import COQUI_AVAILABLE, PYAUDIO_AVAILABLE
    
    print(f"System Capabilities:")
    print(f"  Coqui TTS: {'Available' if COQUI_AVAILABLE else 'Not Available'}")
    print(f"  PyAudio: {'Available' if PYAUDIO_AVAILABLE else 'Not Available'}")
    print()
    
    if not COQUI_AVAILABLE:
        print("Warning: Coqui TTS not available. Install with: pip install TTS")
        print("Some demos may not work properly.\n")
    
    if not PYAUDIO_AVAILABLE:
        print("Warning: PyAudio not available. Install with: pip install pyaudio")
        print("Direct audio playback may not work properly.\n")
    
    # Run demos
    try:
        demo_basic_local_tts()
        time.sleep(1)
        
        demo_streaming_tts()
        time.sleep(1)
        
        demo_performance_comparison()
        time.sleep(1)
        
        demo_voice_models()
        time.sleep(1)
        
        demo_hybrid_approach()
        time.sleep(1)
        
        demo_error_handling()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
    
    print("\nDemo suite completed!")


if __name__ == "__main__":
    main() 