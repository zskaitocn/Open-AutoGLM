#!/usr/bin/env python3
"""
Task Execution Monitor - Record AI's decision-making process.

This script monitors a single task execution and records all AI steps
for analysis and debugging.

Usage:
    python scripts/monitor_task_execution.py watch_ad
    python scripts/monitor_task_execution.py watch_video
"""

import sys
import json
from datetime import datetime
from phone_agent import PhoneAgent
from phone_agent.agent import AgentConfig
from phone_agent.model import ModelConfig
from phone_agent.config.prompts_simplified import get_focused_task_prompt


class TaskExecutionMonitor:
    """Monitor and record task execution steps."""
    
    def __init__(self, task_type: str, task_description: str = ""):
        self.task_type = task_type
        self.task_description = task_description
        self.steps = []
        self.start_time = datetime.now()
        self.log_file = f"task_execution_{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log_step(self, step_number: int, step_type: str, content: str):
        """Record a single step."""
        step = {
            "step": step_number,
            "type": step_type,  # 'thinking', 'action', 'result', 'error'
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.steps.append(step)
        print(f"\n[步骤 {step_number}] {step_type.upper()}")
        print(f"{'='*70}")
        print(content[:500] if len(content) > 500 else content)
        if len(content) > 500:
            print("... (截断，完整内容见日志)")
    
    def save_log(self):
        """Save all recorded steps to file."""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"任务监控日志\n")
            f.write(f"={'='*70}\n")
            f.write(f"任务类型: {self.task_type}\n")
            f.write(f"开始时间: {self.start_time.isoformat()}\n")
            f.write(f"执行用时: {(datetime.now() - self.start_time).total_seconds():.1f} 秒\n")
            f.write(f"步骤数: {len(self.steps)}\n")
            f.write(f"{'='*70}\n\n")
            
            for step in self.steps:
                f.write(f"[步骤 {step['step']}] {step['type'].upper()}\n")
                f.write(f"时间: {step['timestamp']}\n")
                f.write(f"{'-'*70}\n")
                f.write(f"{step['content']}\n\n")
        
        print(f"\n✅ 日志已保存: {self.log_file}")
    
    def analyze_steps(self):
        """Analyze the recorded steps."""
        print(f"\n{'='*70}")
        print("【执行分析】")
        print(f"{'='*70}")
        
        thinking_steps = [s for s in self.steps if s['type'] == 'thinking']
        action_steps = [s for s in self.steps if s['type'] == 'action']
        
        print(f"\n📋 步骤统计：")
        print(f"  - 思考步骤: {len(thinking_steps)}")
        print(f"  - 动作步骤: {len(action_steps)}")
        print(f"  - 总步数: {len(self.steps)}")
        
        if action_steps:
            print(f"\n🎯 AI 执行的动作序列：")
            for i, step in enumerate(action_steps, 1):
                # 解析动作内容
                content = step['content']
                if 'Launch' in content:
                    print(f"  {i}. 启动应用")
                elif 'Tap' in content:
                    print(f"  {i}. 点击")
                elif 'Swipe' in content:
                    print(f"  {i}. 滑动")
                elif 'Type' in content:
                    print(f"  {i}. 输入文本")
                elif 'Wait' in content:
                    print(f"  {i}. 等待")
                elif 'Back' in content:
                    print(f"  {i}. 返回")
                elif 'finish' in content:
                    print(f"  {i}. ✅ 任务完成")
                else:
                    print(f"  {i}. {content[:50]}")
        
        if thinking_steps:
            print(f"\n💭 首次思考内容摘要：")
            first_thinking = thinking_steps[0]['content'][:300]
            print(f"  {first_thinking}...")


def run_monitored_task(task_type: str, task_description: str = ""):
    """Run a task with monitoring."""
    
    monitor = TaskExecutionMonitor(task_type, task_description)
    
    # Configure the model
    model_config = ModelConfig(
        base_url="https://open.bigmodel.cn/api/paas/v4",
        model_name="autoglm-Phone",
        api_key="00cc470b3663486ab28f235f9105a970.1fswSCl7PynrBOeC",
        lang="cn"
    )
    
    # Get the simplified prompt
    system_prompt = get_focused_task_prompt(task_type, task_description)
    
    # Record the prompt
    monitor.log_step(0, "info", f"使用的提示词（{len(system_prompt)} 字符）:\n\n{system_prompt}")
    
    # Configure the agent
    agent_config = AgentConfig(
        max_steps=50,
        verbose=True,
        lang="cn",
        auto_cleanup_screenshots=False,  # 保留截图用于调试
        system_prompt=system_prompt
    )
    
    # Create the agent
    agent = PhoneAgent(
        model_config=model_config,
        agent_config=agent_config,
    )
    
    # Task descriptions
    task_descriptions = {
        "watch_video": "观看抖音推荐视频，完整播放至少3个视频。不要提前退出。",
        "watch_ad": "进入任务中心，找到广告任务，观看完整广告。重要：必须等到广告完全播放完出现领取成功再关闭，否则拿不到金币！出现弹窗时，点击领取奖励。",
        "daily_checkin": "完成每日签到。",
        "simple_task": task_description or "点赞当前视频。",
        "navigate_to_earn": "进入抖音的赚金币页面。",
    }
    
    task_desc = task_descriptions.get(task_type, task_description)
    
    print("=" * 70)
    print(f"【任务监控】{task_type.upper()}")
    print("=" * 70)
    print(f"任务描述: {task_desc}")
    print(f"提示词字数: {len(system_prompt)}")
    print("-" * 70)
    print("开始执行...\n")
    
    try:
        # 这里需要修改 PhoneAgent 来记录每一步
        # 暂时先运行任务，然后手动分析输出
        result = agent.run(task_desc)
        
        monitor.log_step(99, "result", f"最终结果:\n{result}")
        
        print("\n✅ 任务执行完成")
        
    except Exception as e:
        monitor.log_step(99, "error", f"任务执行出错:\n{str(e)}")
        print(f"\n❌ 任务执行出错: {e}")
    
    # Save logs
    monitor.save_log()
    
    # Analyze
    monitor.analyze_steps()


def print_help():
    """Print usage help."""
    print("""
【任务执行监控】

用法: python scripts/monitor_task_execution.py [任务类型]

支持的任务类型:
    watch_video      - 观看视频
    watch_ad         - 观看广告  
    daily_checkin    - 每日签到
    simple_task      - 简单任务（点赞/评论）
    navigate_to_earn - 进入赚金币页面

示例:
    python scripts/monitor_task_execution.py watch_ad
    python scripts/monitor_task_execution.py watch_video

监控内容:
    ✓ 记录 AI 的完整思考过程
    ✓ 记录每一个执行动作
    ✓ 分析任务流程和决策点
    ✓ 保存日志文件用于后续分析

日志文件:
    task_execution_[task_type]_[timestamp].log
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
        run_monitored_task(task_type, task_details)
    else:
        print(f"❌ 未知任务类型: {task_type}")
        print_help()
        sys.exit(1)
