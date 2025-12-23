"""
Test configuration for Douyin coins earning automation.

This module provides test utilities and configurations for validating
the Douyin coins earning prompt and automation workflows.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any


class DouyinTask(Enum):
    """Types of Douyin coins earning tasks."""
    
    WATCH_VIDEOS = "watch_videos"  # Watch video stream
    DAILY_SIGNIN = "daily_signin"  # Daily login reward
    WATCH_ADS = "watch_ads"  # Watch advertisement videos
    SHARE_VIDEO = "share_video"  # Share videos
    COMMENT_VIDEO = "comment_video"  # Comment on videos
    LIKE_VIDEO = "like_video"  # Like videos
    INVITE_FRIENDS = "invite_friends"  # Invite friends
    PARTICIPATE_ACTIVITY = "participate_activity"  # Join activities


class TaskDifficulty(Enum):
    """Task difficulty levels."""
    
    EASY = "easy"  # Can be fully automated
    MEDIUM = "medium"  # Requires some user interaction
    HARD = "hard"  # Requires significant user intervention


@dataclass
class DouyinCoinsTask:
    """Configuration for a single coins earning task."""
    
    task_type: DouyinTask
    name: str
    description: str
    estimated_coins: int  # Expected coins from this task
    estimated_time_seconds: int  # Expected time in seconds
    difficulty: TaskDifficulty
    automation_support: float  # 0-1, automation percentage
    prerequisites: List[str] = None  # Tasks that should be done first
    retry_count: int = 3  # Number of retries if failed
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


# Standard Douyin coins earning tasks
DOUYIN_COINS_TASKS: Dict[DouyinTask, DouyinCoinsTask] = {
    DouyinTask.WATCH_VIDEOS: DouyinCoinsTask(
        task_type=DouyinTask.WATCH_VIDEOS,
        name="刷视频",
        description="在推荐视频流中浏览视频",
        estimated_coins=20,
        estimated_time_seconds=300,  # 5 minutes
        difficulty=TaskDifficulty.EASY,
        automation_support=1.0,  # 100% automation support
        retry_count=1
    ),
    DouyinTask.DAILY_SIGNIN: DouyinCoinsTask(
        task_type=DouyinTask.DAILY_SIGNIN,
        name="每日签到",
        description="完成每日登录签到任务",
        estimated_coins=30,
        estimated_time_seconds=30,
        difficulty=TaskDifficulty.EASY,
        automation_support=0.95,  # 95% automation support
        retry_count=2
    ),
    DouyinTask.WATCH_ADS: DouyinCoinsTask(
        task_type=DouyinTask.WATCH_ADS,
        name="看广告",
        description="观看推荐的广告视频",
        estimated_coins=15,
        estimated_time_seconds=120,  # 2 minutes
        difficulty=TaskDifficulty.EASY,
        automation_support=0.9,  # 90% automation support
        retry_count=3
    ),
    DouyinTask.SHARE_VIDEO: DouyinCoinsTask(
        task_type=DouyinTask.SHARE_VIDEO,
        name="分享视频",
        description="分享视频到其他平台",
        estimated_coins=25,
        estimated_time_seconds=60,
        difficulty=TaskDifficulty.MEDIUM,
        automation_support=0.7,  # 70% automation support
        retry_count=3
    ),
    DouyinTask.COMMENT_VIDEO: DouyinCoinsTask(
        task_type=DouyinTask.COMMENT_VIDEO,
        name="评论视频",
        description="在视频下发表评论",
        estimated_coins=10,
        estimated_time_seconds=45,
        difficulty=TaskDifficulty.MEDIUM,
        automation_support=0.6,  # 60% automation support
        prerequisites=["watch_videos"],
        retry_count=3
    ),
    DouyinTask.LIKE_VIDEO: DouyinCoinsTask(
        task_type=DouyinTask.LIKE_VIDEO,
        name="点赞视频",
        description="对视频点赞",
        estimated_coins=5,
        estimated_time_seconds=20,
        difficulty=TaskDifficulty.EASY,
        automation_support=1.0,  # 100% automation support
        retry_count=1
    ),
    DouyinTask.INVITE_FRIENDS: DouyinCoinsTask(
        task_type=DouyinTask.INVITE_FRIENDS,
        name="邀请好友",
        description="邀请好友注册并完成指定操作",
        estimated_coins=100,
        estimated_time_seconds=300,
        difficulty=TaskDifficulty.HARD,
        automation_support=0.0,  # 0% automation support (requires manual)
        retry_count=1
    ),
    DouyinTask.PARTICIPATE_ACTIVITY: DouyinCoinsTask(
        task_type=DouyinTask.PARTICIPATE_ACTIVITY,
        name="参与活动",
        description="参与限时活动赚取额外金币",
        estimated_coins=50,
        estimated_time_seconds=600,
        difficulty=TaskDifficulty.MEDIUM,
        automation_support=0.5,  # 50% automation support
        retry_count=2
    )
}


@dataclass
class DouyinSession:
    """A single session of Douyin coins earning."""
    
    session_id: str
    tasks: List[DouyinCoinsTask]
    target_coins: int
    max_duration_seconds: int
    
    def total_estimated_coins(self) -> int:
        """Calculate total estimated coins from all tasks."""
        return sum(task.estimated_coins for task in self.tasks)
    
    def total_estimated_time(self) -> int:
        """Calculate total estimated time for all tasks."""
        return sum(task.estimated_time_seconds for task in self.tasks)
    
    def average_automation_support(self) -> float:
        """Calculate average automation support percentage."""
        if not self.tasks:
            return 0.0
        return sum(task.automation_support for task in self.tasks) / len(self.tasks)
    
    def is_feasible(self) -> tuple[bool, str]:
        """
        Check if the session is feasible.
        
        Returns:
            (is_feasible, reason)
        """
        estimated_time = self.total_estimated_time()
        
        if estimated_time > self.max_duration_seconds:
            return False, f"估计时间 {estimated_time}s 超过限制 {self.max_duration_seconds}s"
        
        estimated_coins = self.total_estimated_coins()
        if estimated_coins < self.target_coins:
            return False, f"估计金币 {estimated_coins} 低于目标 {self.target_coins}"
        
        automation_support = self.average_automation_support()
        if automation_support < 0.5:
            return False, f"自动化支持度 {automation_support:.1%} 太低"
        
        return True, "可行性检查通过"


# Test scenarios
TEST_SCENARIOS: Dict[str, DouyinSession] = {
    "quick_session": DouyinSession(
        session_id="quick_session",
        tasks=[
            DOUYIN_COINS_TASKS[DouyinTask.DAILY_SIGNIN],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_VIDEOS],
        ],
        target_coins=50,
        max_duration_seconds=600  # 10 minutes
    ),
    "extended_session": DouyinSession(
        session_id="extended_session",
        tasks=[
            DOUYIN_COINS_TASKS[DouyinTask.DAILY_SIGNIN],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_ADS],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_VIDEOS],
            DOUYIN_COINS_TASKS[DouyinTask.LIKE_VIDEO],
        ],
        target_coins=100,
        max_duration_seconds=1200  # 20 minutes
    ),
    "premium_session": DouyinSession(
        session_id="premium_session",
        tasks=[
            DOUYIN_COINS_TASKS[DouyinTask.DAILY_SIGNIN],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_ADS],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_VIDEOS],
            DOUYIN_COINS_TASKS[DouyinTask.LIKE_VIDEO],
            DOUYIN_COINS_TASKS[DouyinTask.SHARE_VIDEO],
        ],
        target_coins=200,
        max_duration_seconds=1800  # 30 minutes
    ),
    "aggressive_session": DouyinSession(
        session_id="aggressive_session",
        tasks=[
            DOUYIN_COINS_TASKS[DouyinTask.DAILY_SIGNIN],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_ADS],
            DOUYIN_COINS_TASKS[DouyinTask.WATCH_VIDEOS],
            DOUYIN_COINS_TASKS[DouyinTask.LIKE_VIDEO],
            DOUYIN_COINS_TASKS[DouyinTask.SHARE_VIDEO],
            DOUYIN_COINS_TASKS[DouyinTask.PARTICIPATE_ACTIVITY],
        ],
        target_coins=350,
        max_duration_seconds=2400  # 40 minutes
    )
}


# Test prompts validation
PROMPT_TEST_CASES = [
    {
        "name": "简单视频浏览",
        "task": "启动抖音，浏览推荐视频流 3 分钟，目标获得 20 金币",
        "expected_actions": ["Launch", "Swipe", "Wait"],
        "should_succeed": True
    },
    {
        "name": "完成每日任务",
        "task": "完成抖音每日签到任务获得奖励金币",
        "expected_actions": ["Launch", "Tap", "Wait"],
        "should_succeed": True
    },
    {
        "name": "多任务组合",
        "task": "在抖音完成签到、观看一个广告、浏览 5 个视频，目标获得 80 金币",
        "expected_actions": ["Launch", "Tap", "Swipe", "Wait"],
        "should_succeed": True
    },
    {
        "name": "带互动的视频浏览",
        "task": "浏览抖音推荐视频 10 分钟，对每个视频点赞，目标获得 150 金币",
        "expected_actions": ["Launch", "Swipe", "Double Tap", "Wait"],
        "should_succeed": True
    },
    {
        "name": "分享视频任务",
        "task": "在抖音上浏览热门视频并分享到其他平台，目标完成 5 次分享",
        "expected_actions": ["Launch", "Swipe", "Tap", "Wait"],
        "should_succeed": True
    }
]


def print_task_summary():
    """Print summary of all available tasks."""
    print("=" * 80)
    print("抖音赚金币任务概览")
    print("=" * 80)
    
    for task_type, task_config in DOUYIN_COINS_TASKS.items():
        print(f"\n【{task_config.name}】")
        print(f"  描述: {task_config.description}")
        print(f"  预期金币: {task_config.estimated_coins} 💰")
        print(f"  预期时间: {task_config.estimated_time_seconds}s ⏱️")
        print(f"  难度: {task_config.difficulty.value}")
        print(f"  自动化支持: {task_config.automation_support:.0%}")
        print(f"  重试次数: {task_config.retry_count}")
        if task_config.prerequisites:
            print(f"  前置条件: {', '.join(task_config.prerequisites)}")


def print_session_feasibility():
    """Print feasibility analysis for all test scenarios."""
    print("=" * 80)
    print("会话可行性分析")
    print("=" * 80)
    
    for session_id, session in TEST_SCENARIOS.items():
        feasible, reason = session.is_feasible()
        status = "✅ 可行" if feasible else "❌ 不可行"
        
        print(f"\n【{session_id}】{status}")
        print(f"  目标金币: {session.target_coins}")
        print(f"  预期金币: {session.total_estimated_coins()}")
        print(f"  预期时间: {session.total_estimated_time()}s / 限制: {session.max_duration_seconds}s")
        print(f"  自动化支持: {session.average_automation_support():.0%}")
        print(f"  原因: {reason}")


if __name__ == "__main__":
    print_task_summary()
    print("\n")
    print_session_feasibility()
