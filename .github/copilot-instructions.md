# AI Coding Agent Instructions for Open-AutoGLM

## Project Overview

**Open-AutoGLM** is an AI-powered Android phone automation framework that uses vision-language models to understand phone screens and execute tasks through ADB (Android Debug Bridge). The agent operates in a **perception-planning-action loop**: capture screenshot → analyze with vision-LLM → generate actions → execute → repeat.

**Key Technologies:**
- Vision-Language Model: AutoGLM-Phone-9B (supports Chinese & multilingual variants)
- API: OpenAI-compatible endpoint (local vLLM/sglang or remote)
- Device Control: ADB (Android Debug Bridge) via subprocess
- Languages: Python 3.10+, Chinese & English UI support

---

## Architecture & Component Boundaries

### Core Loop: `phone_agent/agent.py` → `PhoneAgent`
- **Orchestrates** the main agent loop: screenshot → model inference → action execution → repeat
- **Max steps**: 100 by default; avoid infinite loops by checking step count
- **Context management**: Maintains message history in `self._context` for multi-turn conversations
- **Callbacks**: Accepts `confirmation_callback` (sensitive actions) and `takeover_callback` (login/CAPTCHA)
- **Example**: `examples/basic_usage.py` shows initialization with `ModelConfig` + `AgentConfig`

### Model Integration: `phone_agent/model/client.py` → `ModelClient`
- **Handles** OpenAI-compatible API calls with streaming support
- **ExtractS** thinking and action from streamed content (uses `<think>...</think>` and `<answer>...</answer>` markers)
- **Performance metrics**: Records `time_to_first_token`, `time_to_thinking_end`, `total_time`
- **Key config**: `base_url`, `api_key`, `model_name`, `temperature=0.0` (deterministic), `max_tokens=3000`
- **Frequency penalty**: 0.2 (reduces repetition), **top_p**: 0.85 (nucleus sampling)

### Action Execution: `phone_agent/actions/handler.py` → `ActionHandler`
- **Executes** parsed actions: `Launch`, `Tap`, `Type`, `Swipe`, `Back`, `Home`, `Wait`, `Long Press`, `Double Tap`, `finish`, `Take_over`
- **Action format**: Dict with `_metadata` key indicating action type; coordinates in 0-999 range (normalized)
- **Confirmation flow**: Calls `confirmation_callback()` for sensitive ops (e.g., tapping payment buttons)
- **Takeover flow**: Requests human intervention for login/CAPTCHA via `takeover_callback()`
- **Auto text clearing**: Type action clears existing text automatically; no manual cleanup needed
- **Timing**: Uses `TIMING_CONFIG` from `phone_agent/config/timing.py` for delays between actions

### Device Control: `phone_agent/adb/` (device.py, input.py, screenshot.py, connection.py)
- **Device operations**: `tap()`, `swipe()`, `type_text()`, `launch_app()`, `back()`, `home()`, `get_current_app()`
- **Screenshots**: Uses PIL to capture device screen; detects sensitivity (PIN/login screens)
- **Multi-device support**: Optional `device_id` param for controlling specific devices
- **Keyboard handling**: Switches to ADB keyboard for typing; restores system keyboard after
- **ADB prefix**: Builds command arrays for `subprocess.run()`; no shell injection risks

### Configuration: `phone_agent/config/`
- **`apps.py`**: Map of 50+ app names (Chinese) to Android package names (e.g., `"微信"` → `"com.tencent.mm"`)
- **`prompts.py` / `prompts_zh.py` / `prompts_en.py`**: System prompts defining action grammar and rules
- **`i18n.py`**: UI messages in Chinese (`cn`) and English (`en`)
- **`timing.py`**: Configurable delays for tap, swipe, type operations

---

## Critical Developer Workflows

### Local Setup & Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables (or create .env file)
export PHONE_AGENT_BASE_URL="http://localhost:8000/v1"
export PHONE_AGENT_MODEL="autoglm-phone-9b"
export PHONE_AGENT_API_KEY="your-key"

# Connect Android device via ADB
adb devices  # Verify device is listed

# Run basic example
python examples/basic_usage.py

# Run CLI with interactive mode
python main.py --interactive
```

### Model Deployment (Local Inference)
```bash
# Using sglang (recommended for speed)
pip install sglang transformers>=5.0.0rc0
python -m sglang.launch_server --model-path zai-org/AutoGLM-Phone-9B --port 8000

# Using vLLM
pip install vllm transformers>=5.0.0rc0
python -m vllm.entrypoints.openai.api_server --model zai-org/AutoGLM-Phone-9B --port 8000
```

### Debugging Agent Behavior
- Set `verbose=True` in `AgentConfig` for step-by-step logs
- Set `auto_cleanup_screenshots=False` to preserve device screenshots for debugging (will skip cleanup in finally block)
- Check `agent._context` to inspect message history
- Use `agent.step()` for manual single-step execution instead of `agent.run()`
- Inspect screenshot images from `phone_agent/adb/screenshot.py` → `get_screenshot()` to see what the model sees
- Add print statements in `ActionHandler.execute()` to trace action parsing

### Testing Multi-Step Tasks
- Use `example_with_callbacks()` in `examples/basic_usage.py` as template
- Implement `confirmation_callback()` to auto-approve or reject sensitive actions
- Implement `takeover_callback()` to pause and resume for manual input (login, CAPTCHA)

---

## Key Patterns & Conventions

### Action Grammar (From `prompts.py`)
```
do(action="Launch", app="xxx")          # Start app by name
do(action="Tap", element=[x,y])         # Tap at coordinates
do(action="Tap", element=[x,y], message="...")  # Tap + confirmation
do(action="Type", text="xxx")           # Type text (auto-clears existing)
do(action="Swipe", start=[x1,y1], end=[x2,y2])  # Drag gesture
do(action="Back")                       # Android back button
do(action="Home")                       # Android home button
do(action="Wait", duration="x seconds") # Pause for page load
do(action="Take_over", message="xxx")   # Request human help
finish(message="xxx")                   # Task complete
```

### Multi-Turn Context Management
- **First step**: Screenshot + user task → model response → action
- **Subsequent steps**: Screenshot + action result → model response → next action
- **Context building**: `_context` list maintains full conversation for coherence across steps
- **Max steps protection**: Default 100 steps; exceeding returns "Max steps reached"

### Language & Localization
- **Lang parameter**: Set `lang="cn"` or `lang="en"` in `AgentConfig` and `ModelConfig`
- **System prompts**: Auto-selected from `prompts_zh.py` or `prompts_en.py` via `get_system_prompt(lang)`
- **UI messages**: Auto-selected via `get_messages(lang)` for user-facing output

### Coordinate System & Screen Assumptions
- **Normalized range**: 0-999 for both X and Y (device resolution is scaled to this range)
- **Origin**: Top-left corner (0, 0)
- **Coordinate conversion**: `ActionHandler._convert_relative_to_absolute()` scales normalized coords to actual device resolution
- **Device properties**: `screenshot.width` and `screenshot.height` contain actual pixel dimensions

### Timing & Delays
- **Auto-delays**: Built into action handlers via `TIMING_CONFIG` (e.g., `device.default_tap_delay`)
- **Custom delays**: Pass optional `delay` param to ADB functions (in seconds)
- **Wait action**: For explicit page load waits; max 3 consecutive waits before fallback (per prompt rules)

### Automatic Screenshot Cleanup
- **Auto-cleanup**: Enabled by default via `AgentConfig.auto_cleanup_screenshots = True`
- **Mechanism**: At the end of each `agent.run()`, device temporary files (`/sdcard/tmp.png`) are automatically deleted
- **Control**: Set `auto_cleanup_screenshots=False` to disable if debugging and need to preserve screenshots
- **Function**: `cleanup_device_screenshots(device_id)` in `phone_agent/adb/screenshot.py` handles device-side cleanup
- **Safety**: Cleanup is in `finally` block, guaranteed to execute even if task fails

---

## External Dependencies & Integration Points

### ADB (Android Debug Bridge)
- **System requirement**: ADB must be in PATH; checked by `main.py::check_system_requirements()`
- **Multi-device**: Pass `device_id` to PhoneAgent for specific device; default is first connected device
- **Commands used**: `shell dumpsys window` (get focus), `shell input tap/swipe/type` (control), `shell screencap` (capture)

### Vision-Language Model API
- **OpenAI-compatible**: Expects `/v1/chat/completions` endpoint with streaming support
- **Local models**: sglang or vLLM server expose compatible API
- **Remote models**: Zhipu GLM API (in China) or OpenAI API compatible services
- **Failure handling**: `ModelClient.request()` raises `ValueError` if response can't be parsed

### Model Input Format
- **System message**: Action grammar + rules + current date (from `get_system_prompt()`)
- **User messages**: Include base64-encoded screenshot image + app name + task description
- **Vision format**: PIL Image → base64 → OpenAI message format with `image_url` and `data:image/jpeg;base64,...`

### External Files Not Auto-Managed
- **`.env` file**: Created manually; loads environment variables if present (see [main.py](../main.py) lines 13-21)
- **Privacy policy**: `resources/privacy_policy.txt` — legal terms for end users
- **App packages**: [phone_agent/config/apps.py](../phone_agent/config/apps.py) — maintained list of supported Chinese apps

---

## Common Pitfalls & Solutions

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| "Max steps reached" | Model looping or unclear task | Simplify task, increase `max_steps`, check screenshot quality |
| Screenshot is black/blank | Device locked or sensitive screen | Implement `takeover_callback` to handle login |
| Type action fails | Text not cleared before input | Automatic clearing is built-in; check ADB keyboard is active |
| Tap misses target | Coordinate scaling off | Verify `ActionHandler._convert_relative_to_absolute()` receives correct device dimensions |
| Model offline errors | API endpoint unreachable | Check `base_url` is correct; verify local model server is running |
| Multi-device conflicts | Wrong device executing | Always pass explicit `device_id` in `AgentConfig` for multi-device |
| Sensitivity detection false positive | Screenshot classified as login/PIN | Debug `screenshot.is_sensitive` in `Screenshot.detect_sensitivity()` |

---

## Repository Structure Reference

```
phone_agent/
├── agent.py              # PhoneAgent main class & orchestration loop
├── actions/handler.py    # Action parsing & execution
├── adb/                  # Device control (device.py, screenshot.py, input.py, connection.py)
├── model/client.py       # ModelClient for LLM inference
└── config/               # Prompts, app packages, i18n, timing

examples/
├── basic_usage.py        # Template for PhoneAgent initialization
├── demo_thinking.py      # Extended example with callbacks
└── douyin_coins_example.py  # Production example: Douyin coin earning automation

docs/                    # 📌 Auto-generated documentation (NOT tracked by Git)
├── DOUYIN_COINS_*.md    # Douyin automation guides
├── CLEANUP_*.md         # Cleanup feature documentation
└── *.md                 # All auto-generated docs go here

main.py                  # CLI entry point with ADB setup checks
.gitignore               # Git ignore rules (includes docs/ directory)
```

---

## Documentation Organization Rules

### 📋 File Organization Policy

**1. Auto-Generated Documentation**:
- **Location**: Always in `docs/` directory
- **Git Status**: `docs/` is in `.gitignore` (NOT tracked)
- **Purpose**: Guides, references, implementation notes, changelogs
- **Examples**:
  - `docs/DOUYIN_COINS_GUIDE.md` (implementation guide)
  - `docs/DOUYIN_COINS_QUICK_REFERENCE.md` (quick lookup)
  - `docs/CLEANUP_IMPLEMENTATION_GUIDE.md` (feature docs)

**2. Core Project Files** (Tracked in Git):
- **Location**: Root or subdirectories (not in `docs/`)
- **Examples**:
  - `examples/douyin_coins_example.py` (runnable code)
  - `phone_agent/config/prompts_douyin_coins.py` (core implementation)
  - `phone_agent/config/douyin_coins_config.py` (task configuration)
  - `START_HERE_DOUYIN_COINS.md` (main entry point, tracked)

**3. Temporary Files** (Auto-deleted):
- **Types**: Test outputs, debug scripts, temporary markdown
- **Pattern**: `*_test.py`, `test_*.py`, `*_debug.*`, `temp_*.ps1`
- **Git**: In `.gitignore`, never committed

**4. Environment & Secrets** (Never tracked):
- `.env` (local configuration)
- `.env.local`, `.env.example` (templates)
- `litellm_config.yaml` (local config)

### 🔄 Workflow for Generating Documentation

**When Creating New Documentation**:

```python
# Step 1: Create the markdown file in docs/
docs_file = "docs/MY_NEW_FEATURE_GUIDE.md"
# Write content...

# Step 2: No manual .gitignore change needed!
# docs/ is already ignored, file will NOT be tracked

# Step 3: Reference from project code if needed
# Example: Add link in examples/my_feature.py docstring
```

**Automated Process**:
1. All new markdown files → `docs/` directory
2. All `docs/` files → automatically ignored by Git
3. No manual gitignore updates needed for documentation

### ✅ .gitignore Configuration

```ignore
# Local documentation (auto-generated, not tracked)
docs/
docs_local/
*.md.local

# Temporary test files
*_test.py
test_*.py
*_debug.*

# Temporary scripts
*.ps1
temp_*.ps1
```

**Current Status**:
- ✅ `docs/` directory ignored (all auto-generated docs)
- ✅ Temporary script patterns ignored (`*.ps1`, `temp_*.ps1`)
- ✅ Test file patterns ignored (`*_test.py`, `test_*.py`)
- ✅ Debug files ignored (`*_debug.*`)

### 📌 For AI Agents: Documentation Guidelines

1. **Always** put generated documentation in `docs/` directory
2. **Never** create markdown files in root directory (except `START_HERE*.md` for main entry points)
3. **Always** use descriptive names: `FEATURE_NAME_TYPE.md` (e.g., `DOUYIN_COINS_GUIDE.md`)
4. **Documentation types**:
   - `*_GUIDE.md` - Detailed implementation/usage guide
   - `*_QUICK_REFERENCE.md` - Quick lookup tables
   - `*_INDEX.md` - Navigation/organization
   - `*_CHANGELOG.md` - Version history
5. **Do NOT create** temporary documentation in root (auto-cleanup enabled)
6. **Verify** `.gitignore` before committing to avoid tracking documentation
7. **Reference** docs from code comments: `See docs/FEATURE_NAME_GUIDE.md for details`

---

## For AI Agents: How to Contribute

1. **Understand the loop**: Screenshot → Model → Action → Screenshot (repeat)
2. **Coordinate system**: Always think in 0-999 normalized range; let `ActionHandler` handle device scaling
3. **Test locally**: Run `python examples/basic_usage.py` with a real device connected via ADB
4. **Language awareness**: Check `lang` param in both `ModelConfig` and `AgentConfig`; Chinese prompts != English prompts
5. **Callbacks matter**: Implement `confirmation_callback` for sensitive ops; `takeover_callback` for manual intervention
6. **Max steps**: Always check `agent._step_count < agent_config.max_steps` to avoid infinite loops
7. **App packages**: Use `phone_agent/config/apps.py` to map app names to Android packages; don't hardcode package names
8. **Performance**: Monitor `ModelResponse` timing metrics for latency; use `temperature=0.0` for deterministic behavior
