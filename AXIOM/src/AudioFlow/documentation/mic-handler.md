# The Mic-Handler

Here user input(audio) is transcribed into text to be sent to CmdCraft/Command-Handler. \
Using pythons `speech recognition` and openai `whisper` we can get a pretty accurate \
transcription really quickly 

## set_mic_input

Inside this function the mic input is captured then transcribed \
Saved the result to class variable 

Adjust for ambient noise before recording 

## get_mic_input 

This function just returns the transcribed text