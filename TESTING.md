# ARIA OS — Testing Checklist

Run through this list before a graduation demo. Anything that fails opens `aria_os.log` first — it records every step of the voice loop with `[ARIA-OS]` lines.

## 1. Boot
- [ ] `run_aria.bat` opens. Splash plays, then ARIA OS home appears.
- [ ] In kiosk mode the window is frameless + fullscreen. Esc exits cleanly.
- [ ] No new lines in `crash.log` after a clean Esc-exit.

## 2. Profiles
- [ ] First-run wizard creates a parent profile (name, PIN, language).
- [ ] First-run wizard creates a child profile (name, age, language, comm level).
- [ ] Quit, relaunch — both profiles survive.
- [ ] WelcomeBackScreen shows existing children and lets you switch.
- [ ] Parent Dashboard PIN entry uses the **on-screen numpad** (password field, max length 4).

## 3. Voice loop (verbal child)
- [ ] Greeting plays in the child's language (`ar`, `en`, or `de`).
- [ ] After the greeting the status shows **"I'm listening… 🎙️"** and the mic level bar moves when you speak.
- [ ] Say "I am hungry" (or Arabic equivalent) — ARIA replies kindly.
- [ ] Say "What should I do?" — ARIA remembers the previous turn (chat history).
- [ ] Say "ARIA, open games" — Games screen opens.
- [ ] Inside Games, say "go back" — returns to the shell.
- [ ] Say "ARIA, open the calm zone" — Calm Zone opens.
- [ ] Tap-to-talk button is a reliable fallback whenever auto-listen is unsure.

## 4. Camera & presence
- [ ] Top-bar badge shows **"👁 Looking for you…"** when no face is in frame.
- [ ] When the child appears, badge flips to **"👀 I see you"** within ~1 s.
- [ ] When the child leaves, badge returns to "Looking for you" after ~4 s of absence.
- [ ] When `ambient_emotion_enabled` is on: a held sad face for ~6 s pops the comfort card; tapping **Calm Zone** opens it.

## 5. Non-verbal scan flow (set a child's `communication_level` to `non_verbal`)
- [ ] Home shell shows the **Picture Talk** tile first.
- [ ] After the greeting ARIA reads each tile aloud (~5 s pause each).
- [ ] A head **nod** picks the option ARIA is currently saying.
- [ ] A head **shake** advances to the next option.
- [ ] Picking "Picture Talk" opens the Communication Board.

## 6. Provider Control Center (⚙ Setup)
- [ ] All 12 toggles show the expected status chip (`key set` / `needs key` / `ready`).
- [ ] Toggling Groq off and asking ARIA a question routes to the next enabled AI provider.
- [ ] Pasting a new key into the field and tapping **Save** is reflected immediately (status chip flips to green).
- [ ] Toggling **ElevenLabs** off makes the next reply use edge-tts. Toggling it back on (with a key set) returns the premium voice.
- [ ] Toggling **Whisper** off makes Arabic transcription fall back to Google STT.
- [ ] **✕ Exit** button quits ARIA OS with a confirm dialog.

## 7. Calm Zone (camera-distress demo)
- [ ] With `ambient_emotion_enabled: true` and a sad expression held ~6 s, the home shell shows the soft comfort card and ARIA speaks the offer.
- [ ] Tapping **🌿 Calm Zone** opens the breathing exercise.
- [ ] Tapping **😊 I'm okay** dismisses the card with no nav.
- [ ] Card auto-dismisses after 22 s if untouched.

## 8. Settings & onboarding device tests
- [ ] In Settings, the microphone dropdown lists every input device.
- [ ] In Settings, the camera dropdown lists every input camera.
- [ ] Selecting a different mic / camera persists across restarts.

## 9. Graceful failure
- [ ] Disconnect the mic — `[ARIA-OS] auto-listen: ERROR …` appears in `aria_os.log`, and the status shows the localised "tap 🎙 to talk" warning.
- [ ] Disconnect the camera — presence badge stays on "Looking for you", listening still works.
- [ ] Turn off Wi-Fi — Groq/Cerebras fail, but Whisper still transcribes; the AI returns the localised offline reply ("I'm here with you — let's do something calm together").
- [ ] Pull the network mid-TTS — the **TTS watchdog** resumes the listening loop within ~22 s.

## 10. Clean exit
- [ ] Esc, **✕ Exit** button, or closing the window all end the process with **no new lines** in `crash.log`.
- [ ] `aria_os.log` has a "===== ARIA OS session …" header for each run.

## Demo flow (the headline)
1. Launch -> ARIA greets by name.
2. **"I'm hungry"** -> ARIA acknowledges and remembers.
3. **"What should I do?"** -> ARIA recalls the hunger and suggests asking a parent / checking the snack routine.
4. Camera sees sustained sadness -> comfort card -> **Calm Zone** opens.
5. Open Parent Dashboard (PIN via on-screen numpad) -> the chat history, emotion log and memory summary all show this session.

Every step is in `aria_os.log` — the demo narrates itself.
