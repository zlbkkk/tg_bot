import pymysql
from loguru import logger

# 数据库连接信息
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_PORT = 3306
DB_NAME = 'tg_bot_db'

# 创建数据库连接
def get_connection():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# 保存群组信息
def save_group(group_id, group_name):
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            # 检查群组是否已存在
            cursor.execute(
                "SELECT * FROM bot_groups WHERE group_id = %s",
                (group_id,)
            )
            existing_group = cursor.fetchone()
            
            if existing_group:
                # 更新群组信息
                cursor.execute(
                    "UPDATE bot_groups SET group_name = %s, is_active = TRUE WHERE group_id = %s",
                    (group_name, group_id)
                )
                logger.info(f"更新群组信息: {group_id} - {group_name}")
            else:
                # 插入新群组
                cursor.execute(
                    "INSERT INTO bot_groups (group_id, group_name) VALUES (%s, %s)",
                    (group_id, group_name)
                )
                logger.info(f"添加新群组: {group_id} - {group_name}")
            
            connection.commit()
            return True
    except Exception as e:
        logger.error(f"保存群组信息失败: {e}")
        return False
    finally:
        connection.close()

# 获取机器人所在的所有群组
def get_all_groups():
    connection = get_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM bot_groups WHERE is_active = TRUE ORDER BY join_date DESC"
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取群组列表失败: {e}")
        return []
    finally:
        connection.close()

# 标记群组为非活跃（机器人被踢出群组时）
def mark_group_inactive(group_id):
    connection = get_connection()
    if not connection:
        return False
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE bot_groups SET is_active = FALSE WHERE group_id = %s",
                (group_id,)
            )
            connection.commit()
            logger.info(f"标记群组为非活跃: {group_id}")
            return True
    except Exception as e:
        logger.error(f"标记群组非活跃失败: {e}")
        return False
    finally:
        connection.close() 