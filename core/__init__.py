"""
ARIA OS — core orchestration engines.

These modules turn ARIA from a page-based app into a hands-free, voice-first
operating environment. They are Qt-aware where they must coordinate the UI,
but contain no screen code:

    intent_router          voice line  ->  navigation / command / talk
    auto_listening_engine  continuous hands-free microphone loop
    conversation           STT -> intent -> AI -> TTS orchestrator

The UI subscribes to ConversationEngine signals; it never calls STT, the AI
providers, or TTS directly.
"""
