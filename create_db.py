import pymysql

# 数据库连接信息
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_PORT = 3306
DB_NAME = 'tg_bot_db'

# 创建数据库连接
def create_connection():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            charset='utf8mb4'
        )
        print("数据库连接成功")
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

# 创建数据库和表
def setup_database():
    connection = create_connection()
    if connection:
        try:
            with connection.cursor() as cursor:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {DB_NAME} 创建成功或已存在")
                
                # 使用数据库
                cursor.execute(f"USE {DB_NAME}")
                
                # 创建群组表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_groups (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    group_id BIGINT NOT NULL,
                    group_name VARCHAR(255) NOT NULL,
                    join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    UNIQUE KEY (group_id)
                )
                """)
                print("表 bot_groups 创建成功或已存在")
                
            connection.commit()
            print("数据库初始化完成")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
        finally:
            connection.close()

if __name__ == "__main__":
    setup_database() 