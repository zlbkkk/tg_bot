from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger
import db_utils
import asyncio

# 管理机器人的用户名，请替换为您的第二个机器人的用户名
ADMIN_BOT_USERNAME = "TEST1_SASABOT"  # 替换为您的管理机器人用户名

# 添加一个辅助函数来检查机器人是否为管理员
async def is_bot_admin(context, chat_id):
    """检查机器人是否为群组管理员"""
    try:
        # 获取机器人信息
        bot_info = await context.bot.get_me()
        bot_id = bot_info.id
        
        # 获取机器人在群组中的状态
        chat_member = await context.bot.get_chat_member(chat_id=chat_id, user_id=bot_id)
        
        # 判断是否为管理员
        is_admin = chat_member.status in ['administrator', 'creator']
        
        logger.info(f"机器人ID: {bot_id}, 群组ID: {chat_id}, 状态: {chat_member.status}, 是否管理员: {is_admin}")
        
        return is_admin
    except Exception as e:
        logger.error(f"检查管理员状态时出错: {e}")
        return False  # 出错时默认返回False

# 添加一个辅助函数来检查用户是否为管理员
async def is_user_admin(context, chat_id, user_id):
    """检查用户是否为群组管理员"""
    try:
        chat_member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        is_admin = chat_member.status in ['creator', 'administrator']
        logger.info(f"用户ID: {user_id}, 群组ID: {chat_id}, 状态: {chat_member.status}, 是否管理员: {is_admin}")
        return is_admin
    except Exception as e:
        logger.error(f"检查用户管理员状态时出错: {e}")
        return False  # 出错时默认返回False

async def start(update, context):
    chat_type = update.effective_chat.type
    
    
    if chat_type == 'group' or chat_type == 'supergroup':
        # 在群组中的响应
        group_id = update.effective_chat.id
        group_name = update.effective_chat.title
        user_id = update.effective_user.id
        
        # 保存群组信息到数据库
        db_utils.save_group(group_id, group_name)
        
        # 同时保存到管理机器人的配置中
        try:
            from admin_bot import get_group_config, update_group_config
            config = get_group_config(group_id)
            update_group_config(group_id, 'group_name', group_name)
        except Exception as e:
            logger.error(f"保存群组名称到配置时出错: {e}")
        
        # 检查机器人是否为管理员
        is_bot_admin_status = await is_bot_admin(context, group_id)
        logger.info(f"start命令 - 机器人管理员状态: {is_bot_admin_status}")
        
        # 检查发送命令的用户是否为管理员
        is_user_admin_status = await is_user_admin(context, group_id, user_id)
        logger.info(f"start命令 - 用户管理员状态: {is_user_admin_status}")
        
        if is_bot_admin_status:
            # 如果机器人是管理员
            if is_user_admin_status:
                # 如果用户也是管理员，显示完整的按钮
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
                # 如果用户不是管理员，显示权限不足的提示
                await update.message.reply_text(
                    '⚠️ 您不是群组管理员，无法使用管理功能。\n'
                    '请联系群组管理员进行操作。'
                )
        else:
            # 如果机器人不是管理员，只显示提示按钮，不显示管理菜单和Language按钮
            logger.warning(f"机器人在群组 {group_id} 中不是管理员")
            keyboard = [
                [InlineKeyboardButton("⚠️ 请先将我设为管理员 ⚠️", callback_data='need_admin')]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                '⚠️ 请先将我设置为管理员，否则无法使用管理功能。\n\n'
                '需要以下权限：\n'
                '- 删除消息\n'
                '- 封禁成员\n\n'
                '设置完成后，请在群组中发送 /start 命令重新开始。',
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
                # 使用标准的t.me链接格式
                group_id_str = str(group['group_id']).replace('-100', '')
                keyboard.append([
                    InlineKeyboardButton(
                        f"👥 {group['group_name']} (点击后发送/start)", 
                        url=f"https://t.me/c/{group_id_str}"
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
    
    # 获取用户ID和群组ID
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    
    # 获取机器人ID
    bot_id = context.bot.id
    
    # 记录回调数据
    logger.info(f"收到按钮回调: {query.data}, 用户ID: {user_id}, 群组ID: {chat_id}")
    
    # 继续处理原有的回调逻辑
    await query.answer()
    
    # 直接处理admin_menu和language回调
    if query.data == 'admin_menu':
        # 首先检查机器人是否为管理员
        is_bot_admin_status = await is_bot_admin(context, chat_id)
        logger.info(f"机器人管理员状态: {is_bot_admin_status}")
        
        if not is_bot_admin_status:
            # 如果机器人不是管理员，显示提示消息
            await query.message.reply_text('⚠️ 请先将我设置为管理员，否则无法使用管理功能。\n\n'
                                         '需要以下权限：\n'
                                         '- 删除消息\n'
                                         '- 封禁成员\n\n'
                                         '设置完成后，请在群组中发送 /start 命令重新开始。')
            return
        
        # 检查用户是否为群组管理员
        is_user_admin_status = await is_user_admin(context, chat_id, user_id)
        logger.info(f"用户管理员状态: {is_user_admin_status}")
        
        # 检查用户是否是TEST999kkkBot管理员
        is_bot_admin_user = await is_test999_admin(user_id, bot_id)
        logger.info(f"机器人管理员状态: {is_bot_admin_user}")
        
        if not is_user_admin_status and not is_bot_admin_user:
            # 如果用户不是管理员，显示提示消息
            await query.answer("⚠️ 只有管理员才可以使用此功能！", show_alert=True)
            return
        
        # 用户是管理员，继续处理
        logger.info(f"准备重定向到管理机器人 {ADMIN_BOT_USERNAME}")
        
        # 重定向到管理机器人
        keyboard = [
            [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={chat_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("请点击下方按钮进入管理菜单：", reply_markup=reply_markup)
        logger.info("成功发送管理菜单按钮")
        return
    
    elif query.data == 'language':
        # 首先检查机器人是否为管理员
        is_bot_admin_status = await is_bot_admin(context, chat_id)
        logger.info(f"机器人管理员状态: {is_bot_admin_status}")
        
        if not is_bot_admin_status:
            # 如果机器人不是管理员，显示提示消息
            await query.message.reply_text('⚠️ 请先将我设置为管理员，否则无法使用语言设置功能。\n\n'
                                         '需要以下权限：\n'
                                         '- 删除消息\n'
                                         '- 封禁成员\n\n'
                                         '设置完成后，请在群组中发送 /start 命令重新开始。')
            return
        
        # 检查用户是否为群组管理员
        is_user_admin_status = await is_user_admin(context, chat_id, user_id)
        logger.info(f"用户管理员状态: {is_user_admin_status}")
        
        # 检查用户是否是TEST999kkkBot管理员
        is_bot_admin_user = await is_test999_admin(user_id, bot_id)
        logger.info(f"机器人管理员状态: {is_bot_admin_user}")
        
        if not is_user_admin_status and not is_bot_admin_user:
            # 如果用户不是管理员，显示提示消息
            await query.answer("⚠️ 只有管理员才可以使用此功能！", show_alert=True)
            return
        
        # 用户是管理员，继续处理
        logger.info("准备显示语言选择菜单")
        
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
        logger.info("成功发送语言选择菜单")
        return
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
            # 在群组中，检查机器人是否为管理员
            is_bot_admin_status = await is_bot_admin(context, chat_id)
            
            # 检查用户是否为管理员
            user_id = query.from_user.id
            is_user_admin_status = await is_user_admin(context, chat_id, user_id)
            
            if is_bot_admin_status:
                if is_user_admin_status:
                    # 如果机器人和用户都是管理员，显示完整的按钮
                    keyboard = [
                        [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={chat_id}")],
                        [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
                    ]
                else:
                    # 如果用户不是管理员，显示权限不足的提示
                    await query.message.reply_text('⚠️ 您不是群组管理员，无法使用管理功能。\n'
                                                '请联系群组管理员进行操作。')
                    return
            else:
                # 如果机器人不是管理员，显示提示按钮
                keyboard = [
                    [InlineKeyboardButton("⚠️ 请先将我设为管理员 ⚠️", callback_data='need_admin')]
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
    # 在群组中，如果消息是"start"，则执行start命令
    elif update.effective_chat.type in ['group', 'supergroup']:
        if update.message.text and update.message.text.lower() == 'start':
            await start(update, context)
        # 检查是否是从链接跳转过来的用户的第一条消息
        elif update.message.text and not update.message.text.startswith('/'):
            # 获取用户ID
            user_id = update.effective_user.id
            
            # 检查是否是该用户在该群组的第一条消息
            # 这里使用context.user_data来存储用户状态
            group_id = update.effective_chat.id
            user_key = f"{user_id}_{group_id}_welcomed"
            
            if not context.user_data.get(user_key):
                # 标记已经欢迎过该用户
                context.user_data[user_key] = True
                
                # 检查机器人是否为管理员
                is_bot_admin_status = await is_bot_admin(context, group_id)
                
                # 检查用户是否为管理员
                is_user_admin_status = await is_user_admin(context, group_id, user_id)
                
                if is_bot_admin_status:
                    if is_user_admin_status:
                        # 如果机器人和用户都是管理员，显示完整的按钮
                        keyboard = [
                            [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={group_id}")],
                            [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # 使用reply_to_message_id回复用户的消息
                        await update.message.reply_text(
                            '请发送 /start 命令开始使用机器人，或点击下方按钮进入管理菜单。',
                            reply_markup=reply_markup
                        )
                    else:
                        # 如果用户不是管理员，只显示普通提示
                        await update.message.reply_text(
                            '欢迎使用机器人！请发送 /start 命令开始使用。\n'
                            '注意：管理功能仅限群组管理员使用。'
                        )
                else:
                    # 如果机器人不是管理员，只显示提示按钮
                    keyboard = [
                        [InlineKeyboardButton("⚠️ 请先将我设为管理员 ⚠️", callback_data='need_admin')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        '⚠️ 请先将我设置为管理员，否则无法使用管理功能。\n\n'
                        '需要以下权限：\n'
                        '- 删除消息\n'
                        '- 封禁成员\n\n'
                        '设置完成后，请在群组中发送 /start 命令重新开始。',
                        reply_markup=reply_markup
                    )

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
                    
                    # 自动发送start命令
                    await start(update, context)
        
        # 检查是否有成员离开
        if update.message and update.message.left_chat_member:
            chat_id = update.effective_chat.id
            
            if update.message.left_chat_member.id == context.bot.id:
                # 标记群组为非活跃
                db_utils.mark_group_inactive(chat_id)
                logger.info(f"机器人被踢出群组: {chat_id}")
                
                # 记录详细信息
                chat_title = update.effective_chat.title
                user_id = update.from_user.id if update.from_user else "未知用户"
                logger.info(f"机器人被用户 {user_id} 从群组 {chat_id} ({chat_title}) 中踢出")
    except Exception as e:
        logger.error(f"处理群组成员变化时出错: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")

# 处理机器人成员状态变化
async def chat_member_status(update, context):
    result = update.my_chat_member
    
    if result:
        chat_id = result.chat.id
        chat_title = result.chat.title
        
        # 记录详细的状态变化信息
        old_status = result.old_chat_member.status if result.old_chat_member else "unknown"
        new_status = result.new_chat_member.status if result.new_chat_member else "unknown"
        logger.info(f"机器人状态变化: {chat_id} - {chat_title}, 旧状态: {old_status}, 新状态: {new_status}")
        
        # 如果机器人被添加到群组或权限被提升为管理员
        if (old_status in ['left', 'kicked', 'restricted'] or old_status == "unknown") and new_status in ['member', 'administrator']:
            # 保存群组信息
            db_utils.save_group(chat_id, chat_title)
            logger.info(f"机器人被添加到群组或提升为管理员: {chat_id}")
        
        # 如果机器人被踢出群组或权限被降低
        elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked', 'restricted']:
            # 标记群组为非活跃
            db_utils.mark_group_inactive(chat_id)
            logger.info(f"机器人被踢出群组或权限被降低: {chat_id}")

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
    
    # 添加带有@机器人用户名的命令处理器
    bot_info = await application.bot.get_me()
    bot_username = bot_info.username
    
    # 创建一个自定义过滤器，用于处理带有@机器人用户名的命令
    async def filter_command_with_username(update, context):
        if update.message and update.message.text:
            command_pattern = f"/start@{bot_username}"
            return command_pattern in update.message.text
        return False
    
    # 添加带有@机器人用户名的start命令处理器
    application.add_handler(MessageHandler(filters.create(filter_command_with_username), start))
    
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
    
    # 添加一个特殊处理器，监听用户进入群组的事件
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_user_join))
    
    application.add_error_handler(error)

    # 启动机器人
    await application.initialize()
    await application.start()
    await application.run_polling()
    print("执行完成")

# 处理用户进入群组的事件
async def handle_user_join(update, context):
    """当用户进入群组时，提示他们输入/start命令"""
    # 检查是否是机器人自己
    if any(member.id == context.bot.id for member in update.message.new_chat_members):
        # 如果是机器人自己，已经在handle_chat_member中处理了
        return
    
    # 如果是其他用户，发送欢迎消息并提示输入/start
    try:
        # 获取群组配置
        group_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # 检查机器人是否为管理员
        is_bot_admin_status = await is_bot_admin(context, group_id)
        
        # 检查发送命令的用户是否为管理员
        is_user_admin_status = await is_user_admin(context, group_id, user_id)
        
        if is_bot_admin_status:
            if is_user_admin_status:
                # 如果机器人和用户都是管理员，显示完整的按钮
                keyboard = [
                    [InlineKeyboardButton("👨‍💻 进入管理菜单 👨‍💻", url=f"https://t.me/{ADMIN_BOT_USERNAME}?start={group_id}")],
                    [InlineKeyboardButton("🇨🇳 Language 🇨🇳", callback_data='language')]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f'欢迎新成员加入！请点击下方按钮进入管理菜单，或者发送 /start 命令开始使用机器人。',
                    reply_markup=reply_markup
                )
            else:
                # 如果用户不是管理员，只显示普通欢迎消息
                await update.message.reply_text(
                    f'欢迎新成员加入！请发送 /start 命令开始使用机器人。\n'
                    '注意：管理功能仅限群组管理员使用。'
                )
        else:
            # 如果机器人不是管理员，只显示提示按钮
            keyboard = [
                [InlineKeyboardButton("⚠️ 请先将我设为管理员 ⚠️", callback_data='need_admin')]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                '⚠️ 请先将我设置为管理员，否则无法使用管理功能。\n\n'
                '需要以下权限：\n'
                '- 删除消息\n'
                '- 封禁成员\n\n'
                '设置完成后，请在群组中发送 /start 命令重新开始。',
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"处理用户加入群组时出错: {e}")

# 只有直接运行此文件时才执行main函数
if __name__ == '__main__':
    asyncio.run(main())

