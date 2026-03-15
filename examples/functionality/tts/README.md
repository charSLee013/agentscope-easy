# TTS (Text-to-Speech) in AgentScope

This example demonstrates how to integrate DashScope Realtime TTS model with
`ReActAgent` to enable audio output. The agent can speak its responses in
real-time.

This example uses DashScope's Realtime TTS model. You can also switch to other
TTS models supported by AgentScope, such as OpenAI or Gemini.

AgentScope keeps local audio playback disabled by default. The example enables
`agentscope._config.audio_playback_enabled` explicitly so you can hear the
generated speech when running it in a local terminal session.

To run the example, execute:

```bash
python main.py
```
