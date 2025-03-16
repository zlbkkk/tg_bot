from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from loguru import logger
import json
import os
import asyncio

# 存储群组配置的文件
CONFIG_FILE = 'group_configs.json'

# 加载群组配置
def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存群组配置
def save_configs(configs):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False, indent=2)

# 获取群组配置
def get_group_config(group_id):
    configs = load_configs()
    if str(group_id) not in configs:
        configs[str(group_id)] = {
            'welcome_msg': '欢迎新成员加入！',
            'language': 'zh',
            'anti_spam': False,
            'auto_delete': False
        }
        save_configs(configs)
    return configs[str(group_id)]

# 更新群组配置
def update_group_config(group_id, key, value):
    configs = load_configs()
    if str(group_id) not in configs:
        configs[str(group_id)] = {}
    configs[str(group_id)][key] = value
    save_configs(configs)

async def start(update, context):
    user_id = update.effective_user.id
    args = context.args
    
    if args and args[0].lstrip('-').isdigit():
        # 如果有参数且是数字，认为是群组ID
        group_id = args[0]
        config = get_group_config(group_id)
        
        # 创建管理菜单，与截图中的布局完全一致，2x8网格布局
        keyboard = [
            [
                InlineKeyboardButton("🎁 抽奖", callback_data=f'lottery_{group_id}'),
                InlineKeyboardButton("🔗 邀请链接", callback_data=f'invite_{group_id}')
            ],
            [
                InlineKeyboardButton("🐉 接龙", callback_data=f'chain_{group_id}'),
                InlineKeyboardButton("📊 统计", callback_data=f'stats_{group_id}')
            ],
            [
                InlineKeyboardButton("💬 自动回复", callback_data=f'autoreply_{group_id}'),
                InlineKeyboardButton("⏰ 定时消息", callback_data=f'schedule_{group_id}')
            ],
            [
                InlineKeyboardButton("🤖 验证", callback_data=f'verify_{group_id}'),
                InlineKeyboardButton("👋 进群欢迎", callback_data=f'welcome_{group_id}')
            ],
            [
                InlineKeyboardButton("📧 反垃圾", callback_data=f'antispam_{group_id}'),
                InlineKeyboardButton("💬 反刷屏", callback_data=f'antiflood_{group_id}')
            ],
            [
                InlineKeyboardButton("📢 违禁词", callback_data=f'banned_words_{group_id}'),
                InlineKeyboardButton("🔍 检查", callback_data=f'check_{group_id}')
            ],
            [
                InlineKeyboardButton("🏆 积分", callback_data=f'points_{group_id}'),
                InlineKeyboardButton("👤 新成员限制", callback_data=f'new_member_restriction_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f'设置[ 群组 ]，选择要更改的项目',
            reply_markup=reply_markup
        )
    else:
        # 私聊但没有群组ID参数
        keyboard = [
            [InlineKeyboardButton("➕ 添加我到群组", url=f"https://t.me/YourMainBot?startgroup=true")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            '👋 欢迎使用管理机器人！\n\n'
            '请先将主机器人添加到您的群组，然后通过主机器人进入管理菜单。',
            reply_markup=reply_markup
        )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    # 解析回调数据
    data = query.data.split('_')
    action = data[0]
    group_id = data[1] if len(data) > 1 else None
    
    if action == 'notify':
        # 通知功能
        keyboard = [
            [
                InlineKeyboardButton("发送通知", callback_data=f'send_notify_{group_id}'),
                InlineKeyboardButton("通知设置", callback_data=f'notify_settings_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("通知功能设置", reply_markup=reply_markup)
    
    elif action == 'game':
        # 游戏功能
        keyboard = [
            [
                InlineKeyboardButton("猜数字", callback_data=f'game_number_{group_id}'),
                InlineKeyboardButton("石头剪刀布", callback_data=f'game_rps_{group_id}')
            ],
            [
                InlineKeyboardButton("猜谜语", callback_data=f'game_riddle_{group_id}'),
                InlineKeyboardButton("更多游戏", callback_data=f'game_more_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("游戏功能设置", reply_markup=reply_markup)
    
    elif action == 'lottery':
        # 抽奖功能
        keyboard = [
            [
                InlineKeyboardButton("创建抽奖", callback_data=f'create_lottery_{group_id}'),
                InlineKeyboardButton("结束抽奖", callback_data=f'end_lottery_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("抽奖设置", reply_markup=reply_markup)
    
    elif action == 'welcome':
        # 欢迎消息设置
        config = get_group_config(group_id)
        current_msg = config.get('welcome_msg', '欢迎新成员加入！')
        
        keyboard = [
            [
                InlineKeyboardButton("启用欢迎消息", callback_data=f'enable_welcome_{group_id}'),
                InlineKeyboardButton("禁用欢迎消息", callback_data=f'disable_welcome_{group_id}')
            ],
            [
                InlineKeyboardButton("设置欢迎消息", callback_data=f'set_welcome_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            f"欢迎消息设置\n\n当前欢迎消息：\n{current_msg}",
            reply_markup=reply_markup
        )
    
    elif action == 'back':
        # 返回主菜单，与start函数中的布局保持一致
        keyboard = [
            [
                InlineKeyboardButton("🎁 抽奖", callback_data=f'lottery_{group_id}'),
                InlineKeyboardButton("🔗 邀请链接", callback_data=f'invite_{group_id}')
            ],
            [
                InlineKeyboardButton("🐉 接龙", callback_data=f'chain_{group_id}'),
                InlineKeyboardButton("📊 统计", callback_data=f'stats_{group_id}')
            ],
            [
                InlineKeyboardButton("💬 自动回复", callback_data=f'autoreply_{group_id}'),
                InlineKeyboardButton("⏰ 定时消息", callback_data=f'schedule_{group_id}')
            ],
            [
                InlineKeyboardButton("🤖 验证", callback_data=f'verify_{group_id}'),
                InlineKeyboardButton("👋 进群欢迎", callback_data=f'welcome_{group_id}')
            ],
            [
                InlineKeyboardButton("📧 反垃圾", callback_data=f'antispam_{group_id}'),
                InlineKeyboardButton("💬 反刷屏", callback_data=f'antiflood_{group_id}')
            ],
            [
                InlineKeyboardButton("📢 违禁词", callback_data=f'banned_words_{group_id}'),
                InlineKeyboardButton("🔍 检查", callback_data=f'check_{group_id}')
            ],
            [
                InlineKeyboardButton("🏆 积分", callback_data=f'points_{group_id}'),
                InlineKeyboardButton("👤 新成员限制", callback_data=f'new_member_restriction_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f'设置[ 群组 ]，选择要更改的项目',
            reply_markup=reply_markup
        )
    
    elif action == 'language':
        # 语言设置
        keyboard = [
            [
                InlineKeyboardButton("🇨🇳 中文", callback_data=f'set_lang_zh_{group_id}'),
                InlineKeyboardButton("🇺🇸 English", callback_data=f'set_lang_en_{group_id}')
            ],
            [
                InlineKeyboardButton("🇯🇵 日本語", callback_data=f'set_lang_jp_{group_id}'),
                InlineKeyboardButton("🇰🇷 한국어", callback_data=f'set_lang_kr_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("请选择语言 / Please select language", reply_markup=reply_markup)
    
    elif action.startswith('set_lang_'):
        # 设置语言
        lang = action.split('_')[2]
        update_group_config(group_id, 'language', lang)
        
        # 返回主菜单
        await query.message.reply_text(f"语言已设置为: {lang}")
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=f'设置[ 群组 ]，选择要更改的项目',
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎁 抽奖", callback_data=f'lottery_{group_id}'),
                    InlineKeyboardButton("🔗 邀请链接", callback_data=f'invite_{group_id}')
                ],
                [
                    InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
                ]
            ])
        )
    
    elif action == 'banned_words':
        # 违禁词功能
        keyboard = [
            [
                InlineKeyboardButton("添加违禁词", callback_data=f'add_banned_word_{group_id}'),
                InlineKeyboardButton("删除违禁词", callback_data=f'remove_banned_word_{group_id}')
            ],
            [
                InlineKeyboardButton("查看违禁词列表", callback_data=f'list_banned_words_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("违禁词设置", reply_markup=reply_markup)
    
    elif action == 'points':
        # 积分功能
        keyboard = [
            [
                InlineKeyboardButton("积分规则", callback_data=f'points_rules_{group_id}'),
                InlineKeyboardButton("积分排行", callback_data=f'points_ranking_{group_id}')
            ],
            [
                InlineKeyboardButton("积分奖励", callback_data=f'points_rewards_{group_id}'),
                InlineKeyboardButton("积分设置", callback_data=f'points_settings_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分系统设置", reply_markup=reply_markup)
    
    elif action == 'new_member_restriction':
        # 新成员限制功能
        keyboard = [
            [
                InlineKeyboardButton("开启限制", callback_data=f'enable_restriction_{group_id}'),
                InlineKeyboardButton("关闭限制", callback_data=f'disable_restriction_{group_id}')
            ],
            [
                InlineKeyboardButton("设置限制时间", callback_data=f'set_restriction_time_{group_id}'),
                InlineKeyboardButton("设置限制条件", callback_data=f'set_restriction_condition_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("新成员限制设置", reply_markup=reply_markup)

async def help(update, context):
    await update.message.reply_text(
        '管理机器人帮助：\n'
        '/start - 开始使用\n'
        '/help - 显示帮助信息\n\n'
        '如何使用：\n'
        '1. 将主机器人添加到您的群组\n'
        '2. 在群组中发送 /start\n'
        '3. 点击"进入管理菜单"按钮\n'
        '4. 在此机器人中配置您的群组设置'
    )

async def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

async def setup_commands(application):
    commands = [
        BotCommand("start", "开始使用管理机器人"),
        BotCommand("help", "显示帮助信息")
    ]
    await application.bot.set_my_commands(commands)

async def main():
    print("准备启动管理机器人...")
    # 请替换为您的第二个机器人的Token
    # 使用默认配置，不需要手动设置job_queue为None
    application = Application.builder().token('7676940394:AAFAX1DEUyca_zvcXA2ODAaAUbyx_jdUnd0').build()
    print("管理机器人连接成功")
    
    # 设置命令菜单
    await setup_commands(application)
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    
    # 添加按钮回调处理器
    application.add_handler(CallbackQueryHandler(button_callback))
    
    application.add_error_handler(error)

    # 启动机器人
    await application.initialize()
    await application.start()
    await application.run_polling()
    print("管理机器人已停止")

# 只有直接运行此文件时才执行main函数
if __name__ == '__main__':
    asyncio.run(main())
