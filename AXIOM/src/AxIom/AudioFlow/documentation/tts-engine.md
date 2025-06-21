# The TTS-Engine

Here the TTS(text-to-speech) is handled using ElevenLabs\
This will have to change at some point to do the TTS locally for real-time communication 

## List Speakers
 This returns a list of All voices that can be used to generate TTS

## Generate Speech

Params: `speader_id: str`, `text: str`
Returns: `np.ndarray`
Here the TTS Output is generated then saved to a wav file 
This will be used to play the audio instead of calling their `play()`

