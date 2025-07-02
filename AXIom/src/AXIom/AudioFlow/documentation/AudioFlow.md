# AudioFlow
Something

This library contains all functions that handle: 
- Microphone input 
- TTS 

Here is AudioFlow tied into the AXIOM System

```mermaid
flowchart LR
    %% Group your modules
    subgraph CmdCraft
      CH[CommandHandler]
      FH[FunctionHandler]
      PM[PromptHandler]
      
    end

    subgraph AudioFlow
      MI[MicInput]
      TC[TTS]
    
    end

    %% Relationships
    MI --> CH
    CH --> FH
    CH --> PM
    PM --> LLM
    LLM --> TC
    FH --> Function
    Function --> TC
```

## The inner workings 

This was a bitch to do honestly man, I mean if you want to cut latency down? FUUUUCK 

Anyways there is the basic runndown of it: 

```mermaid
flowchart TD
    A[main] --> B[Create TTSHandler instance]
    B --> C[tts.speak]

    C --> D{Is text empty?}
    D -- Yes --> E[Raise ValueError]
    D -- No --> F[Print ARA: <text>]

    F --> G[Check for ffplay]
    G -- Found --> H[_speak_ffplay]
    H --> H1[Synthesize to bytes]
    H1 --> H2[Launch ffplay subprocess with stdin]
    H2 --> H3[proc.communicate]
    H3 --> Z[Done]

    G -- Not found --> I[Check for afplay]
    I -- Found macOS --> J[_speak_afplay]
    J --> J1[Synthesize to bytes]
    J1 --> J2[Launch afplay subprocess INVALID: stdin]
    J2 --> J3[Fails --> fallback]
    J3 --> K[_fallback_speak]
    K --> K1[synthesize_to_file]
    K1 --> K2[play_audio]
    K2 --> K3[Remove temp file]
    K3 --> Z

    I -- Not found --> K

    C -->|Any Exception| K

    Z[Log 'TTS done.']

```