#!/usr/bin/env python3
"""
Example: Douyin (TikTok China) coin earning automation.

This example demonstrates how to use the PhoneAgent to automate
browsing Douyin and earning coins through various in-app activities.

Usage:
    python examples/douyin_coins_example.py
"""

from phone_agent import PhoneAgent
from phone_agent.agent import AgentConfig
from phone_agent.model import ModelConfig
from phone_agent.config.prompts_douyin_coins import get_douyin_coins_prompt


def example_basic_coin_earning():
    """Example: Basic coin earning through video browsing."""
    
    # Configure the model (using Zhipu BigModel API)
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-Phone",
        api_key="00cc470b3663486ab28f235f9105a970.1fswSCl7PynrBOeC",
        lang="cn"
    )
    
    # Configure the agent
    agent_config = AgentConfig(
        max_steps=50,
        verbose=True,
        lang="cn",
        auto_cleanup_screenshots=True
    )
    
    # Create the agent with Douyin coins prompt
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )
    
    # Override the system prompt with Douyin coins specific prompt
    agent._system_prompt = get_douyin_coins_prompt()
    
    # Task description
    task = "打开抖音，浏览推荐视频流，每个视频观看至少3-5秒。同时完成赚金币任务，目标是获得至少100金币。"
    
    print("=" * 60)
    print("抖音赚金币任务开始")
    print("=" * 60)
    print(f"任务: {task}\n")
    
    try:
        result = agent.run(task)
        print(f"\n任务完成！\n结果: {result}")
    except Exception as e:
        print(f"\n任务执行出错: {e}")


def example_with_callbacks():
    """Example: Coin earning with user confirmation callbacks."""
    
    def confirmation_callback(message: str) -> bool:
        """
        Callback for sensitive operations (e.g., tapping payment buttons).
        Returns True to approve, False to reject.
        """
        print(f"\n[确认请求] {message}")
        response = input("是否继续? (y/n): ").strip().lower()
        return response == 'y'
    
    def takeover_callback(message: str) -> bool:
        """
        Callback for manual intervention (e.g., login, CAPTCHA).
        Returns True when user is ready to continue.
        """
        print(f"\n[需要人工操作] {message}")
        input("请完成上述操作后按Enter继续...")
        return True
    
    # Configure the model (using Zhipu BigModel API)
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-Phone",
        api_key="00cc470b3663486ab28f235f9105a970.1fswSCl7PynrBOeC",
        lang="cn"
    )
    
    # Configure the agent
    agent_config = AgentConfig(
        max_steps=100,
        verbose=True,
        lang="cn",
        auto_cleanup_screenshots=False  # Keep screenshots for debugging
    )
    
    # Create the agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
        confirmation_callback=confirmation_callback,
        takeover_callback=takeover_callback
    )
    
    # Override the system prompt
    agent._system_prompt = get_douyin_coins_prompt()
    
    # Task: Advanced coin earning with multiple strategies
    task = """
    在抖音上执行以下赚金币策略：
    1. 首先，进入抖音的"赚金币"或"任务中心"页面
    2. 查看今日所有可用的任务和活动
    3. 优先完成高收益的任务（如分享、观看广告等）
    4. 每个任务完成后要确认是否成功获得金币
    5. 然后浏览推荐视频流，尽量浏览高质量内容
    6. 对感兴趣的视频点赞以增加互动
    7. 定期检查金币余额变化
    8. 目标：在30分钟内获得至少200金币
    """
    
    print("=" * 60)
    print("抖音高级赚金币任务开始（带确认机制）")
    print("=" * 60)
    print(f"任务: {task.strip()}\n")
    
    try:
        result = agent.run(task)
        print(f"\n任务完成！\n结果: {result}")
    except Exception as e:
        print(f"\n任务执行出错: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--advanced":
        # Run advanced example with callbacks
        example_with_callbacks()
    else:
        # Run basic example
        example_basic_coin_earning()
