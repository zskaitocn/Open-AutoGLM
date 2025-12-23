#!/usr/bin/env python3
"""
Douyin Lite Single Task Focused Automation.

This script runs ONE focused task at a time, with simplified prompts
designed for the AI's limited capabilities.

Usage:
    # Watch videos
    python examples/douyin_single_task.py watch_video
    
    # Watch advertisement
    python examples/douyin_single_task.py watch_ad
    
    # Daily check-in
    python examples/douyin_single_task.py daily_checkin
    
    # Navigate to earn coins section
    python examples/douyin_single_task.py navigate_to_earn
    
    # Simple interaction (like/comment)
    python examples/douyin_single_task.py simple_task "点赞视频"
"""

import sys
from phone_agent import PhoneAgent
from phone_agent.agent import AgentConfig
from phone_agent.model import ModelConfig
from phone_agent.config.prompts_simplified import get_focused_task_prompt


def run_single_task(task_type: str, task_description: str = ""):
    """
    Run a single focused task.
    
    Args:
        task_type: Type of task ('watch_video', 'watch_ad', 'daily_checkin', 'simple_task', 'navigate_to_earn')
        task_description: Additional description for the task
    """
    
    # Configure the model
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-Phone",
        api_key="00cc470b3663486ab28f235f9105a970.1fswSCl7PynrBOeC",
        lang="cn"
    )
    
    # Get the simplified prompt for this task
    system_prompt = get_focused_task_prompt(task_type, task_description)
    
    # Configure the agent with FOCUSED, SIMPLIFIED prompt
    agent_config = AgentConfig(
        max_steps=30,  # 减少步数，专注于单个任务
        verbose=True,
        lang="cn",
        auto_cleanup_screenshots=True,
        system_prompt=system_prompt
    )
    
    # Create the agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )
    
    # Prepare the task description
    task_descriptions = {
        "watch_video": "观看抖音推荐视频，完整播放至少3个视频。不要提前退出。",
        "watch_ad": "进入任务中心，找到广告任务，观看完整广告。重要：必须等到广告完全播放完再关闭，否则拿不到金币！",
        "daily_checkin": "每日签到任务。进入我的页面，点击签到按钮。",
        "simple_task": task_description or "完成一个简单的互动任务（点赞或评论）。",
        "navigate_to_earn": "进入抖音极速版的赚金币功能页面。",
    }
    
    task_desc = task_descriptions.get(task_type, task_description)
    
    print("=" * 70)
    print(f"【单任务聚焦】{task_type.upper()}")
    print("=" * 70)
    print(f"任务: {task_desc}")
    print(f"提示词字数: {len(system_prompt)}")
    print("-" * 70)
    print("开始执行...\n")
    
    try:
        result = agent.run(task_desc)
        print("\n" + "=" * 70)
        print("✅ 任务完成！")
        print("=" * 70)
        print(f"结果: {result}")
        print("=" * 70)
        
        # Print success indicators
        print("\n【任务成果】")
        if "finish" in result or "完成" in result:
            print("✅ AI 报告任务已完成")
        if "广告" in task_type or "ad" in task_type:
            print("✅ 请检查 App 中金币是否增加")
        if "视频" in task_type or "video" in task_type:
            print("✅ 请检查视频是否已观看")
        if "签到" in task_type or "checkin" in task_type:
            print("✅ 请检查签到状态是否已更新")
            
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ 任务执行出错！")
        print("=" * 70)
        print(f"错误: {e}")
        print("\n【可能的原因】")
        print("1. 设备未连接或 ADB 不可用")
        print("2. 网络连接异常")
        print("3. App 版本不匹配")
        print("4. 某些 UI 元素位置与提示词不符")


def print_help():
    """Print usage help."""
    print("""
【单任务聚焦自动化】

用法：python examples/douyin_single_task.py [任务类型] [可选参数]

支持的任务类型：
    
    watch_video      - 观看推荐视频（专注于完整播放）
    watch_ad         - 观看广告（关键：必须等广告播完再关闭！）
    daily_checkin    - 每日签到（简单任务）
    simple_task      - 简单互动（点赞、评论）
    navigate_to_earn - 进入赚金币功能页面

示例：

    # 观看3个推荐视频
    python examples/douyin_single_task.py watch_video
    
    # 观看一个完整广告（重点：广告必须播完）
    python examples/douyin_single_task.py watch_ad
    
    # 完成每日签到
    python examples/douyin_single_task.py daily_checkin
    
    # 点赞当前视频
    python examples/douyin_single_task.py simple_task "点赞当前视频"
    
    # 进入赚金币页面
    python examples/douyin_single_task.py navigate_to_earn

【重要提示】

⚠️ 广告任务最为关键：
   - 广告必须播完才能获得金币
   - 如果提前点击"跳过"会导致失败
   - 一定要等倒计时结束（变成"关闭"按钮）
   - 本脚本包含特殊的广告观看提示

📱 每次运行只聚焦一个任务：
   - 简化 AI 的判断难度
   - 提高任务成功率
   - 便于调试和优化

✅ 推荐执行顺序：
   1. navigate_to_earn  - 进入赚币页面
   2. daily_checkin     - 完成签到（快速，有奖励）
   3. watch_ad          - 观看广告（关键，高收益）
   4. watch_video       - 观看视频（需要多次）
   5. simple_task       - 互动任务（可选）
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    task_type = sys.argv[1].lower()
    task_details = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    if task_type in ["help", "-h", "--help"]:
        print_help()
    elif task_type in ["watch_video", "watch_ad", "daily_checkin", "simple_task", "navigate_to_earn"]:
        run_single_task(task_type, task_details)
    else:
        print(f"❌ 未知的任务类型: {task_type}")
        print_help()
        sys.exit(1)
