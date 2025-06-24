# main.py
"""
Main function
All external files will be called here
"""
import os
from CmdCraft import cmd_handler as ch
from CmdCraft import prompt_handler as ph
from AudioFlow import tts_engine as te
from AudioFlow import mic_input as se
from dotenv import load_dotenv
import time

load_dotenv()
LLM_URL = os.getenv("LLM_URL")


def main():
    print("Initializing components...")
    handler = ch.CommandHandler()
    p_handler = ph.PromptHandler(url=LLM_URL)
    tts = te.TTSEngine()
    mic = se.MicInput()
    print("Components initialized.")

    print("Starting the AXIom...")
    while True:
        mic.set_mic_input()
        inp = mic.get_text()
        print(inp)
        system_message = "Your nane is AURA, (spelt ARA) the adaptive real time assistant. You must. keep your responses short(1-2 sentences max, no more that 25 words)."
        try:
            handler.set_command(inp)
            handler.parse_command()
            print("→ Function flag:", handler.function_flag)
            if handler.function_flag == 1:
                print("→ Function call:", handler.function_call)
                print("→ Target:", handler.target)
                tts.speak("Calling function...")

            else:
                print("Going to llm...")
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": inp}
                ]
                result = p_handler.send_prompt(messages)
                print(f"ARA: {result["message"]["content"]}")
                response = result["message"]["content"]
                tts.speak(response)

            command = handler.get_commands()
            print(f"\nCommand: {command}")
            time.sleep(0.5)
        except ValueError as err:
            print("→ Error:", err)


if __name__ == "__main__":
    main()




