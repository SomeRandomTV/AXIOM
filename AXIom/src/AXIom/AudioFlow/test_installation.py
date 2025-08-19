#!/usr/bin/env python3
"""
Installation Test Script
Verifies that all enhanced TTS dependencies are properly installed.
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        if package_name:
            module = importlib.import_module(module_name, package_name)
        else:
            module = importlib.import_module(module_name)
        print(f"✓ {module_name} - Available")
        return True
    except ImportError as e:
        print(f"✗ {module_name} - Not available: {e}")
        return False

def test_tts_handler():
    """Test the enhanced TTS handler."""
    try:
        from tts_handler import TTSHandler, COQUI_AVAILABLE, PYAUDIO_AVAILABLE
        
        print(f"\nTTS Handler Status:")
        print(f"  Coqui TTS: {'Available' if COQUI_AVAILABLE else 'Not Available'}")
        print(f"  PyAudio: {'Available' if PYAUDIO_AVAILABLE else 'Not Available'}")
        
        # Try to initialize
        tts = TTSHandler(use_local=False, streaming=False)  # Use cloud TTS for testing
        print("✓ TTSHandler - Initialized successfully")
        
        # Test basic functionality
        tts.speak("Installation test successful.")
        print("✓ TTSHandler - Basic speech test passed")
        
        tts.cleanup()
        return True
        
    except Exception as e:
        print(f"✗ TTSHandler - Failed: {e}")
        return False

def main():
    """Run all installation tests."""
    print("Enhanced TTS Installation Test")
    print("=" * 40)
    
    # Test core dependencies
    print("\nCore Dependencies:")
    core_deps = [
        "gtts",
        "numpy",
        "torch",
        "torchaudio"
    ]
    
    core_available = all(test_import(dep) for dep in core_deps)
    
    # Test enhanced dependencies
    print("\nEnhanced Dependencies:")
    enhanced_deps = [
        "TTS",
        "pyaudio"
    ]
    
    enhanced_available = all(test_import(dep) for dep in enhanced_deps)
    
    # Test TTS handler
    print("\nTTS Handler Test:")
    handler_working = test_tts_handler()
    
    # Summary
    print("\n" + "=" * 40)
    print("Installation Summary:")
    print(f"  Core Dependencies: {'✓ All Available' if core_available else '✗ Some Missing'}")
    print(f"  Enhanced Dependencies: {'✓ All Available' if enhanced_available else '✗ Some Missing'}")
    print(f"  TTS Handler: {'✓ Working' if handler_working else '✗ Not Working'}")
    
    if core_available and enhanced_available and handler_working:
        print("\n🎉 All tests passed! Enhanced TTS is ready to use.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please check the installation.")
        
        if not enhanced_available:
            print("\nTo install enhanced dependencies:")
            print("  pip install TTS pyaudio")
            print("  # On macOS: brew install portaudio")
            print("  # On Ubuntu: sudo apt-get install portaudio19-dev")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 