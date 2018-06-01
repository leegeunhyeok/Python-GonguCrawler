import os
import configparser

path = "../../conf/config.cfg"
config = configparser.ConfigParser()
config_data = {}

# 데이터베이스 설정 정보 불러오기
def get_database_conf():
    db_info = {}
    db_info["HOST"] = config.get("DATABASE_INFO", "host")
    db_info["PORT"] = config.getint("DATABASE_INFO", "port")
    db_info["USER"] = config.get("DATABASE_INFO", "user")
    db_info["PASSWORD"] = config.get("DATABASE_INFO", "password")
    db_info["DATABASE"] = config.get("DATABASE_INFO", "database")
    config_data["DATABASE"] = db_info

# 프로세스 설정 정보 불러오기
def get_process_conf():
    config_data["PROCESS"] = config.getint("PROCESS_INFO", "count")

# 이미지 로컬 저장 여부
def get_image_conf():
    image_info = {}
    image_info["ORIGIN"] = config.getboolean("CREATE_IMAGE", "create_origin_image")
    image_info["THUMBNAIL"] = config.getboolean("CREATE_IMAGE", "create_thumbnail_image")
    image_info["LICENSE"] = config.getboolean("CREATE_IMAGE", "create_license_image")
    config_data["IMAGE"] = image_info

# 자동 데이터 삭제 여부 불러오기
def get_auto_reset_conf():
    config_data["AUTO_RESET"] = config.getboolean("AUTO_RESET", "auto")

# 자동 크롤링 정보 불러오기
def get_auto_crawling_conf():
    config_data["AUTO_CRAWLING"] = config.getboolean("AUTO_CRAWLING", "auto")

# 크롤링 대기시간 정보 불러오기
def get_sleep_info_conf():
    sleep_info = {}
    sleep_info["COUNT"] = config.getint("SLEEP_INFO", "count")
    sleep_info["TIME"] = config.getint("SLEEP_INFO", "time")
    config_data["SLEEP_INFO"] = sleep_info

# 데이터 불러온 후 반환
def read():
    if os.path.exists(path):
        config.read(path, encoding="utf-8")
        get_database_conf()
        get_process_conf()
        get_image_conf()
        get_auto_reset_conf()
        get_auto_crawling_conf()
        get_sleep_info_conf()
    else:
        print(path, "설정파일이 존재하지 않습니다.")
    return config_data
