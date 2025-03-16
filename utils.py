"""
工具函数模块，提供各种辅助功能
"""
import json
import os
import random
import string
from datetime import datetime, timedelta
from loguru import logger

# 生成随机字符串
def generate_random_string(length=8):
    """生成指定长度的随机字符串"""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

# 格式化时间
def format_time(dt=None, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化时间"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)

# 计算时间差
def time_diff(start_time, end_time=None):
    """计算时间差，返回秒数"""
    if end_time is None:
        end_time = datetime.now()
    return (end_time - start_time).total_seconds()

# 加载JSON文件
def load_json(file_path):
    """加载JSON文件"""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载JSON文件失败: {e}")
        return {}

# 保存JSON文件
def save_json(file_path, data):
    """保存JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return False

# 检查是否是管理员
async def is_admin(bot, chat_id, user_id):
    """检查用户是否是管理员"""
    try:
        chat_member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"检查管理员状态失败: {e}")
        return False

# 获取群组成员数量
async def get_member_count(bot, chat_id):
    """获取群组成员数量"""
    try:
        count = await bot.get_chat_member_count(chat_id)
        return count
    except Exception as e:
        logger.error(f"获取群组成员数量失败: {e}")
        return 0

# 检查文本是否包含违禁词
def contains_banned_words(text, banned_words):
    """检查文本是否包含违禁词"""
    if not text or not banned_words:
        return False
    
    text = text.lower()
    for word in banned_words:
        if word.lower() in text:
            return True
    return False 