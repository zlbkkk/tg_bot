import pymysql
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_PORT, DB_NAME

def create_database():
    """创建数据库（如果不存在）"""
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"数据库 {DB_NAME} 创建成功或已存在")
    except Exception as e:
        print(f"创建数据库时出错: {e}")
    finally:
        cursor.close()
        conn.close()

def create_tables():
    """创建所需的表"""
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database=DB_NAME
    )
    cursor = conn.cursor()
    
    try:
        # 创建群组配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_configs (
            group_id BIGINT PRIMARY KEY,
            group_name VARCHAR(255) DEFAULT '未命名群组',
            welcome_msg TEXT,
            language VARCHAR(10) DEFAULT 'zh',
            anti_spam BOOLEAN DEFAULT FALSE,
            auto_delete BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("群组配置表创建成功")
        
        # 创建积分系统配置表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS points_configs (
            group_id BIGINT PRIMARY KEY,
            points_enabled BOOLEAN DEFAULT FALSE,
            checkin_points INT DEFAULT 1,
            message_points INT DEFAULT 1,
            daily_message_limit INT DEFAULT 0,
            min_message_length INT DEFAULT 0,
            invite_points INT DEFAULT 1,
            daily_invite_limit INT DEFAULT 0,
            points_alias VARCHAR(50) DEFAULT '积分',
            ranking_alias VARCHAR(50) DEFAULT '积分排行',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("积分系统配置表创建成功")
        
        # 创建用户积分表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_points (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            user_id BIGINT,
            points INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY group_user (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("用户积分表创建成功")
        
        # 创建积分记录表（记录积分变动历史）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS points_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            user_id BIGINT,
            points_change INT NOT NULL,
            reason VARCHAR(255),
            admin_id BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("积分记录表创建成功")
        
        # 创建签到记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkin_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            user_id BIGINT,
            checkin_date DATE,
            points_earned INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY group_user_date (group_id, user_id, checkin_date),
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("签到记录表创建成功")
        
        # 创建发言积分记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_points_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            user_id BIGINT,
            message_date DATE,
            points_earned INT DEFAULT 0,
            message_count INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY group_user_date (group_id, user_id, message_date),
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("发言积分记录表创建成功")
        
        # 创建邀请积分记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_points_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            group_id BIGINT,
            inviter_id BIGINT,
            invitee_id BIGINT,
            invite_date DATE,
            points_earned INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY group_inviter_invitee (group_id, inviter_id, invitee_id),
            FOREIGN KEY (group_id) REFERENCES group_configs(group_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("邀请积分记录表创建成功")
        
        conn.commit()
        print("所有表创建成功")
    except Exception as e:
        conn.rollback()
        print(f"创建表时出错: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_database()
    create_tables()
    print("数据库设置完成") 