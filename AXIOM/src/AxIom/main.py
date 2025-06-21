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

load_dotenv()
LLM_URL = os.getenv("LLM_URL")


def main():
    handler = ch.CommandHandler()
    p_handler = ph.PromptHandler(url=LLM_URL)
    tts = te.TTS_Engine()
    mic = se.MicInput()

    while True:
        mic.set_mic_input()
        inp = mic.get_text()
        print(inp)
        system_message = "Your name is AURA, (spelt ARA) the adaptive real time assistant. You must. keep your responses short(1-2 sentences max, no more that 25 words)."
        try:
            handler.set_command(inp)
            handler.parse_command()
            print("→ Function flag:", handler.function_flag)
            if handler.function_flag == 1:
                print("→ Function call:", handler.function_call)
                print("→ Target:", handler.target)
                tts.speak(f"Calling {handler.function_call} with parameters {handler.target}")
            else:
                print("Going to llm...")
                messages = [{"role": "user", "context": system_message, "content": inp}]
                result = p_handler.send_prompt(messages)
                print(f"Result: {result["message"]["content"]}")
                tts.speak(result["message"]["content"])

            command = handler.get_commands()
            print(f"\nCommand: {command}")
        except ValueError as err:
            print("→ Error:", err)


if __name__ == "__main__":
    main()




