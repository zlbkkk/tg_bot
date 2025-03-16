from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from loguru import logger
import json
import os
import asyncio
from config import MAIN_BOT_USERNAME, ADMIN_BOT_USERNAME

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
            'auto_delete': False,
            'group_name': f'群组 {group_id}'  # 添加默认群组名称
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
    
    try:
        # 检查是否有群组ID参数
        group_id = None
        if args and args[0].lstrip('-').isdigit():
            group_id = args[0]
            logger.info(f"收到群组ID参数: {group_id}")
            
            # 获取群组配置
            config = get_group_config(group_id)
            group_name = config.get('group_name', f'群组 {group_id}')
            
            # 在消息中显示群组名称
            message_text = f'设置[ {group_name} ]，选择要更改的项目'
        else:
            # 即使没有参数也显示管理菜单
            message_text = f'设置[ 群组 ]，选择要更改的项目'
            logger.info("没有收到群组ID参数，显示默认管理菜单")
        
        # 创建管理菜单，与截图中的布局完全一致，2x8网格布局
        keyboard = [
            [
                InlineKeyboardButton("🎁 抽奖", callback_data=f'lottery{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("🔗 邀请链接", callback_data=f'invite{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("🐉 接龙", callback_data=f'chain{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("📊 统计", callback_data=f'stats{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("💬 自动回复", callback_data=f'autoreply{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("⏰ 定时消息", callback_data=f'schedule{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("🤖 验证", callback_data=f'verify{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("👋 进群欢迎", callback_data=f'welcome{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("📧 反垃圾", callback_data=f'antispam{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("💬 反刷屏", callback_data=f'antiflood{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("📢 违禁词", callback_data=f'banned_words{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("🔍 检查", callback_data=f'check{"_"+group_id if group_id else ""}')
            ],
            [
                InlineKeyboardButton("🏆 积分", callback_data=f'points{"_"+group_id if group_id else ""}'),
                InlineKeyboardButton("👤 新成员限制", callback_data=f'new_member_restriction{"_"+group_id if group_id else ""}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"在start命令中发生错误: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 发送简单的欢迎消息，不使用复杂的按钮
        await update.message.reply_text(
            '👋 欢迎使用WeGroup!\n\n'
            '请将主机器人添加到您的群组，然后通过主机器人进入管理菜单。'
        )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    # 解析回调数据
    data = query.data.split('_')
    action = data[0]
    
    # 处理select_group回调
    if action == 'select_group':
        group_id = data[1] if len(data) > 1 else None
        if group_id:
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
            
            await query.message.edit_text(
                f'设置[ 群组 ]，选择要更改的项目',
                reply_markup=reply_markup
            )
        return
    
    # 获取group_id，如果没有则使用默认值
    group_id = data[1] if len(data) > 1 else None
    
    # 处理没有group_id的回调
    if action == 'lottery' and not group_id:
        # 抽奖功能
        keyboard = [
            [
                InlineKeyboardButton("创建抽奖", callback_data='create_lottery'),
                InlineKeyboardButton("结束抽奖", callback_data='end_lottery')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data='back')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("抽奖设置", reply_markup=reply_markup)
        return
    
    elif action == 'banned_words' and not group_id:
        # 违禁词功能
        keyboard = [
            [
                InlineKeyboardButton("添加违禁词", callback_data='add_banned_word'),
                InlineKeyboardButton("删除违禁词", callback_data='remove_banned_word')
            ],
            [
                InlineKeyboardButton("查看违禁词列表", callback_data='list_banned_words')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data='back')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("违禁词设置", reply_markup=reply_markup)
        return
    
    elif action == 'points' and not group_id:
        # 积分功能
        keyboard = [
            [
                InlineKeyboardButton("积分规则", callback_data='points_rules'),
                InlineKeyboardButton("积分排行", callback_data='points_ranking')
            ],
            [
                InlineKeyboardButton("积分奖励", callback_data='points_rewards'),
                InlineKeyboardButton("积分设置", callback_data='points_settings')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data='back')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分系统设置", reply_markup=reply_markup)
        return
    
    elif action == 'new_member_restriction' and not group_id:
        # 新成员限制功能
        keyboard = [
            [
                InlineKeyboardButton("开启限制", callback_data='enable_restriction'),
                InlineKeyboardButton("关闭限制", callback_data='disable_restriction')
            ],
            [
                InlineKeyboardButton("设置限制时间", callback_data='set_restriction_time'),
                InlineKeyboardButton("设置限制条件", callback_data='set_restriction_condition')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data='back')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("新成员限制设置", reply_markup=reply_markup)
        return
    
    elif action == 'back' and not group_id:
        # 返回主菜单，与start函数中的布局保持一致
        keyboard = [
            [
                InlineKeyboardButton("🎁 抽奖", callback_data='lottery'),
                InlineKeyboardButton("🔗 邀请链接", callback_data='invite')
            ],
            [
                InlineKeyboardButton("🐉 接龙", callback_data='chain'),
                InlineKeyboardButton("📊 统计", callback_data='stats')
            ],
            [
                InlineKeyboardButton("💬 自动回复", callback_data='autoreply'),
                InlineKeyboardButton("⏰ 定时消息", callback_data='schedule')
            ],
            [
                InlineKeyboardButton("🤖 验证", callback_data='verify'),
                InlineKeyboardButton("👋 进群欢迎", callback_data='welcome')
            ],
            [
                InlineKeyboardButton("📧 反垃圾", callback_data='antispam'),
                InlineKeyboardButton("💬 反刷屏", callback_data='antiflood')
            ],
            [
                InlineKeyboardButton("📢 违禁词", callback_data='banned_words'),
                InlineKeyboardButton("🔍 检查", callback_data='check')
            ],
            [
                InlineKeyboardButton("🏆 积分", callback_data='points'),
                InlineKeyboardButton("👤 新成员限制", callback_data='new_member_restriction')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f'设置[ 群组 ]，选择要更改的项目',
            reply_markup=reply_markup
        )
        return
    
    # 处理有group_id的回调
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
    
    elif action == 'points_rules':
        # 积分规则功能
        keyboard = [
            [
                InlineKeyboardButton("添加规则", callback_data=f'add_points_rule_{group_id}'),
                InlineKeyboardButton("删除规则", callback_data=f'remove_points_rule_{group_id}')
            ],
            [
                InlineKeyboardButton("查看规则列表", callback_data=f'list_points_rules_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分规则设置", reply_markup=reply_markup)
    
    elif action == 'points_ranking':
        # 积分排行功能
        keyboard = [
            [
                InlineKeyboardButton("查看积分排行", callback_data=f'view_points_ranking_{group_id}'),
                InlineKeyboardButton("重置积分排行", callback_data=f'reset_points_ranking_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分排行设置", reply_markup=reply_markup)
    
    elif action == 'points_rewards':
        # 积分奖励功能
        keyboard = [
            [
                InlineKeyboardButton("添加奖励", callback_data=f'add_points_reward_{group_id}'),
                InlineKeyboardButton("删除奖励", callback_data=f'remove_points_reward_{group_id}')
            ],
            [
                InlineKeyboardButton("查看奖励列表", callback_data=f'list_points_rewards_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分奖励设置", reply_markup=reply_markup)
    
    elif action == 'points_settings':
        # 积分设置功能
        keyboard = [
            [
                InlineKeyboardButton("设置积分阈值", callback_data=f'set_points_threshold_{group_id}'),
                InlineKeyboardButton("设置积分周期", callback_data=f'set_points_period_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text("积分设置", reply_markup=reply_markup)

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
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    
    # 记录更详细的错误信息
    import traceback
    logger.error(f"错误详情: {traceback.format_exc()}")
    
    # 如果是在私聊中发生的错误，可以通知用户
    if update and update.effective_chat and update.effective_chat.type == 'private':
        await update.effective_message.reply_text(
            "抱歉，处理您的请求时出现了错误。管理员已收到通知，将尽快修复。"
        )

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
    
    # 添加处理私聊消息的处理器
    application.add_handler(MessageHandler(filters.CHAT_TYPE.PRIVATE & ~filters.COMMAND, handle_private_message))
    
    application.add_error_handler(error)

    # 启动机器人
    await application.initialize()
    await application.start()
    await application.run_polling()
    print("管理机器人已停止")

# 处理私聊消息
async def handle_private_message(update, context):
    """当用户在私聊中发送非命令消息时，显示管理菜单"""
    # 检查是否是第一次对话
    if not context.user_data.get('menu_shown'):
        # 标记已显示菜单
        context.user_data['menu_shown'] = True
        
        # 显示管理菜单
        # 创建管理菜单，与截图中的布局完全一致，2x8网格布局
        keyboard = [
            [
                InlineKeyboardButton("🎁 抽奖", callback_data='lottery'),
                InlineKeyboardButton("🔗 邀请链接", callback_data='invite')
            ],
            [
                InlineKeyboardButton("🐉 接龙", callback_data='chain'),
                InlineKeyboardButton("📊 统计", callback_data='stats')
            ],
            [
                InlineKeyboardButton("💬 自动回复", callback_data='autoreply'),
                InlineKeyboardButton("⏰ 定时消息", callback_data='schedule')
            ],
            [
                InlineKeyboardButton("🤖 验证", callback_data='verify'),
                InlineKeyboardButton("👋 进群欢迎", callback_data='welcome')
            ],
            [
                InlineKeyboardButton("📧 反垃圾", callback_data='antispam'),
                InlineKeyboardButton("💬 反刷屏", callback_data='antiflood')
            ],
            [
                InlineKeyboardButton("📢 违禁词", callback_data='banned_words'),
                InlineKeyboardButton("🔍 检查", callback_data='check')
            ],
            [
                InlineKeyboardButton("🏆 积分", callback_data='points'),
                InlineKeyboardButton("👤 新成员限制", callback_data='new_member_restriction')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f'设置[ 群组 ]，选择要更改的项目',
            reply_markup=reply_markup
        )

# 只有直接运行此文件时才执行main函数
if __name__ == '__main__':
    asyncio.run(main())
