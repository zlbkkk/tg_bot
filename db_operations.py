import pymysql
from loguru import logger
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME

def get_db_connection():
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            database=DB_NAME,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

# 群组配置相关操作
def get_group_config_db(group_id):
    """从数据库获取群组配置"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor()
    try:
        # 检查群组是否存在
        cursor.execute("SELECT * FROM group_configs WHERE group_id = %s", (group_id,))
        group_config = cursor.fetchone()
        
        if not group_config:
            # 如果群组不存在，创建默认配置
            cursor.execute(
                "INSERT INTO group_configs (group_id, group_name, welcome_msg, language) VALUES (%s, %s, %s, %s)",
                (group_id, f'群组 {group_id}', '欢迎新成员加入！', 'zh')
            )
            conn.commit()
            
            # 重新获取配置
            cursor.execute("SELECT * FROM group_configs WHERE group_id = %s", (group_id,))
            group_config = cursor.fetchone()
        
        # 获取积分系统配置
        cursor.execute("SELECT * FROM points_configs WHERE group_id = %s", (group_id,))
        points_config = cursor.fetchone()
        
        if not points_config:
            # 如果积分配置不存在，创建默认配置
            cursor.execute(
                "INSERT INTO points_configs (group_id) VALUES (%s)",
                (group_id,)
            )
            conn.commit()
            
            # 重新获取积分配置
            cursor.execute("SELECT * FROM points_configs WHERE group_id = %s", (group_id,))
            points_config = cursor.fetchone()
        
        # 合并两个配置
        result = {**group_config, **points_config} if group_config and points_config else {}
        return result
    except Exception as e:
        logger.error(f"获取群组配置失败: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def update_group_config_db(group_id, key, value):
    """更新群组配置到数据库"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 确定更新哪个表
        if key in ['group_name', 'welcome_msg', 'language', 'anti_spam', 'auto_delete']:
            table = 'group_configs'
        elif key in ['points_enabled', 'checkin_points', 'message_points', 'daily_message_limit', 
                    'min_message_length', 'invite_points', 'daily_invite_limit', 
                    'points_alias', 'ranking_alias']:
            table = 'points_configs'
        else:
            logger.error(f"未知的配置键: {key}")
            return False
        
        # 检查记录是否存在
        cursor.execute(f"SELECT 1 FROM {table} WHERE group_id = %s", (group_id,))
        exists = cursor.fetchone()
        
        if exists:
            # 更新记录
            cursor.execute(f"UPDATE {table} SET {key} = %s WHERE group_id = %s", (value, group_id))
        else:
            # 如果是group_configs表且记录不存在
            if table == 'group_configs':
                cursor.execute(
                    "INSERT INTO group_configs (group_id, group_name, welcome_msg, language, anti_spam, auto_delete) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    (group_id, f'群组 {group_id}', '欢迎新成员加入！', 'zh', False, False)
                )
                # 如果key不是默认插入的字段，再次更新
                if key not in ['group_name', 'welcome_msg', 'language', 'anti_spam', 'auto_delete']:
                    cursor.execute(f"UPDATE {table} SET {key} = %s WHERE group_id = %s", (value, group_id))
            
            # 如果是points_configs表且记录不存在
            elif table == 'points_configs':
                # 确保group_configs表中有记录
                cursor.execute("SELECT 1 FROM group_configs WHERE group_id = %s", (group_id,))
                group_exists = cursor.fetchone()
                
                if not group_exists:
                    cursor.execute(
                        "INSERT INTO group_configs (group_id, group_name) VALUES (%s, %s)",
                        (group_id, f'群组 {group_id}')
                    )
                
                # 插入积分配置记录
                cursor.execute(
                    "INSERT INTO points_configs (group_id, points_enabled, checkin_points, message_points, "
                    "daily_message_limit, min_message_length, invite_points, daily_invite_limit, "
                    "points_alias, ranking_alias) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (group_id, False, 1, 1, 0, 0, 1, 0, '积分', '积分排行')
                )
                # 如果key不是默认插入的字段，再次更新
                cursor.execute(f"UPDATE {table} SET {key} = %s WHERE group_id = %s", (value, group_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"更新群组配置失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# 用户积分相关操作
def get_user_points(group_id, user_id):
    """获取用户积分"""
    conn = get_db_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT points FROM user_points WHERE group_id = %s AND user_id = %s",
            (group_id, user_id)
        )
        result = cursor.fetchone()
        return result['points'] if result else 0
    except Exception as e:
        logger.error(f"获取用户积分失败: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

def add_user_points(group_id, user_id, points, reason=None, admin_id=None):
    """增加用户积分"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 检查用户是否存在
        cursor.execute(
            "SELECT points FROM user_points WHERE group_id = %s AND user_id = %s",
            (group_id, user_id)
        )
        user_exists = cursor.fetchone()
        
        if user_exists:
            # 更新积分
            cursor.execute(
                "UPDATE user_points SET points = points + %s WHERE group_id = %s AND user_id = %s",
                (points, group_id, user_id)
            )
        else:
            # 插入新记录
            cursor.execute(
                "INSERT INTO user_points (group_id, user_id, points) VALUES (%s, %s, %s)",
                (group_id, user_id, points)
            )
        
        # 记录积分变动历史
        cursor.execute(
            "INSERT INTO points_history (group_id, user_id, points_change, reason, admin_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (group_id, user_id, points, reason, admin_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"增加用户积分失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def deduct_user_points(group_id, user_id, points, reason=None, admin_id=None):
    """扣除用户积分"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 检查用户是否存在且积分是否足够
        cursor.execute(
            "SELECT points FROM user_points WHERE group_id = %s AND user_id = %s",
            (group_id, user_id)
        )
        user_points = cursor.fetchone()
        
        if not user_points or user_points['points'] < points:
            return False
        
        # 更新积分
        cursor.execute(
            "UPDATE user_points SET points = points - %s WHERE group_id = %s AND user_id = %s",
            (points, group_id, user_id)
        )
        
        # 记录积分变动历史
        cursor.execute(
            "INSERT INTO points_history (group_id, user_id, points_change, reason, admin_id) "
            "VALUES (%s, %s, %s, %s, %s)",
            (group_id, user_id, -points, reason, admin_id)
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"扣除用户积分失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_points_ranking(group_id, limit=10):
    """获取积分排行榜"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT user_id, points FROM user_points "
            "WHERE group_id = %s ORDER BY points DESC LIMIT %s",
            (group_id, limit)
        )
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"获取积分排行榜失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def clear_group_points(group_id):
    """清空群组所有用户的积分"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 删除用户积分记录
        cursor.execute("DELETE FROM user_points WHERE group_id = %s", (group_id,))
        
        # 记录清空操作到历史记录
        cursor.execute(
            "INSERT INTO points_history (group_id, user_id, points_change, reason) "
            "VALUES (%s, %s, %s, %s)",
            (group_id, 0, 0, "清空群组积分")
        )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"清空群组积分失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# 签到相关操作
def record_user_checkin(group_id, user_id, points):
    """记录用户签到"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 检查今日是否已签到
        cursor.execute(
            "SELECT 1 FROM checkin_records WHERE group_id = %s AND user_id = %s AND checkin_date = CURDATE()",
            (group_id, user_id)
        )
        already_checked_in = cursor.fetchone()
        
        if already_checked_in:
            return False
        
        # 记录签到
        cursor.execute(
            "INSERT INTO checkin_records (group_id, user_id, checkin_date, points_earned) "
            "VALUES (%s, %s, CURDATE(), %s)",
            (group_id, user_id, points)
        )
        
        # 增加用户积分
        add_user_points(group_id, user_id, points, "每日签到")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"记录用户签到失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# 发言积分相关操作
def record_message_points(group_id, user_id, points):
    """记录用户发言积分"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 检查今日是否已有记录
        cursor.execute(
            "SELECT points_earned, message_count FROM message_points_records "
            "WHERE group_id = %s AND user_id = %s AND message_date = CURDATE()",
            (group_id, user_id)
        )
        today_record = cursor.fetchone()
        
        # 获取每日上限
        cursor.execute(
            "SELECT daily_message_limit FROM points_configs WHERE group_id = %s",
            (group_id,)
        )
        config = cursor.fetchone()
        daily_limit = config['daily_message_limit'] if config else 0
        
        # 检查是否达到每日上限
        if today_record:
            if daily_limit > 0 and today_record['points_earned'] >= daily_limit:
                return False
            
            # 更新记录
            cursor.execute(
                "UPDATE message_points_records SET points_earned = points_earned + %s, "
                "message_count = message_count + 1 WHERE group_id = %s AND user_id = %s AND message_date = CURDATE()",
                (points, group_id, user_id)
            )
        else:
            # 创建新记录
            cursor.execute(
                "INSERT INTO message_points_records (group_id, user_id, message_date, points_earned, message_count) "
                "VALUES (%s, %s, CURDATE(), %s, 1)",
                (group_id, user_id, points)
            )
        
        # 增加用户积分
        add_user_points(group_id, user_id, points, "发言奖励")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"记录发言积分失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# 邀请积分相关操作
def record_invite_points(group_id, inviter_id, invitee_id, points):
    """记录邀请积分"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        # 检查是否已记录过该邀请
        cursor.execute(
            "SELECT 1 FROM invite_points_records WHERE group_id = %s AND inviter_id = %s AND invitee_id = %s",
            (group_id, inviter_id, invitee_id)
        )
        already_recorded = cursor.fetchone()
        
        if already_recorded:
            return False
        
        # 获取每日上限
        cursor.execute(
            "SELECT daily_invite_limit FROM points_configs WHERE group_id = %s",
            (group_id,)
        )
        config = cursor.fetchone()
        daily_limit = config['daily_invite_limit'] if config else 0
        
        # 检查今日邀请数量是否达到上限
        if daily_limit > 0:
            cursor.execute(
                "SELECT COUNT(*) as invite_count FROM invite_points_records "
                "WHERE group_id = %s AND inviter_id = %s AND invite_date = CURDATE()",
                (group_id, inviter_id)
            )
            today_count = cursor.fetchone()
            if today_count and today_count['invite_count'] >= daily_limit:
                return False
        
        # 记录邀请
        cursor.execute(
            "INSERT INTO invite_points_records (group_id, inviter_id, invitee_id, invite_date, points_earned) "
            "VALUES (%s, %s, %s, CURDATE(), %s)",
            (group_id, inviter_id, invitee_id, points)
        )
        
        # 增加用户积分
        add_user_points(group_id, inviter_id, points, "邀请新成员")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        logger.error(f"记录邀请积分失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close() 