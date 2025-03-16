import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters
from loguru import logger
import importlib
import sys
import os
import signal

# 导入两个机器人的模块
sys.path.append('.')
import tg_bot_test
import admin_bot

async def run_main_bot():
    """运行主机器人"""
    print("准备启动主机器人...")
    
    # 创建主机器人应用
    main_bot = Application.builder().token('8057896490:AAHyuY9GnXIAqWsdwSoRO_SSsE3x4xIVsZ8').build()
    
    print("主机器人连接成功")
    
    # 设置主机器人命令
    await tg_bot_test.setup_commands(main_bot)
    
    # 为主机器人添加处理器
    main_bot.add_handler(CommandHandler("start", tg_bot_test.start))
    main_bot.add_handler(CommandHandler("help", tg_bot_test.help))
    main_bot.add_handler(CommandHandler("about", tg_bot_test.about))
    main_bot.add_handler(CallbackQueryHandler(tg_bot_test.button_callback))
    main_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, tg_bot_test.echo))
    main_bot.add_handler(MessageHandler(
        filters.ChatType.GROUPS & 
        (filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER), 
        tg_bot_test.handle_chat_member
    ))
    main_bot.add_handler(ChatMemberHandler(tg_bot_test.chat_member_status, ChatMemberHandler.MY_CHAT_MEMBER))
    main_bot.add_error_handler(tg_bot_test.error)
    
    # 初始化和启动主机器人
    await main_bot.initialize()
    await main_bot.start()
    
    print("主机器人已启动")
    
    # 启动轮询
    await main_bot.updater.start_polling()
    
    return main_bot

async def run_admin_bot():
    """运行管理机器人"""
    print("准备启动管理机器人...")
    
    # 创建管理机器人应用
    admin_bot_app = Application.builder().token('7676940394:AAFAX1DEUyca_zvcXA2ODAaAUbyx_jdUnd0').build()
    
    print("管理机器人连接成功")
    
    # 设置管理机器人命令
    await admin_bot.setup_commands(admin_bot_app)
    
    # 为管理机器人添加处理器
    admin_bot_app.add_handler(CommandHandler("start", admin_bot.start))
    admin_bot_app.add_handler(CommandHandler("help", admin_bot.help))
    admin_bot_app.add_handler(CallbackQueryHandler(admin_bot.button_callback))
    admin_bot_app.add_error_handler(admin_bot.error)
    
    # 初始化和启动管理机器人
    await admin_bot_app.initialize()
    await admin_bot_app.start()
    
    print("管理机器人已启动")
    
    # 启动轮询
    await admin_bot_app.updater.start_polling()
    
    return admin_bot_app

async def main():
    """主函数"""
    print("准备启动两个机器人...")
    
    # 运行两个机器人
    main_bot = await run_main_bot()
    admin_bot_app = await run_admin_bot()
    
    print("两个机器人已启动，按Ctrl+C停止")
    
    # 等待停止信号
    try:
        # 创建一个永不完成的任务，以保持程序运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # 捕获Ctrl+C
        print("正在停止机器人...")
    finally:
        # 停止两个机器人
        await main_bot.stop()
        await admin_bot_app.stop()
        print("两个机器人已停止")

if __name__ == "__main__":
    # 确保没有其他Python进程在运行
    try:
        # 获取当前进程ID
        current_pid = os.getpid()
        
        # 在Windows上使用tasklist命令查找Python进程
        if os.name == 'nt':
            os.system(f'taskkill /F /FI "IMAGENAME eq python.exe" /FI "PID ne {current_pid}"')
        # 在Linux/Mac上使用pkill命令
        else:
            os.system(f'pkill -f python -9')
        
        print("已终止其他Python进程")
    except Exception as e:
        print(f"终止其他进程时出错: {e}")
    
    # 运行两个机器人
    asyncio.run(main()) 