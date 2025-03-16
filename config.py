"""
配置文件，存储机器人的配置信息
"""

# 主机器人配置
MAIN_BOT_TOKEN = '8057896490:AAHyuY9GnXIAqWsdwSoRO_SSsE3x4xIVsZ8'  # 替换为您的主机器人Token
MAIN_BOT_USERNAME = 'TEST999kkkBot'  # 替换为您的主机器人用户名

# 管理机器人配置
ADMIN_BOT_TOKEN = '7676940394:AAFAX1DEUyca_zvcXA2ODAaAUbyx_jdUnd0'  # 替换为您的管理机器人Token
ADMIN_BOT_USERNAME = 'TEST1_SASABOT'  # 替换为您的管理机器人用户名

# 数据库配置
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_PORT = 3306
DB_NAME = 'tg_bot_db'

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'bot.log'

# 功能配置
DEFAULT_LANGUAGE = 'zh'  # 默认语言
DEFAULT_WELCOME_MSG = '欢迎新成员加入！'  # 默认欢迎消息
ANTI_SPAM_ENABLED = False  # 默认反垃圾功能是否启用
AUTO_DELETE_ENABLED = False  # 默认自动删除功能是否启用 