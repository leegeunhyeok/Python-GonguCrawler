import os
import configparser

path = "../../conf/config.cfg"
config = configparser.ConfigParser()
config_data = {}

# 데이터베이스 설정 정보 불러오기
def get_database_conf():
    db_info = {}
    db_info["host"] = config.get("DATABASE_INFO", "host")
    db_info["port"] = config.getint("DATABASE_INFO", "port")
    db_info["user"] = config.get("DATABASE_INFO", "user")
    db_info["password"] = config.get("DATABASE_INFO", "password")
    db_info["database"] = config.get("DATABASE_INFO", "database")
    config_data["database"] = db_info

# 썸네일 생성 여부 불러오기
def get_thumb_info():
    config_data["THUMBNAIL"] = config.getboolean("CREATE_THUMB_INFO", "create")

# 자동 데이터 삭제 여부 불러오기
def get_auto_reset():
    config_data["AUTO_RESET"] = config.getboolean("AUTO_RESET", "auto")

# 크롤링 대기시간 정보 불러오기
def get_sleep_info():
    sleep_info = {}
    sleep_info["COUNT"] = config.getint("SLEEP_INFO", "count")
    sleep_info["TIME"] = config.getint("SLEEP_INFO", "time")
    config_data["SLEEP_INFO"] = sleep_info

# 데이터 불러온 후 반환
def read():
    if os.path.exists(path):
        config.read(path, encoding="utf-8")
        get_database_conf()
        get_thumb_info()
        get_auto_reset()
        get_sleep_info()
    else:
        print(path, "설정파일이 존재하지 않습니다.")
    return config_data
