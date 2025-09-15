# src/main.py
from CmdCraft.ollama_manager import OllamaManager

def main():
    ollama = OllamaManager()

    # try starting server
    if ollama.start_server() != 0:
        print("⚠️ Could not start Ollama server. Exiting...")
        return

    print("✅ Ollama Manager REPL started. Type 'exit' to quit.")
    print("Commands: 'list' = list models, 'restart' = restart server")

    while True:
        try:
            text = input("\n> ")

            if text.lower() in {"exit", "quit"}:
                ollama.stop_server()
                print("👋 Exiting REPL...")
                break

            elif text.lower() == "restart":
                result = ollama.restart_server()
                print("🔄 Restart:", "OK" if result == 0 else "Failed")

            elif text.lower() == "list":
                models = ollama.list_models()
                print("📦 Available models:", models)

            else:
                response = ollama.chat(text)
                if response and 'message' in response and 'content' in response['message']:
                    print("🤖:", response['message']['content'])
                else:
                    print("🤖:", response)

        except KeyboardInterrupt:
            ollama.stop_server()
            print("\n👋 Exiting REPL...")
            break

if __name__ == "__main__":
    main()