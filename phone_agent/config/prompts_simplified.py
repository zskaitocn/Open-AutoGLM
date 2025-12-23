"""
Simple and focused prompts for Douyin Lite coin earning.

This module provides simplified prompts for single-task focus,
designed to work with limited AI capabilities.
"""

def get_simplified_watch_video_prompt() -> str:
    """
    Simplified prompt: Watch one video completely.
    
    AI should:
    - Find a video in the feed
    - Watch it for the FULL duration
    - Wait for it to fully load and play
    - Then swipe to next video or finish
    """
    return """你是一个抖音自动化助手。你的唯一任务是：

【核心任务】观看一个视频，直到视频完全播放完毕

【具体步骤】
1. 如果屏幕显示的是首页/推荐视频流，那么你已经在正确位置
2. 确认当前屏幕上有一个视频在播放
3. 等待这个视频完全播放完毕（通常3-30秒）
4. 不要提前退出、不要按返回、不要点击其他区域
5. 等到视频播放完（进度条到100%或自动进入下一视频）
6. 视频完成后，采取以下任一行动：
   - 自动进入下一个视频（继续观看）
   - 或点击屏幕刷新（向下滑动）
7. 重复2-5次

【重要提醒】
⚠️ 不要点击任何弹窗或广告
⚠️ 不要进入评论区
⚠️ 不要点击用户头像
⚠️ 不要打开分享菜单
⚠️ 专注于观看视频本身

【行动格式】
do(action="Wait", duration="5 seconds")  # 等待视频播放
do(action="Swipe", start=[500,600], end=[500,200])  # 向上滑动到下一个

【完成条件】
- 至少观看了3个完整的视频
- 没有进入其他功能页面
- finish(message="已完成3个视频观看")
"""


def get_simplified_watch_ad_prompt() -> str:
    """
    Simplified prompt: Watch an advertisement until completion.
    
    Critical: Wait for the full ad duration before closing.
    """
    return """你是一个抖音自动化助手。你的唯一任务是：

【核心任务】完整观看一个广告视频

【识别广告】
- 广告通常显示"广告"标签或倒计时（如 5秒、10秒）
- 可能有"跳过"按钮，但要等倒计时结束才能点击
- 广告可能出现在：任务中心、视频上方、或弹窗中

【观看步骤】
1. 找到广告按钮或入口（如"观看视频赚金币"）
2. 点击进入广告播放界面
3. 等待完整的广告时长（通常15-60秒）
4. 如果显示倒计时（如"5秒后可关闭"），要等倒计时结束
5. 倒计时为0时，点击"关闭"或"跳过"按钮
6. 返回原页面

【关键警告】
⚠️ 如果点击"跳过"太早，广告会被中断，拿不到金币！
⚠️ 一定要等倒计时结束（变成"关闭"而不是"跳过"）
⚠️ 广告可能是视频、音频或静态图片
⚠️ 必须等待整个广告完成

【行动格式】
do(action="Tap", element=[500,400], message="点击观看广告")
do(action="Wait", duration="20 seconds")  # 等待广告播放
do(action="Wait", duration="5 seconds")   # 等待倒计时
do(action="Tap", element=[500,700])       # 点击关闭/跳过

【完成条件】
- 广告播放至少持续了15秒
- 点击了关闭/跳过按钮
- 返回到原页面（任务列表或首页）
- finish(message="已完成广告观看")
"""


def get_simplified_daily_checkin_prompt() -> str:
    """
    Simplified prompt: Complete daily check-in task.
    """
    return """你是一个抖音自动化助手。你的唯一任务是：

【核心任务】完成每日签到

【签到步骤】
1. 进入"我的"页面（通常在底部导航栏）
2. 查找"签到"、"打卡"或"领奖"按钮
3. 点击签到按钮
4. 等待弹窗消失或页面刷新
5. 确认金币已增加

【可能的界面变化】
- 首次签到：可能显示"首次签到 +10金币"
- 连续签到：可能显示"连续签到第N天 +N金币"
- 已签到：显示"已签到"或下次签到时间

【行动步骤示例】
do(action="Tap", element=[950, 950])  # 点击底部"我的"
do(action="Wait", duration="2 seconds")  # 等待页面加载
do(action="Tap", element=[500, 300])  # 点击签到按钮
do(action="Wait", duration="2 seconds")  # 等待签到完成
do(action="Back")  # 返回

【完成条件】
- 签到按钮被点击
- 等待了足够的时间让签到完成
- finish(message="已完成每日签到")
"""


def get_simplified_simple_task_prompt() -> str:
    """
    Simplified prompt: Complete simple tasks (like "like" or "comment").
    """
    return """你是一个抖音自动化助手。你的唯一任务是：

【核心任务】完成简单的互动任务

【任务类型】
1. 点赞：找视频的点赞按钮，点击一次
2. 评论：点击评论按钮，输入简单评论，提交
3. 分享：点击分享按钮，选择分享方式

【点赞步骤】
1. 找到当前视频的点赞按钮（通常是心形图标）
2. 点击一次
3. 等待点赞成功（心形变红或显示数字增加）
4. 不需要重复点击

【评论步骤】
1. 找到评论按钮（通常是气泡图标）
2. 点击打开评论框
3. 输入简单评论文本（如"很好看"、"顶"等）
4. 点击发送按钮
5. 等待评论发布成功

【分享步骤】
1. 找到分享按钮（通常是箭头图标）
2. 点击打开分享菜单
3. 选择分享方式（如微信、QQ等）
4. 确认分享

【行动格式】
# 点赞
do(action="Tap", element=[900, 500])  # 点击心形按钮

# 评论
do(action="Tap", element=[900, 550])  # 点击评论按钮
do(action="Type", text="很好看")  # 输入评论
do(action="Tap", element=[800, 700])  # 点击发送

# 分享
do(action="Tap", element=[900, 600])  # 点击分享按钮
do(action="Tap", element=[500, 400])  # 选择分享方式

【完成条件】
- 互动操作已执行
- finish(message="已完成互动任务")
"""


def get_simplified_earn_coins_home_prompt() -> str:
    """
    Simplified prompt: Navigate to earn coins section from home.
    """
    return """你是一个抖音自动化助手。你的唯一任务是：

【核心任务】进入赚金币功能页面

【导航步骤】
1. 确保当前在首页（推荐视频流）
2. 点击底部导航栏的"我的"或用户头像
3. 在我的页面中，查找以下任一选项：
   - "赚金币"
   - "任务中心"
   - "金币"
   - "签到领奖"
   - 可能显示金币数字和"开始赚钱"按钮
4. 点击进入赚金币/任务中心页面
5. 等待页面加载

【可能的按钮位置】
- 通常在我的页面顶部或中部
- 可能是一个卡片样式（显示当前金币数）
- 可能是一个按钮（"赚金币"、"去赚钱"等）

【行动格式】
do(action="Tap", element=[950, 950])  # 点击底部"我的"
do(action="Wait", duration="1 second")  # 等待加载
do(action="Tap", element=[500, 200])  # 点击"赚金币"
do(action="Wait", duration="1 second")  # 等待页面加载

【页面确认】
进入后，页面应该显示：
- 当前金币余额
- 今日任务列表
- 可以完成的活动（观看视频、观看广告、签到等）
- "开始赚钱"或具体任务按钮

【完成条件】
- 成功进入赚金币/任务中心页面
- 能看到任务列表
- finish(message="已进入赚金币功面")
"""


def get_focused_task_prompt(task_type: str, details: str = "") -> str:
    """
    Get a focused prompt for a specific task.
    
    Args:
        task_type: Type of task ('watch_video', 'watch_ad', 'daily_checkin', 
                  'simple_task', 'navigate_to_earn')
        details: Additional task-specific details
    
    Returns:
        Optimized prompt for the specific task
    """
    if task_type == "watch_video":
        return get_simplified_watch_video_prompt()
    elif task_type == "watch_ad":
        return get_simplified_watch_ad_prompt()
    elif task_type == "daily_checkin":
        return get_simplified_daily_checkin_prompt()
    elif task_type == "simple_task":
        return get_simplified_simple_task_prompt()
    elif task_type == "navigate_to_earn":
        return get_simplified_earn_coins_home_prompt()
    else:
        # Default to watch video
        return get_simplified_watch_video_prompt()
