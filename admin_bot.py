from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from loguru import logger
import json
import os
import asyncio
from config import MAIN_BOT_USERNAME, ADMIN_BOT_USERNAME
import telegram
# 导入数据库操作模块
from db_operations import get_group_config_db, update_group_config_db, get_user_points, add_user_points, deduct_user_points
from db_operations import get_points_ranking as db_get_points_ranking
from db_operations import clear_group_points

# 存储群组配置的文件 (保留兼容性)
CONFIG_FILE = 'group_configs.json'

# 加载群组配置 (保留兼容性)
def load_configs():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# 保存群组配置 (保留兼容性)
def save_configs(configs):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False, indent=2)

# 获取群组配置 (使用数据库)
def get_group_config(group_id):
    # 从数据库获取群组配置
    config = get_group_config_db(group_id)
    
    # 如果数据库中没有配置，则使用默认值
    if not config:
        config = {
            'welcome_msg': '欢迎新成员加入！',
            'language': 'zh',
            'anti_spam': False,
            'auto_delete': False,
            'group_name': f'群组 {group_id}',
            'points_enabled': False,
            'checkin_points': 1,
            'message_points': 1,
            'daily_message_limit': 0,
            'min_message_length': 0,
            'invite_points': 1,
            'daily_invite_limit': 0,
            'points_alias': '积分',
            'ranking_alias': '积分排行'
        }
    
    return config

# 更新群组配置 (使用数据库)
def update_group_config(group_id, key, value):
    # 更新数据库中的群组配置
    return update_group_config_db(group_id, key, value)

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
    
    # 处理有group_id的抽奖功能
    elif action == 'lottery' and group_id:
        # 获取群组名称
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取该群组的抽奖次数
        lottery_count = config.get('lottery_count', 0)
        
        # 获取已开奖、未开奖和取消的数量
        opened_count = config.get('opened_lottery', 0)
        pending_count = config.get('pending_lottery', 0)
        canceled_count = config.get('canceled_lottery', 0)
        
        # 构建抽奖信息文本
        lottery_text = f"🎁 [ {group_name} ]抽奖\n\n创建的抽奖次数:{lottery_count}\n\n已开奖:{opened_count}    未开奖:{pending_count}    取消:{canceled_count}"
        
        # 创建抽奖功能按钮
        keyboard = [
            [
                InlineKeyboardButton("➕ 发起抽奖活动", callback_data=f'create_lottery_{group_id}'),
            ],
            [
                InlineKeyboardButton("📝 创建的抽奖记录", callback_data=f'lottery_records_{group_id}'),
            ],
            [
                InlineKeyboardButton("⚙️ 抽奖设置", callback_data=f'lottery_settings_{group_id}'),
            ],
            [
                InlineKeyboardButton("🏠 返回首页", callback_data=f'back_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(lottery_text, reply_markup=reply_markup)
        return
    
    # 处理创建抽奖的回调
    elif action == 'create_lottery':
        # 如果没有group_id，提示用户选择群组
        if not group_id:
            # 获取用户管理的群组列表
            groups = []
            configs = load_configs()
            for gid, config in configs.items():
                groups.append({
                    'group_id': gid,
                    'group_name': config.get('group_name', f'群组 {gid}')
                })
            
            if not groups:
                await query.message.edit_text("您还没有管理任何群组，请先将机器人添加到群组。")
                return
            
            # 创建群组选择按钮
            keyboard = []
            for group in groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👥 {group['group_name']}", 
                        callback_data=f'create_lottery_{group["group_id"]}'
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ 返回", callback_data='lottery')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("请选择要创建抽奖的群组：", reply_markup=reply_markup)
        else:
            # 直接进入创建抽奖流程
            await handle_create_lottery(update, context, group_id)
        return
    
    # 处理结束抽奖的回调
    elif action == 'end_lottery':
        # 如果没有group_id，提示用户选择群组
        if not group_id:
            # 获取用户管理的群组列表
            groups = []
            configs = load_configs()
            for gid, config in configs.items():
                # 只显示有未开奖的群组
                if config.get('pending_lottery', 0) > 0:
                    groups.append({
                        'group_id': gid,
                        'group_name': config.get('group_name', f'群组 {gid}'),
                        'pending': config.get('pending_lottery', 0)
                    })
            
            if not groups:
                await query.message.edit_text("没有找到有未开奖的群组。")
                keyboard = [[InlineKeyboardButton("⬅️ 返回", callback_data='lottery')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text("没有找到有未开奖的群组。", reply_markup=reply_markup)
                return
            
            # 创建群组选择按钮
            keyboard = []
            for group in groups:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👥 {group['group_name']} (未开奖: {group['pending']})", 
                        callback_data=f'end_lottery_{group["group_id"]}'
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("⬅️ 返回", callback_data='lottery')])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text("请选择要结束抽奖的群组：", reply_markup=reply_markup)
        else:
            # 显示该群组的未开奖列表
            await show_pending_lotteries(update, context, group_id)
        return
    
    # 处理抽奖记录的回调
    elif action == 'lottery_records':
        # 获取群组名称
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取抽奖记录
        lottery_records = config.get('lottery_records', [])
        
        if not lottery_records:
            text = f"[ {group_name} ] 还没有创建过抽奖。"
        else:
            text = f"[ {group_name} ] 的抽奖记录：\n\n"
            for i, record in enumerate(lottery_records, 1):
                status = "已开奖" if record.get('is_opened', False) else "未开奖"
                if record.get('is_canceled', False):
                    status = "已取消"
                
                text += f"{i}. {record.get('title', '无标题')} - {status}\n"
                text += f"   创建时间: {record.get('create_time', '未知')}\n"
                if status == "已开奖":
                    text += f"   开奖时间: {record.get('open_time', '未知')}\n"
                    text += f"   中奖人数: {len(record.get('winners', []))}\n"
                text += "\n"
        
        # 创建返回按钮
        keyboard = [[InlineKeyboardButton("⬅️ 返回", callback_data=f'lottery_{group_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(text, reply_markup=reply_markup)
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
    
    elif action == 'points' and group_id:
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取积分系统状态
        points_enabled = config.get('points_enabled', False)
        status_text = "✅ 启用" if points_enabled else "❌ 关闭"
        
        # 构建积分规则文本
        checkin_points = config.get('checkin_points', 1)
        message_points = config.get('message_points', 1)
        daily_message_limit = config.get('daily_message_limit', 0)
        min_message_length = config.get('min_message_length', 0)
        invite_points = config.get('invite_points', 1)
        daily_invite_limit = config.get('daily_invite_limit', 0)
        points_alias = config.get('points_alias', '积分')
        ranking_alias = config.get('ranking_alias', '积分排行')
        
        # 格式化限制文本
        daily_message_limit_text = "无限制" if daily_message_limit == 0 else str(daily_message_limit)
        min_message_length_text = "无限制" if min_message_length == 0 else str(min_message_length)
        daily_invite_limit_text = "无限制" if daily_invite_limit == 0 else str(daily_invite_limit)
        
        points_text = (
            f"积分\n\n"
            f"群成员签到或发言获得积分，消耗积分抽奖或管理员手动扣除积分。\n\n"
            f"状态: {status_text}\n"
            f"签到规则:\n"
            f"└ 发送'签到'，每日签到获得{checkin_points} 积分\n"
            f"发言规则:\n"
            f"└ 发言1次，获得{message_points} 积分\n"
            f"└ 每日获取上限{daily_message_limit_text} 积分\n"
            f"└ 最小字数长度限制: {min_message_length_text}\n"
            f"邀请规则:\n"
            f"└ 邀请1人，获得{invite_points} 积分\n"
            f"└ 每日获取上限{daily_invite_limit_text} 积分\n"
            f"积分别名:\n"
            f"└ 群组中发送'{points_alias}'查询自己的积分\n"
            f"排行别名:\n"
            f"└ 群组中发送'{ranking_alias}'查询积分排名"
        )
        
        # 创建按钮
        # 根据积分系统状态显示不同的按钮
        if points_enabled:
            status_buttons = [
                InlineKeyboardButton("状态:", callback_data=f'points_status_title_{group_id}'),
                InlineKeyboardButton("✓启用", callback_data=f'points_enable_{group_id}'),
                InlineKeyboardButton("关闭", callback_data=f'points_disable_{group_id}')
            ]
        else:
            status_buttons = [
                InlineKeyboardButton("状态:", callback_data=f'points_status_title_{group_id}'),
                InlineKeyboardButton("启用", callback_data=f'points_enable_{group_id}'),
                InlineKeyboardButton("✓关闭", callback_data=f'points_disable_{group_id}')
            ]
        
        keyboard = [
            status_buttons,
            [
                InlineKeyboardButton("⚙️ 签到规则", callback_data=f'points_checkin_rules_{group_id}'),
                InlineKeyboardButton("⚙️ 发言规则", callback_data=f'points_message_rules_{group_id}')
            ],
            [
                InlineKeyboardButton("⚙️ 邀请规则", callback_data=f'points_invite_rules_{group_id}'),
                InlineKeyboardButton("⚙️ 积分别名", callback_data=f'points_alias_{group_id}')
            ],
            [
                InlineKeyboardButton("⚙️ 排行别名", callback_data=f'points_ranking_alias_{group_id}'),
                InlineKeyboardButton("➕ 增加积分", callback_data=f'points_add_{group_id}')
            ],
            [
                InlineKeyboardButton("➖ 扣除积分", callback_data=f'points_deduct_{group_id}'),
                InlineKeyboardButton("🎁 积分抽奖", callback_data=f'points_lottery_{group_id}')
            ],
            [
                InlineKeyboardButton("🗑️ 清空数据", callback_data=f'points_clear_{group_id}'),
                InlineKeyboardButton("⬅️ 返回", callback_data=f'back_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        try:
            await query.message.edit_text(points_text, reply_markup=reply_markup)
        except telegram.error.BadRequest as e:
            if "Message is not modified" in str(e):
                # 如果消息内容没有变化，只需回答查询
                await query.answer()
            else:
                # 其他错误则重新抛出
                raise
        return
    
    # 处理积分状态切换
    elif action == 'points_enable':
        # 启用积分系统
        update_group_config(group_id, 'points_enabled', True)
        
        # 重新显示积分菜单
        await query.answer("积分系统已启用")
        query.data = f'points_{group_id}'
        await button_callback(update, context)
        return
    
    elif action == 'points_disable':
        # 禁用积分系统
        update_group_config(group_id, 'points_enabled', False)
        
        # 重新显示积分菜单
        await query.answer("积分系统已关闭")
        query.data = f'points_{group_id}'
        await button_callback(update, context)
        return
    
    # 处理积分规则设置
    elif action == 'points_checkin_rules':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取签到规则
        checkin_points = config.get('checkin_points', 1)
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("设置签到获得积分", callback_data=f'set_checkin_points_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            f"[ {group_name} ] 签到规则设置\n\n"
            f"当前设置:\n"
            f"- 每次签到获得 {checkin_points} 积分",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_message_rules':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取发言规则
        message_points = config.get('message_points', 1)
        daily_message_limit = config.get('daily_message_limit', 0)  # 0表示无限制
        min_message_length = config.get('min_message_length', 0)  # 0表示无限制
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("设置发言获得积分", callback_data=f'set_message_points_{group_id}')
            ],
            [
                InlineKeyboardButton("设置每日上限", callback_data=f'set_daily_message_limit_{group_id}')
            ],
            [
                InlineKeyboardButton("设置最小字数", callback_data=f'set_min_message_length_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 构建显示文本
        daily_limit_text = "无限制" if daily_message_limit == 0 else str(daily_message_limit)
        min_length_text = "无限制" if min_message_length == 0 else str(min_message_length)
        
        await query.message.edit_text(
            f"[ {group_name} ] 发言规则设置\n\n"
            f"当前设置:\n"
            f"- 每次发言获得 {message_points} 积分\n"
            f"- 每日获取上限: {daily_limit_text}\n"
            f"- 最小字数要求: {min_length_text}",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_invite_rules':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取邀请规则
        invite_points = config.get('invite_points', 1)
        daily_invite_limit = config.get('daily_invite_limit', 0)  # 0表示无限制
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("设置邀请获得积分", callback_data=f'set_invite_points_{group_id}')
            ],
            [
                InlineKeyboardButton("设置每日上限", callback_data=f'set_daily_invite_limit_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 构建显示文本
        daily_limit_text = "无限制" if daily_invite_limit == 0 else str(daily_invite_limit)
        
        await query.message.edit_text(
            f"[ {group_name} ] 邀请规则设置\n\n"
            f"当前设置:\n"
            f"- 每次邀请获得 {invite_points} 积分\n"
            f"- 每日获取上限: {daily_limit_text}",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_alias':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取积分别名
        points_alias = config.get('points_alias', '积分')
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("设置积分别名", callback_data=f'set_points_alias_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"[ {group_name} ] 积分别名设置\n\n"
            f"当前设置:\n"
            f"- 积分别名: {points_alias}\n"
            f"- 用户可以在群组中发送 '{points_alias}' 查询自己的积分",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_ranking_alias':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取排行别名
        ranking_alias = config.get('ranking_alias', '积分排行')
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("设置排行别名", callback_data=f'set_ranking_alias_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"[ {group_name} ] 排行别名设置\n\n"
            f"当前设置:\n"
            f"- 排行别名: {ranking_alias}\n"
            f"- 用户可以在群组中发送 '{ranking_alias}' 查询积分排名",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_add':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 设置用户状态为等待输入用户ID
        context.user_data['adding_points'] = {
            'group_id': group_id,
            'step': 'user_id'
        }
        
        # 创建取消按钮
        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_add_{group_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"您正在为 [ {group_name} ] 增加积分。\n\n"
            f"请输入用户ID或用户名(@username)：",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_deduct':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 设置用户状态为等待输入用户ID
        context.user_data['deducting_points'] = {
            'group_id': group_id,
            'step': 'user_id'
        }
        
        # 创建取消按钮
        keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_deduct_{group_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"您正在为 [ {group_name} ] 扣除积分。\n\n"
            f"请输入用户ID或用户名(@username)：",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_lottery':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 创建按钮
        keyboard = [
            [
                InlineKeyboardButton("创建积分抽奖", callback_data=f'create_points_lottery_{group_id}')
            ],
            [
                InlineKeyboardButton("查看积分抽奖", callback_data=f'view_points_lottery_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"[ {group_name} ] 积分抽奖\n\n"
            f"用户可以使用积分参与抽奖活动。",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'points_clear':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 创建确认按钮
        keyboard = [
            [
                InlineKeyboardButton("✅ 确认清空", callback_data=f'confirm_points_clear_{group_id}')
            ],
            [
                InlineKeyboardButton("❌ 取消", callback_data=f'points_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"⚠️ 警告 ⚠️\n\n"
            f"您确定要清空 [ {group_name} ] 的所有积分数据吗？\n"
            f"此操作不可逆，所有用户的积分将被重置为0。",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'confirm_points_clear':
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 清空积分数据
        update_group_config(group_id, 'user_points', {})
        
        # 创建返回按钮
        keyboard = [[InlineKeyboardButton("⬅️ 返回", callback_data=f'points_{group_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"✅ 已清空 [ {group_name} ] 的所有积分数据。",
            reply_markup=reply_markup
        )
        return
    
    elif action == 'cancel_points_add' or action == 'cancel_points_deduct':
        # 清除用户状态
        if 'adding_points' in context.user_data:
            context.user_data.pop('adding_points')
        if 'deducting_points' in context.user_data:
            context.user_data.pop('deducting_points')
        
        # 返回积分菜单
        query.data = f'points_{group_id}'
        await button_callback(update, context)
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

    # 处理确认创建抽奖的回调
    elif action == 'confirm_lottery':
        # 获取抽奖数据
        lottery_data = context.user_data.get('creating_lottery', {})
        if not lottery_data or lottery_data.get('group_id') != group_id:
            await query.message.edit_text("抽奖创建已取消或超时。")
            return
        
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 创建抽奖记录
        from datetime import datetime
        
        lottery_record = {
            'title': lottery_data['title'],
            'description': lottery_data.get('description', ''),
            'prize_count': lottery_data['prize_count'],
            'end_time': lottery_data['end_time'],
            'create_time': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'is_opened': False,
            'is_canceled': False,
            'participants': [],
            'winners': []
        }
        
        # 更新群组配置
        lottery_records = config.get('lottery_records', [])
        lottery_records.append(lottery_record)
        
        # 更新统计数据
        lottery_count = config.get('lottery_count', 0) + 1
        pending_count = config.get('pending_lottery', 0) + 1
        
        update_group_config(group_id, 'lottery_records', lottery_records)
        update_group_config(group_id, 'lottery_count', lottery_count)
        update_group_config(group_id, 'pending_lottery', pending_count)
        
        # 清除用户状态
        context.user_data.pop('creating_lottery', None)
        
        # 发送成功消息
        success_text = (
            f"✅ 抽奖创建成功！\n\n"
            f"群组：{group_name}\n"
            f"标题：{lottery_record['title']}\n"
            f"奖品数量：{lottery_record['prize_count']}\n"
            f"开奖时间：{lottery_record['end_time']}\n\n"
            f"抽奖已添加到群组，用户可以参与抽奖。"
        )
        
        # 创建返回按钮
        keyboard = [[InlineKeyboardButton("返回抽奖菜单", callback_data=f'lottery_{group_id}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(success_text, reply_markup=reply_markup)
        
        # 在群组中发送抽奖消息
        try:
            # 创建参与抽奖按钮
            participate_keyboard = [
                [InlineKeyboardButton("🎲 参与抽奖", callback_data=f'participate_lottery_{len(lottery_records)-1}')]
            ]
            participate_markup = InlineKeyboardMarkup(participate_keyboard)
            
            # 构建抽奖消息
            lottery_msg = (
                f"🎁 新抽奖活动\n\n"
                f"标题：{lottery_record['title']}\n"
            )
            
            if lottery_record['description']:
                lottery_msg += f"描述：{lottery_record['description']}\n"
            
            lottery_msg += (
                f"奖品数量：{lottery_record['prize_count']}\n"
                f"开奖时间：{lottery_record['end_time']}\n\n"
                f"点击下方按钮参与抽奖！"
            )
            
            # 发送消息到群组
            from telegram import Bot
            bot = context.bot
            await bot.send_message(
                chat_id=int(group_id),
                text=lottery_msg,
                reply_markup=participate_markup
            )
            
            logger.info(f"抽奖消息已发送到群组 {group_id}")
        except Exception as e:
            logger.error(f"发送抽奖消息到群组时出错: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            
            # 通知用户
            await query.message.reply_text(
                f"⚠️ 抽奖已创建，但发送到群组时出错。请检查机器人是否在群组中并有发送消息的权限。\n"
                f"错误信息: {str(e)}"
            )
    
    # 处理取消创建抽奖的回调
    elif action == 'cancel_lottery':
        # 清除用户状态
        context.user_data.pop('creating_lottery', None)
        
        # 发送取消消息
        await query.message.edit_text("❌ 抽奖创建已取消。")
        
        # 返回抽奖菜单
        keyboard = [[InlineKeyboardButton("返回抽奖菜单", callback_data=f'lottery{"_"+group_id if group_id else ""}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text("❌ 抽奖创建已取消。", reply_markup=reply_markup)
    
    # 处理抽奖设置的回调
    elif action == 'lottery_settings':
        # 获取群组名称
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 创建设置按钮
        keyboard = [
            [
                InlineKeyboardButton("🔔 开奖通知", callback_data=f'lottery_notify_{group_id}'),
                InlineKeyboardButton("🔄 自动开奖", callback_data=f'lottery_auto_draw_{group_id}')
            ],
            [
                InlineKeyboardButton("⬅️ 返回", callback_data=f'lottery_{group_id}')
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"[ {group_name} ] 抽奖设置", reply_markup=reply_markup)
        return

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
    # 检查是否正在创建抽奖
    if context.user_data.get('creating_lottery'):
        await handle_lottery_creation_input(update, context)
        return
    
    # 检查是否正在增加积分
    if context.user_data.get('adding_points'):
        await handle_points_add_input(update, context)
        return
    
    # 检查是否正在扣除积分
    if context.user_data.get('deducting_points'):
        await handle_points_deduct_input(update, context)
        return
        
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

# 处理增加积分的用户输入
async def handle_points_add_input(update, context):
    """处理用户在增加积分过程中的输入"""
    points_data = context.user_data['adding_points']
    group_id = points_data['group_id']
    step = points_data['step']
    
    # 获取群组名称
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_add_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 处理不同步骤的输入
    if step == 'user_id':
        # 保存用户ID或用户名
        user_identifier = update.message.text.strip()
        if not user_identifier:
            await update.message.reply_text(
                "用户ID或用户名不能为空，请重新输入：",
                reply_markup=reply_markup
            )
            return
        
        points_data['user_identifier'] = user_identifier
        points_data['step'] = 'points_amount'
        
        await update.message.reply_text(
            f"用户已设置为：{user_identifier}\n\n"
            "请输入要增加的积分数量：",
            reply_markup=reply_markup
        )
    
    elif step == 'points_amount':
        # 保存积分数量
        try:
            points_amount = int(update.message.text.strip())
            if points_amount <= 0:
                raise ValueError("积分数量必须大于0")
            
            points_data['points_amount'] = points_amount
            points_data['step'] = 'confirm'
            
            # 显示确认信息
            confirm_text = (
                f"请确认增加积分信息：\n\n"
                f"群组：{group_name}\n"
                f"用户：{points_data['user_identifier']}\n"
                f"增加积分：{points_amount}\n\n"
                f"确认增加积分？"
            )
            
            # 创建确认按钮
            keyboard = [
                [InlineKeyboardButton("✅ 确认增加", callback_data=f'confirm_points_add_{group_id}')],
                [InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_add_{group_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(confirm_text, reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text(
                "请输入有效的正整数：",
                reply_markup=reply_markup
            )

# 处理扣除积分的用户输入
async def handle_points_deduct_input(update, context):
    """处理用户在扣除积分过程中的输入"""
    points_data = context.user_data['deducting_points']
    group_id = points_data['group_id']
    step = points_data['step']
    
    # 获取群组名称
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_deduct_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 处理不同步骤的输入
    if step == 'user_id':
        # 保存用户ID或用户名
        user_identifier = update.message.text.strip()
        if not user_identifier:
            await update.message.reply_text(
                "用户ID或用户名不能为空，请重新输入：",
                reply_markup=reply_markup
            )
            return
        
        points_data['user_identifier'] = user_identifier
        points_data['step'] = 'points_amount'
        
        await update.message.reply_text(
            f"用户已设置为：{user_identifier}\n\n"
            "请输入要扣除的积分数量：",
            reply_markup=reply_markup
        )
    
    elif step == 'points_amount':
        # 保存积分数量
        try:
            points_amount = int(update.message.text.strip())
            if points_amount <= 0:
                raise ValueError("积分数量必须大于0")
            
            points_data['points_amount'] = points_amount
            points_data['step'] = 'confirm'
            
            # 显示确认信息
            confirm_text = (
                f"请确认扣除积分信息：\n\n"
                f"群组：{group_name}\n"
                f"用户：{points_data['user_identifier']}\n"
                f"扣除积分：{points_amount}\n\n"
                f"确认扣除积分？"
            )
            
            # 创建确认按钮
            keyboard = [
                [InlineKeyboardButton("✅ 确认扣除", callback_data=f'confirm_points_deduct_{group_id}')],
                [InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_deduct_{group_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(confirm_text, reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text(
                "请输入有效的正整数：",
                reply_markup=reply_markup
            )

# 处理抽奖创建过程中的用户输入
async def handle_lottery_creation_input(update, context):
    """处理用户在创建抽奖过程中的输入"""
    lottery_data = context.user_data['creating_lottery']
    group_id = lottery_data['group_id']
    step = lottery_data['step']
    
    # 获取群组名称
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_lottery_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # 处理不同步骤的输入
    if step == 'title':
        # 保存标题
        title = update.message.text.strip()
        if not title:
            await update.message.reply_text(
                "标题不能为空，请重新输入：",
                reply_markup=reply_markup
            )
            return
        
        lottery_data['title'] = title
        lottery_data['step'] = 'description'
        
        await update.message.reply_text(
            f"标题已设置为：{title}\n\n"
            "请输入抽奖描述（可选，输入 - 跳过）：",
            reply_markup=reply_markup
        )
    
    elif step == 'description':
        # 保存描述
        description = update.message.text.strip()
        if description == '-':
            description = ""
        
        lottery_data['description'] = description
        lottery_data['step'] = 'prize_count'
        
        await update.message.reply_text(
            f"描述已设置。\n\n"
            "请输入奖品数量（1-100）：",
            reply_markup=reply_markup
        )
    
    elif step == 'prize_count':
        # 保存奖品数量
        try:
            prize_count = int(update.message.text.strip())
            if prize_count < 1 or prize_count > 100:
                raise ValueError("奖品数量必须在1-100之间")
            
            lottery_data['prize_count'] = prize_count
            lottery_data['step'] = 'end_time'
            
            await update.message.reply_text(
                f"奖品数量已设置为：{prize_count}\n\n"
                "请输入开奖时间（格式：YYYY-MM-DD HH:MM，例如：2023-12-31 23:59）：",
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text(
                "请输入有效的数字（1-100）：",
                reply_markup=reply_markup
            )
    
    elif step == 'end_time':
        # 保存开奖时间
        from datetime import datetime
        
        try:
            end_time_str = update.message.text.strip()
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")
            
            # 检查时间是否有效（不能是过去的时间）
            now = datetime.now()
            if end_time <= now:
                raise ValueError("开奖时间必须是未来的时间")
            
            lottery_data['end_time'] = end_time_str
            lottery_data['step'] = 'confirm'
            
            # 显示确认信息
            confirm_text = (
                f"请确认抽奖信息：\n\n"
                f"群组：{group_name}\n"
                f"标题：{lottery_data['title']}\n"
                f"描述：{lottery_data.get('description', '无')}\n"
                f"奖品数量：{lottery_data['prize_count']}\n"
                f"开奖时间：{end_time_str}\n\n"
                f"确认创建抽奖？"
            )
            
            # 创建确认按钮
            keyboard = [
                [InlineKeyboardButton("✅ 确认创建", callback_data=f'confirm_lottery_{group_id}')],
                [InlineKeyboardButton("❌ 取消", callback_data=f'cancel_lottery_{group_id}')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(confirm_text, reply_markup=reply_markup)
        except ValueError:
            await update.message.reply_text(
                "请输入有效的时间格式（YYYY-MM-DD HH:MM）：",
                reply_markup=reply_markup
            )

# 处理创建抽奖的函数
async def handle_create_lottery(update, context, group_id):
    query = update.callback_query
    
    # 获取群组名称
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 设置用户状态为等待输入抽奖标题
    context.user_data['creating_lottery'] = {
        'group_id': group_id,
        'step': 'title',
    }
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_lottery_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"您正在为 [ {group_name} ] 创建抽奖活动。\n\n"
        "请输入抽奖标题：",
        reply_markup=reply_markup
    )

# 显示未开奖列表的函数
async def show_pending_lotteries(update, context, group_id):
    query = update.callback_query
    
    # 获取群组名称
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 获取未开奖的抽奖列表
    lottery_records = config.get('lottery_records', [])
    pending_lotteries = [
        record for record in lottery_records 
        if not record.get('is_opened', False) and not record.get('is_canceled', False)
    ]
    
    if not pending_lotteries:
        text = f"[ {group_name} ] 没有未开奖的抽奖活动。"
        keyboard = [[InlineKeyboardButton("⬅️ 返回", callback_data=f'lottery_{group_id}')]]
    else:
        text = f"[ {group_name} ] 的未开奖活动：\n\n"
        keyboard = []
        
        for i, lottery in enumerate(pending_lotteries):
            text += f"{i+1}. {lottery.get('title', '无标题')}\n"
            text += f"   创建时间: {lottery.get('create_time', '未知')}\n"
            text += f"   参与人数: {len(lottery.get('participants', []))}\n\n"
            
            # 为每个抽奖添加一个按钮
            keyboard.append([
                InlineKeyboardButton(
                    f"🎲 开奖 #{i+1} {lottery.get('title', '无标题')[:10]}...", 
                    callback_data=f'draw_lottery_{group_id}_{i}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("⬅️ 返回", callback_data=f'lottery_{group_id}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# 处理积分功能
async def handle_points_action(update, context, group_id=None):
    """处理积分功能"""
    query = update.callback_query
    
    if not group_id:
        # 如果没有指定群组ID，显示选择群组界面
        await query.answer("请选择要管理积分的群组")
        # 获取用户管理的群组列表
        admin_groups = get_admin_groups(query.from_user.id)
        
        if not admin_groups:
            await query.edit_message_text("您没有管理的群组。")
            return
        
        # 创建群组选择按钮
        keyboard = []
        for group in admin_groups:
            group_id = group['id']
            group_name = group.get('name', f'群组 {group_id}')
            keyboard.append([InlineKeyboardButton(group_name, callback_data=f'points_{group_id}')])
        
        # 添加返回主菜单按钮
        keyboard.append([InlineKeyboardButton("返回主菜单", callback_data='back_to_main')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text("请选择要管理积分的群组：", reply_markup=reply_markup)
    else:
        # 获取群组配置
        config = get_group_config(group_id)
        group_name = config.get('group_name', f'群组 {group_id}')
        
        # 获取积分统计信息
        points_stats = get_points_stats(group_id)
        total_users = points_stats.get('total_users', 0)
        total_points = points_stats.get('total_points', 0)
        
        # 创建积分管理菜单
        message_text = (
            f"【{group_name}】积分管理\n\n"
            f"当前共有 {total_users} 名用户，总积分 {total_points}\n\n"
            "请选择操作："
        )
        
        # 创建积分管理按钮
        keyboard = [
            [
                InlineKeyboardButton("📋 积分规则", callback_data=f'points_rules_{group_id}'),
                InlineKeyboardButton("🏆 积分排行", callback_data=f'points_ranking_{group_id}')
            ],
            [
                InlineKeyboardButton("🎁 积分奖励", callback_data=f'points_rewards_{group_id}'),
                InlineKeyboardButton("⚙️ 积分设置", callback_data=f'points_settings_{group_id}')
            ],
            [
                InlineKeyboardButton("➕ 增加积分", callback_data=f'add_points_{group_id}'),
                InlineKeyboardButton("➖ 扣除积分", callback_data=f'deduct_points_{group_id}')
            ],
            [InlineKeyboardButton("返回主菜单", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(message_text, reply_markup=reply_markup)

# 显示积分规则
async def show_points_rules(update, context, group_id):
    """显示积分规则"""
    query = update.callback_query
    await query.answer("正在加载积分规则...")
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 获取积分规则
    points_rules = config.get('points_rules', {})
    
    # 构建规则文本
    rules_text = f"【{group_name}】积分规则\n\n"
    
    if not points_rules:
        rules_text += "暂无积分规则，请在积分设置中添加。"
    else:
        for rule_name, rule_value in points_rules.items():
            rules_text += f"• {rule_name}: {rule_value} 积分\n"
    
    # 创建返回按钮
    keyboard = [[InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(rules_text, reply_markup=reply_markup)

# 显示积分排行榜
async def show_points_ranking(update, context, group_id):
    """显示积分排行榜"""
    query = update.callback_query
    await query.answer("正在加载积分排行榜...")
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 获取积分排行榜
    ranking = get_points_ranking(group_id)
    
    # 构建排行榜文本
    ranking_text = f"【{group_name}】积分排行榜\n\n"
    
    if not ranking:
        ranking_text += "暂无积分数据。"
    else:
        for i, user in enumerate(ranking[:10], 1):
            user_name = user.get('name', f"用户 {user.get('id')}")
            points = user.get('points', 0)
            ranking_text += f"{i}. {user_name}: {points} 积分\n"
    
    # 创建返回按钮
    keyboard = [[InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(ranking_text, reply_markup=reply_markup)

# 显示积分奖励
async def show_points_rewards(update, context, group_id):
    """显示积分奖励"""
    query = update.callback_query
    await query.answer("正在加载积分奖励...")
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 获取积分奖励
    rewards = config.get('points_rewards', {})
    
    # 构建奖励文本
    rewards_text = f"【{group_name}】积分奖励\n\n"
    
    if not rewards:
        rewards_text += "暂无积分奖励，请在积分设置中添加。"
    else:
        for points_required, reward_name in rewards.items():
            rewards_text += f"• {reward_name}: 需要 {points_required} 积分\n"
    
    # 创建返回按钮
    keyboard = [[InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(rewards_text, reply_markup=reply_markup)

# 显示积分设置
async def show_points_settings(update, context, group_id):
    """显示积分设置"""
    query = update.callback_query
    await query.answer("正在加载积分设置...")
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 获取积分设置
    points_settings = config.get('points_settings', {})
    
    # 构建设置文本
    settings_text = f"【{group_name}】积分设置\n\n"
    
    # 获取设置状态
    daily_message = points_settings.get('daily_message', False)
    auto_rewards = points_settings.get('auto_rewards', False)
    
    # 创建设置按钮
    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if daily_message else '❌'} 每日积分提醒", 
                callback_data=f'toggle_daily_message_{group_id}'
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if auto_rewards else '❌'} 自动发放奖励", 
                callback_data=f'toggle_auto_rewards_{group_id}'
            )
        ],
        [
            InlineKeyboardButton("编辑积分规则", callback_data=f'edit_points_rules_{group_id}'),
            InlineKeyboardButton("编辑积分奖励", callback_data=f'edit_points_rewards_{group_id}')
        ],
        [InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(settings_text, reply_markup=reply_markup)

# 开始增加积分流程
async def start_add_points(update, context, group_id):
    """开始增加积分流程"""
    query = update.callback_query
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 初始化增加积分状态
    context.user_data['adding_points'] = {
        'group_id': group_id,
        'step': 'user_id'
    }
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_add_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"【{group_name}】增加积分\n\n"
        "请输入要增加积分的用户ID或用户名：",
        reply_markup=reply_markup
    )

# 开始扣除积分流程
async def start_deduct_points(update, context, group_id):
    """开始扣除积分流程"""
    query = update.callback_query
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 初始化扣除积分状态
    context.user_data['deducting_points'] = {
        'group_id': group_id,
        'step': 'user_id'
    }
    
    # 创建取消按钮
    keyboard = [[InlineKeyboardButton("❌ 取消", callback_data=f'cancel_points_deduct_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"【{group_name}】扣除积分\n\n"
        "请输入要扣除积分的用户ID或用户名：",
        reply_markup=reply_markup
    )

# 确认增加积分
async def confirm_add_points(update, context, group_id):
    """确认增加积分"""
    query = update.callback_query
    
    # 检查是否有增加积分的数据
    if 'adding_points' not in context.user_data or context.user_data['adding_points']['group_id'] != group_id:
        await query.edit_message_text("增加积分操作已取消。")
        return
    
    # 获取增加积分数据
    points_data = context.user_data['adding_points']
    user_identifier = points_data.get('user_identifier')
    points_amount = points_data.get('points_amount')
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 增加积分
    success = add_user_points(group_id, user_identifier, points_amount)
    
    # 清除增加积分状态
    del context.user_data['adding_points']
    
    # 创建返回按钮
    keyboard = [[InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if success:
        await query.edit_message_text(
            f"✅ 已成功为用户 {user_identifier} 增加 {points_amount} 积分。",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            f"❌ 增加积分失败，请检查用户ID是否正确。",
            reply_markup=reply_markup
        )

# 取消增加积分
async def cancel_add_points(update, context, group_id):
    """取消增加积分"""
    query = update.callback_query
    
    # 清除增加积分状态
    if 'adding_points' in context.user_data:
        del context.user_data['adding_points']
    
    # 返回积分管理菜单
    await handle_points_action(update, context, group_id)

# 确认扣除积分
async def confirm_deduct_points(update, context, group_id):
    """确认扣除积分"""
    query = update.callback_query
    
    # 检查是否有扣除积分的数据
    if 'deducting_points' not in context.user_data or context.user_data['deducting_points']['group_id'] != group_id:
        await query.edit_message_text("扣除积分操作已取消。")
        return
    
    # 获取扣除积分数据
    points_data = context.user_data['deducting_points']
    user_identifier = points_data.get('user_identifier')
    points_amount = points_data.get('points_amount')
    
    # 获取群组配置
    config = get_group_config(group_id)
    group_name = config.get('group_name', f'群组 {group_id}')
    
    # 扣除积分
    success = deduct_user_points(group_id, user_identifier, points_amount)
    
    # 清除扣除积分状态
    del context.user_data['deducting_points']
    
    # 创建返回按钮
    keyboard = [[InlineKeyboardButton("返回积分管理", callback_data=f'back_to_points_{group_id}')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if success:
        await query.edit_message_text(
            f"✅ 已成功从用户 {user_identifier} 扣除 {points_amount} 积分。",
            reply_markup=reply_markup
        )
    else:
        await query.edit_message_text(
            f"❌ 扣除积分失败，请检查用户ID是否正确或用户积分是否足够。",
            reply_markup=reply_markup
        )

# 取消扣除积分
async def cancel_deduct_points(update, context, group_id):
    """取消扣除积分"""
    query = update.callback_query
    
    # 清除扣除积分状态
    if 'deducting_points' in context.user_data:
        del context.user_data['deducting_points']
    
    # 返回积分管理菜单
    await handle_points_action(update, context, group_id)

# 获取积分统计信息 (使用数据库)
def get_points_stats(group_id):
    # 从数据库获取群组配置
    config = get_group_config(group_id)
    
    # 返回积分统计信息
    return {
        'enabled': config.get('points_enabled', False),
        'total_users': 0,  # 这个可以从数据库中获取
        'total_points': 0  # 这个可以从数据库中获取
    }

# 获取积分排行榜 (使用数据库)
def get_points_ranking(group_id, limit=10):
    # 从数据库获取积分排行榜
    return db_get_points_ranking(group_id, limit)

# 增加用户积分 (使用数据库)
def add_user_points(group_id, user_identifier, points_amount, reason=None, admin_id=None):
    # 增加用户积分
    return add_user_points(group_id, user_identifier, points_amount, reason, admin_id)

# 扣除用户积分 (使用数据库)
def deduct_user_points(group_id, user_identifier, points_amount, reason=None, admin_id=None):
    # 扣除用户积分
    return deduct_user_points(group_id, user_identifier, points_amount, reason, admin_id)

# 获取用户管理的群组列表
def get_admin_groups(user_id):
    """获取用户管理的群组列表"""
    # 这里应该从数据库获取用户管理的群组列表
    # 示例数据
    configs = load_configs()
    admin_groups = []
    
    for group_id, config in configs.items():
        admin_groups.append({
            'id': group_id,
            'name': config.get('group_name', f'群组 {group_id}')
        })
    
    return admin_groups

# 只有直接运行此文件时才执行main函数
if __name__ == '__main__':
    asyncio.run(main())
