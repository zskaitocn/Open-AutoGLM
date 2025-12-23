"""Main PhoneAgent class for orchestrating phone automation."""

import json
import traceback
from dataclasses import dataclass
from typing import Any, Callable, TYPE_CHECKING

from phone_agent.actions import ActionHandler
from phone_agent.actions.handler import do, finish, parse_action
from phone_agent.adb import get_current_app, get_screenshot
from phone_agent.config import get_messages, get_system_prompt
from phone_agent.model import ModelClient, ModelConfig
from phone_agent.model.client import MessageBuilder

if TYPE_CHECKING:
    from phone_agent.adb.screenshot import Screenshot


@dataclass
class AgentConfig:
    """Configuration for the PhoneAgent."""

    max_steps: int = 100
    device_id: str | None = None
    lang: str = "cn"
    system_prompt: str | None = None
    verbose: bool = True
    auto_cleanup_screenshots: bool = True

    def __post_init__(self):
        if self.system_prompt is None:
            self.system_prompt = get_system_prompt(self.lang)


@dataclass
class StepResult:
    """Result of a single agent step."""

    success: bool
    finished: bool
    action: dict[str, Any] | None
    thinking: str
    message: str | None = None


class PhoneAgent:
    """
    AI-powered agent for automating Android phone interactions.

    The agent uses a vision-language model to understand screen content
    and decide on actions to complete user tasks.

    Args:
        model_config: Configuration for the AI model.
        agent_config: Configuration for the agent behavior.
        confirmation_callback: Optional callback for sensitive action confirmation.
        takeover_callback: Optional callback for takeover requests.

    Example:
        >>> from phone_agent import PhoneAgent
        >>> from phone_agent.model import ModelConfig
        >>>
        >>> model_config = ModelConfig(base_url="http://localhost:8000/v1")
        >>> agent = PhoneAgent(model_config)
        >>> agent.run("Open WeChat and send a message to John")
    """

    def __init__(
        self,
        model_config: ModelConfig | None = None,
        agent_config: AgentConfig | None = None,
        confirmation_callback: Callable[[str], bool] | None = None,
        takeover_callback: Callable[[str], None] | None = None,
    ):
        self.model_config = model_config or ModelConfig()
        self.agent_config = agent_config or AgentConfig()

        self.model_client = ModelClient(self.model_config)
        self.action_handler = ActionHandler(
            device_id=self.agent_config.device_id,
            confirmation_callback=confirmation_callback,
            takeover_callback=takeover_callback,
        )

        self._context: list[dict[str, Any]] = []
        self._step_count = 0

    def run(self, task: str) -> str:
        """
        Run the agent to complete a task.

        Args:
            task: Natural language description of the task.

        Returns:
            Final message from the agent.
        """
        try:
            # Tier 1: Startup protection - check for and clean stale files
            if self.agent_config.auto_cleanup_screenshots:
                self._cleanup_stale_files()
            
            self._context = []
            self._step_count = 0

            # First step with user prompt
            result = self._execute_step(task, is_first=True)

            if result.finished:
                return result.message or "Task completed"

            # Continue until finished or max steps reached
            while self._step_count < self.agent_config.max_steps:
                result = self._execute_step(is_first=False)

                if result.finished:
                    return result.message or "Task completed"

            return "Max steps reached"
        finally:
            # Tier 3: Final cleanup - ensure files are deleted
            if self.agent_config.auto_cleanup_screenshots:
                self._cleanup_device_screenshots()

    def step(self, task: str | None = None) -> StepResult:
        """
        Execute a single step of the agent.

        Useful for manual control or debugging.

        Args:
            task: Task description (only needed for first step).

        Returns:
            StepResult with step details.
        """
        is_first = len(self._context) == 0

        if is_first and not task:
            raise ValueError("Task is required for the first step")

        return self._execute_step(task, is_first)

    def reset(self) -> None:
        """Reset the agent state for a new task."""
        self._context = []
        self._step_count = 0

    def _cleanup_device_screenshots(self) -> None:
        """
        Clean up temporary screenshot files on the device with retry logic.
        
        Features:
        - Automatic retry with exponential backoff
        - Verification of cleanup success
        - Detailed error reporting and logging
        - Multi-device support (if device_id is None)
        """
        try:
            from phone_agent.adb.cleanup import ScreenshotCleanupManager
            
            manager = ScreenshotCleanupManager(verbose=self.agent_config.verbose)
            result = manager.cleanup(self.agent_config.device_id)
            
            if not result.success:
                # Log the failure with details
                if self.agent_config.verbose:
                    print(f"⚠️  Cleanup failed: {result.message} (Error type: {result.error_type})")
            elif self.agent_config.verbose:
                print("✅ Device screenshots cleaned up")
        
        except Exception as e:
            # Silent failure - log but don't crash
            if self.agent_config.verbose:
                print(f"⚠️  Failed to cleanup device screenshots: {e}")
    
    def _cleanup_stale_files(self, max_age_hours: int = 24) -> None:
        """
        Check for and clean up stale screenshot files from previous failed attempts.
        
        This is Tier 1 protection: runs at the start of each task to recover from
        previous cleanup failures.
        
        Args:
            max_age_hours: Only clean files older than this many hours (default: 24).
        """
        try:
            from phone_agent.adb.cleanup import ScreenshotCleanupManager
            
            manager = ScreenshotCleanupManager(verbose=False)  # Quiet mode
            
            # Check file info
            file_info = manager.get_file_info(self.agent_config.device_id)
            
            if file_info.get("exists"):
                # File exists - check if it's stale
                result = manager.cleanup_stale_files(
                    device_id=self.agent_config.device_id,
                    max_age_hours=max_age_hours,
                )
                
                if self.agent_config.verbose and result.success:
                    if "skipping" not in result.message:
                        print(f"🧹 {result.message}")
        
        except Exception as e:
            # Silent failure in startup protection - don't interrupt task
            if self.agent_config.verbose:
                print(f"⚠️  Failed to check for stale files: {e}")

    def _execute_step(
        self, user_prompt: str | None = None, is_first: bool = False
    ) -> StepResult:
        """Execute a single step of the agent loop."""
        self._step_count += 1

        # Capture current screen state
        screenshot = get_screenshot(self.agent_config.device_id)
        current_app = get_current_app(self.agent_config.device_id)

        # If we got a black/fallback screenshot on first step, try Home to get to known state
        if (screenshot.is_sensitive or self._is_black_image(screenshot)) and is_first:
            if self.agent_config.verbose:
                print("⚠️  Detected black screen on first step, executing Home to reset...")
            # Execute Home action silently to get to a known state
            from phone_agent.adb import home
            home(self.agent_config.device_id)
            import time
            time.sleep(1)
            # Retry the step
            return self._execute_step(user_prompt, is_first)

        # Build messages
        if is_first:
            self._context.append(
                MessageBuilder.create_system_message(self.agent_config.system_prompt)
            )

            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"{user_prompt}\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )
        else:
            screen_info = MessageBuilder.build_screen_info(current_app)
            text_content = f"** Screen Info **\n\n{screen_info}"

            self._context.append(
                MessageBuilder.create_user_message(
                    text=text_content, image_base64=screenshot.base64_data
                )
            )

        # Get model response
        try:
            msgs = get_messages(self.agent_config.lang)
            print("\n" + "=" * 50)
            print(f"💭 {msgs['thinking']}:")
            print("-" * 50)
            response = self.model_client.request(self._context)
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            return StepResult(
                success=False,
                finished=True,
                action=None,
                thinking="",
                message=f"Model error: {e}",
            )

        # Parse action from response
        try:
            action = parse_action(response.action)
        except ValueError:
            if self.agent_config.verbose:
                traceback.print_exc()
            action = finish(message=response.action)

        if self.agent_config.verbose:
            # Print thinking process
            print("-" * 50)
            print(f"🎯 {msgs['action']}:")
            print(json.dumps(action, ensure_ascii=False, indent=2))
            print("=" * 50 + "\n")

        # Remove image from context to save space
        self._context[-1] = MessageBuilder.remove_images_from_message(self._context[-1])

        # Execute action
        try:
            result = self.action_handler.execute(
                action, screenshot.width, screenshot.height
            )
        except Exception as e:
            if self.agent_config.verbose:
                traceback.print_exc()
            result = self.action_handler.execute(
                finish(message=str(e)), screenshot.width, screenshot.height
            )

        # Add assistant response to context
        self._context.append(
            MessageBuilder.create_assistant_message(
                f"<think>{response.thinking}</think><answer>{response.action}</answer>"
            )
        )

        # Check if finished
        finished = action.get("_metadata") == "finish" or result.should_finish

        if finished and self.agent_config.verbose:
            msgs = get_messages(self.agent_config.lang)
            print("\n" + "🎉 " + "=" * 48)
            print(
                f"✅ {msgs['task_completed']}: {result.message or action.get('message', msgs['done'])}"
            )
            print("=" * 50 + "\n")

        return StepResult(
            success=result.success,
            finished=finished,
            action=action,
            thinking=response.thinking,
            message=result.message or action.get("message"),
        )

    @property
    def context(self) -> list[dict[str, Any]]:
        """Get the current conversation context."""
        return self._context.copy()

    @property
    def step_count(self) -> int:
        """Get the current step count."""
        return self._step_count
    @staticmethod
    def _is_black_image(screenshot: "Screenshot") -> bool:
        """Check if a screenshot appears to be all black (failed screenshot)."""
        # Check if it's a fallback image by looking at base64 properties
        # Black images are typically much smaller than real screenshots
        if not screenshot.base64_data:
            return True
        # If the base64 length is very small, it's likely a black placeholder
        return len(screenshot.base64_data) < 5000