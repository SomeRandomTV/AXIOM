# main.py
"""
Main function
All external files will be called here
"""
import os
from CmdCraft import cmd_handler as ch
from CmdCraft import prompt_handler as ph
from AudioFlow import tts_handler as te
from AudioFlow import mic_handler as se
from dotenv import load_dotenv
import time

load_dotenv()

SYSTEM_PROMPT = "Your name is ARA(Adaptive real-time assistant, you are to keep your answers 1-3 sentences"

def main():
    print("Initializing components...")
    handler = ch.CommandHandler()
    p_handler = ph.PromptHandler(model="Llama3", system_prompt=SYSTEM_PROMPT)
    tts = te.TTSHandler()
    mic = se.MicHandler()
    print("Components initialized.")

    print("Starting the AXIom...")
    while True:
        mic.set_mic_input()
        inp = mic.get_text()
        print(inp)
        try:
            handler.set_command(inp)
            handler.parse_command()
            print("→ Function flag:", handler.function_flag)
            if handler.function_flag == 1:
                print("→ Function call:", handler.function_call_name)
                print("→ Target:", handler.function_params)
                tts.speak("Calling function...")
                

            else:
                print("Going to llm...")

                result = p_handler.chat(inp)
                print(result)
                tts.speak(result)

            command = handler.get_function_calls()
            print(f"\nCommand: {command}")
            time.sleep(0.5)
        except ValueError as err:
            print("→ Error:", err)


if __name__ == "__main__":
    main()




