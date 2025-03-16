from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger
import db_utils
import asyncio

# 管理机器人的用户名，请替换为您的第二个机器人的用户名
ADMIN_BOT_USERNAME = "TEST1_SASABOT"  # 替换为您的管理机器人用户名

async def start(update, context):
    chat_type = update.effective_chat.type
    
    
    if chat_type == 'group' or chat_type == 'supergroup':
        # 在群组中的响应
        group_id = update.effective_chat.id
        group_name = update.effective_chat.title
        
        # 保存群组信息到数据库
        db_utils.save_group(group_id, group_name)
        
        # 检查机器人是否为管理员
        try:
            # 直接获取机器人的信息
            bot_info = await context.bot.get_me()
            bot_id = bot_info.id
            
            # 获取机器人在群组中的状态
            chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=bot_id)
            
            # 记录详细日志
            logger.info(f"机器人ID: {bot_id}, 群组ID: {group_id}, 状态: {chat_member.status}")
            logger.info(f"机器人权限: {chat_member.to_dict()}")
            
            # 放宽判断条件，只要不是restricted或left就认为是管理员
            is_admin = chat_member.status not in ['restricted', 'left', 'kicked']
            
            if is_admin:
                keyboard = [
                    [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={group_id}")],
                    [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
                ]
            else:
                logger.warning(f"机器人在群组 {group_id} 中不是管理员，状态: {chat_member.status}")
                keyboard = [
                    [InlineKeyboardButton("⚠️ 请先将我设为管理员 ⚠️", callback_data='need_admin')]
                ]
        except Exception as e:
            logger.error(f"检查管理员状态时出错: {e}")
            # 出错时默认显示所有按钮
            keyboard = [
                [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={group_id}")],
                [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            '欢迎使用机器人:\n'
            '1)请将我设置为管理员，否则我无法回复命令，请至少赋予以下权限：\n'
            '- 删除消息\n'
            '- 封禁成员\n'
            '2)在机器人私聊中发送 /start 打开管理菜单。\n'
            '(本消息仅机器人入群时提醒)',
            reply_markup=reply_markup
        )
    else:
        # 在私聊中的响应
        # 获取机器人所在的群组列表
        groups = db_utils.get_all_groups()
        
        # 创建添加到群组的按钮
        keyboard = [
            [InlineKeyboardButton("➕ 添加到群组", url=f"https://t.me/{context.bot.username}?startgroup=true")]
        ]
        
        # 如果有群组，添加群组按钮
        if groups:
            # 添加标题行
            keyboard.append([InlineKeyboardButton("🔽 【下发是已加入的群组】 🔽", callback_data='group_title')])
            
            # 为每个群组添加一个按钮
            for group in groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👥 {group['group_name']}", 
                        url=f"https://t.me/c/{str(group['group_id']).replace('-100', '')}"
                    )
                ])
        
        # 添加其他功能按钮
        keyboard.append([
            InlineKeyboardButton("📢 添加频道", callback_data='add_channel'),
            InlineKeyboardButton("👥 添加群组", callback_data='add_group')
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            '👋 欢迎使用机器人！\n\n'
            '请将我添加到您的群组，并赋予管理员权限。\n'
            '然后在群组中发送 /start 开始使用。',
            reply_markup=reply_markup
        )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'language':
        # 直接显示语言选择选项，不再检查管理员状态
        # 创建语言选择按钮
        keyboard = [
            [
                InlineKeyboardButton("🇨🇳 中文", callback_data='set_lang_zh'),
                InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')
            ],
            [
                InlineKeyboardButton("🇯🇵 日本語", callback_data='set_lang_jp'),
                InlineKeyboardButton("🇰🇷 한국어", callback_data='set_lang_kr')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data='back_to_main')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('请选择语言 / Please select language / 言語を選択してください', reply_markup=reply_markup)
    elif query.data == 'need_admin':
        await query.message.reply_text('⚠️ 请先将我设置为管理员，否则无法使用管理功能。\n\n'
                                      '需要以下权限：\n'
                                      '- 删除消息\n'
                                      '- 封禁成员\n\n'
                                      '设置完成后，请在群组中发送 /start 命令重新开始。')
    elif query.data == 'add_channel':
        await query.message.reply_text('请将机器人添加为频道管理员，然后转发一条频道消息给机器人。')
    elif query.data == 'add_group':
        # 获取机器人所在的群组列表
        groups = db_utils.get_all_groups()
        
        if groups:
            # 构建群组列表文本
            groups_text = "我已经加入了以下群组：\n\n"
            for i, group in enumerate(groups, 1):
                groups_text += f"{i}. {group['group_name']}\n"
            
            groups_text += "\n如果要添加到新群组，请点击下方按钮。"
            
            # 创建添加到群组的按钮
            keyboard = [
                [InlineKeyboardButton("➕ 添加到新群组", url=f"https://t.me/{context.bot.username}?startgroup=true")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(groups_text, reply_markup=reply_markup)
        else:
            await query.message.reply_text('请将机器人添加到您的群组，并赋予管理员权限。')
    elif query.data == 'group_title':
        # 这只是一个标题，不做任何操作
        pass
    elif query.data.startswith('set_lang_'):
        # 处理语言选择
        lang = query.data.split('_')[2]
        # 这里可以添加保存用户语言选择的代码
        lang_names = {
            'zh': '中文',
            'en': 'English',
            'jp': '日本語',
            'kr': '한국어'
        }
        await query.message.reply_text(f'语言已设置为: {lang_names.get(lang, lang)}')
    elif query.data == 'back_to_main':
        # 返回主菜单
        chat_id = query.message.chat.id
        if query.message.chat.type in ['group', 'supergroup']:
            # 在群组中
            keyboard = [
                [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={chat_id}")],
                [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
            ]
        else:
            # 在私聊中
            keyboard = [
                [InlineKeyboardButton("➕ 添加到群组", url=f"https://t.me/{context.bot.username}?startgroup=true")],
                [
                    InlineKeyboardButton("📢 添加频道", callback_data='add_channel'),
                    InlineKeyboardButton("👥 添加群组", callback_data='add_group')
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('请选择操作:', reply_markup=reply_markup)

async def help(update, context):
    await update.message.reply_text('这是帮助信息：\n/start - 开始使用\n/help - 显示帮助\n/about - 关于我们')

async def about(update, context):
    await update.message.reply_text('这是一个群组管理机器人')

async def echo(update, context):
    # 只在私聊中回复消息
    if update.effective_chat.type == 'private':
        await update.message.reply_text('请使用 /start 命令开始使用机器人')

async def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# 处理机器人被踢出群组的情况
async def handle_chat_member(update, context):
    try:
        # 检查是否有新成员加入
        if update.message and update.message.new_chat_members:
            chat_id = update.effective_chat.id
            chat_title = update.effective_chat.title
            
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    # 保存群组信息
                    db_utils.save_group(chat_id, chat_title)
                    logger.info(f"机器人被添加到群组: {chat_id}")
        
        # 检查是否有成员离开
        if update.message and update.message.left_chat_member:
            chat_id = update.effective_chat.id
            
            if update.message.left_chat_member.id == context.bot.id:
                # 标记群组为非活跃
                db_utils.mark_group_inactive(chat_id)
                logger.info(f"机器人被踢出群组: {chat_id}")
    except Exception as e:
        logger.error(f"处理群组成员变化时出错: {e}")

# 处理机器人成员状态变化
async def chat_member_status(update, context):
    result = update.my_chat_member
    
    if result:
        chat_id = result.chat.id
        chat_title = result.chat.title
        
        # 如果机器人被添加到群组
        if result.new_chat_member and result.new_chat_member.status in ['member', 'administrator']:
            # 保存群组信息
            db_utils.save_group(chat_id, chat_title)
            logger.info(f"机器人被添加到群组 (通过状态变化): {chat_id}")
        
        # 如果机器人被踢出群组
        if result.new_chat_member and result.new_chat_member.status in ['left', 'kicked']:
            # 标记群组为非活跃
            db_utils.mark_group_inactive(chat_id)
            logger.info(f"机器人被踢出群组 (通过状态变化): {chat_id}")

async def setup_commands(application):
    commands = [
        BotCommand("start", "开始使用，打开菜单"),
        BotCommand("help", "显示帮助"),
        BotCommand("about", "关于我们")
    ]
    await application.bot.set_my_commands(commands)

async def main():
    print("准备开始链接")
    # 使用默认配置，不需要手动设置job_queue为None
    application = Application.builder().token('8057896490:AAHyuY9GnXIAqWsdwSoRO_SSsE3x4xIVsZ8').build()
    print("链接成功")
    
    # 设置命令菜单
    await setup_commands(application)
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("about", about))
    
    # 添加按钮回调处理器
    application.add_handler(CallbackQueryHandler(button_callback))

    # 处理普通消息
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # 处理群组成员变化（机器人被踢出或添加到群组）
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & (filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER), handle_chat_member))
    
    # 处理机器人成员状态变化
    application.add_handler(ChatMemberHandler(chat_member_status, ChatMemberHandler.MY_CHAT_MEMBER))
    
    application.add_error_handler(error)

    # 启动机器人
    await application.initialize()
    await application.start()
    await application.run_polling()
    print("执行完成")

# 只有直接运行此文件时才执行main函数
if __name__ == '__main__':
    asyncio.run(main())

