# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from PIL import Image
import urllib.request
import pymysql
import os
import re
import time  # 시간
import multiprocessing
import shutil

conn = pymysql.connect(host="localhost", user="root", password="1234", db="python", charset="utf8", connect_timeout=5, write_timeout=5, read_timeout=5)
cur = conn.cursor()

# 저작물 링크 추출
def get_links(url):
    try:
        html = urllib.request.urlopen(url)
        source = html.read()
        soup = BeautifulSoup(source, "html.parser")
        list = soup.find(id="wrtList")  # 아이템(저작물) 목록
        items = list.find_all("li")  # 아이템(저작물)
        url_list = []
        for item in items:
            url_list.append(item.find("a").get("href"))
        return url_list
    except Exception as e:
        save_log("url", str(e) + "/" + url)
        return []

# 공유마당의 마지막 페이지 추출
def get_max_page():
    url = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrt.do?menuNo=200023&wrtTy=4&depth2At=Y&pageIndex=1"
    html = urllib.request.urlopen(url)
    source = html.read()
    soup = BeautifulSoup(source, "html.parser")
    last_btn = soup.find(class_="end")
    href = last_btn.find("a").get("href")
    max = re.search("[0-9]{1,10}$", href).group()
    print("게시글 마지막 페이지:", max)
    return int(max)


# 저작물의 이미지, 라이선스, 상세정보 파싱
# 공유마당 기본 URL, 상세정보 URL
def get_item_data(work):
    base_list_url = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrt.do?menuNo=200023&wrtTy=4&depth2At=Y&pageIndex="
    page = work[0] # 시작페이지
    max = page + work[1] # ~ 종료페이지
    count = 0 # 현재 진행한 페이지 수
    max_count = work[1] # 마지막 페이지

    process_name = multiprocessing.current_process().name
    while page < max:
        for href in get_links(base_list_url + str(page)):
            get_item_info(href)
            per = round(count / max_count * 100, 3)
            print("{}: [{:<20}] {}% ({}/{})".format(process_name, "=" * int(per / 5), per, count, max_count))
        count += 1
        page += 1
        if count % 20 == 0:
            time.sleep(1) # 20페이지(저작물 180개)마다 1초 대기
    print("{}: [{:<20}] {}% ({}/{})".format(process_name, "=" * 20, 100.0, max_count, max_count))

def get_item_info(href):
    base_url = "https://gongu.copyright.or.kr"
    url = base_url + href
    _id = getCode(url)
    # 에러 핸들링, (SQL, HTML 속성, 기타 오류)
    try:
        source = urllib.request.urlopen(url, timeout=5).read()
        soup = BeautifulSoup(source, "html.parser")

        img_src = soup.find(class_="imgD").find("img").get("src")  # 저작물 이미지 src
        img_name = soup.find(class_="tit_txt3").text  # 이미지 명
        copy = soup.find(class_="copyD")
        copy_src = copy.find("img").get("src")  # 라이선스 이미지 src
        copy_text = copy.text.replace("\n", "").replace("\r", "").replace("\t", "").strip()
        copy_name = copy_src.split("/")[-1]  # 라이선스 이미지 명

        # 라이선스 파일이 없을 때 다운로드 및 저장
        if (not duplicateCheck(copy_name, 1)):
            urllib.request.urlretrieve(base_url + copy_src, "./license/" + copy_name)
            # print("새 라이선스 이미지 다운로드:", copy_name)

        # 상세정보 파싱
        table = soup.find(class_="tb_bbs").find_all("tr")

        # DB 속성 (a, b, c, ...)
        attr = "(_id,filename,path,license,license_name,"

        # DB 값 (v1, v2, v3, ...)
        attrValue = "(\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"," % (
        _id, img_name, "./img/" + _id + ".png", copy_name, copy_text)

        # 컬럼 수
        cols = 0
        for info in table:
            title = info.find("th").text.replace("\\s", "")  # 상세정보 제목
            try:
                attr += attrQuery(title) + ","  # DB 컬럼명 추가
                value = ""
                if (title == u"저작자"):
                    authors = info.find("td").find_all("a")  # 저작자가 여러명인 경우
                    for author in authors:
                        value += author.text + ","  # 저작자가 여러명인 경우 , 문자로 구분
                else:
                    value = info.find("td").text

                value = value.strip()  # 양쪽 불필요한 공백 제거

                # DB 저장할 값 추가
                attrValue += "\"%s\"," % value.replace("\n", "").replace("\r", "").replace("\t", "").replace("\"", "")
                cols += 1
            except RuntimeError as e:
                print("Runtime Error:", e)
                save_log(_id, str(e))  # 로그에 저장

        file_name = _id + ".png"  # 저장 파일명

        # 파일이 존재하지 않는 경우에만 다운로드
        if not duplicateCheck(file_name):
            urllib.request.urlretrieve(base_url + img_src, "./img/" + file_name)
        else:
            print("이미 존재하는 이미지:", file_name)

        # 썸네일 이미지가 없는 경우에만 생성
        if not duplicateCheck(file_name, 2):
            gen_thumbnail(file_name)
        else:
            print("이미 존재하는 썸네일 이미지:", file_name)

        # 맨 뒤에 컬럼 수 데이터 추가
        attr += "col_size)"
        attrValue += "%d)" % cols

        # DB 쿼리
        query = "INSERT INTO crawler %s VALUES %s" % (attr, attrValue)
        cur.execute(query)
        conn.commit()
    except AttributeError as e:  # 속성 오류
        pass
    except pymysql.err.IntegrityError as e:  # 중복, SQL 오류
        pass
    except Exception as e:
        save_log(_id, str(e))  # 기타 예외사항은 로그에 기록


# 게시글 URL에서 wrtSn의 값만 추출
def getCode(url):
    try:
        m = str(re.search(r"wrtSn=\d{4,16}", url).group())
        return re.sub("[^0-9]", "", m)
    except Exception as e:
        print("게시글 번호 추출 오류:", e)
        return "error"


# 중복체크, 파일 존재 유무 (0: 이미지, 1: 라이선스 이미지, 2: 썸네일 이미지)
def duplicateCheck(name, type=0):
    if type == 0:
        path = "./img/"
    elif type == 1:
        path = "./license/"
    elif type == 2:
        path = "./thumbnail/"
    else:
        path = "./img/"
    return os.path.exists(path + name)


# 항목 타이틀로 DB 컬럼 찾기
def attrQuery(title):
    title = title.replace(" ", "")
    if title == u"UCI":
        return "uci"
    elif title == u"ICN":
        return "icn"
    elif title == u"저작자":
        return "author"
    elif title == u"공동저작자":
        return "public_author"
    elif title == u"공표일자(년도)":
        return "publicate_date"
    elif title == u"창작일자(년도)":
        return "create_date"
    elif title == u"공표국가":
        return "publicate_contry"
    elif title == u"분류(장르)":
        return "classification"
    elif title == u"원문제공":
        return "original_text"
    elif title == u"요약정보":
        return "summary_info"
    elif title == u"관련태그":
        return "relation_tag"
    elif title == u"발행일자":
        return "publish_date"
    elif title == u"발행자":
        return "publisher"
    elif title == u"기여자":
        return "contributor"
    elif title == u"저작물명대체제목":
        return "alternate_title"
    elif title == u"저작물파일유형":
        return "substitute"
    elif title == u"저작물속성":
        return "attribute"
    elif title == u"수집연계유형":
        return "collect_type"
    elif title == u"수집연계대상명":
        return "collect_target"
    elif title == u"수집연계URL":
        return "collect_url"
    elif title == u"주언어":
        return "main_language"
    elif title == u"원저작물유형":
        return "original_type"
    elif title == u"원저작물창작일":
        return "original_date"
    elif title == u"원저작물크기":
        return "original_size"
    elif title == u"원저작물소장처":
        return "original_collection"
    elif title == "추가사항":
        return "details"
    else:
        raise RuntimeError("알 수 없는 상세정보")


# 썸네일 생성
def gen_thumbnail(src):
    img = Image.open("./img/" + src)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((200, 200))
    img.save("./thumbnail/" + src)


# 로그 저장
def save_log(msg, err=""):
    f = open("./log/crawler.log", "a", encoding="utf-8")
    f.write(msg + " : " + err + "\n")
    f.close()

def error_list():
    f = open("./log/crawler.log", "r", encoding="utf-8")
    lines = f.readlines()
    urls = []
    for line in lines:
        temp = re.search("^[0-9]{1,10}", line)
        if temp:
            urls.append("/gongu/wrt/wrt/view.do?wrtSn={}&menuNo=200023".format(temp.group()))
    return urls

# 크롤링할 페이지 수를 프로세스 수 만큼 분배
def get_count(max, p):
    i = int(max/p)
    start = 1
    list = []
    for n in range(p-1):
        list.append((start, i)) # 시작 페이지, 부터 몇 페이지 크롤링 할지
        start += i
    list.append((start, i + max%p))
    print(list)
    return list

def start():
    process = []
    #max_page = get_max_page() # 전체 페이지 수
    max_page = 1000
    process_count = 8  # 프로세스 수
    start_time = time.time()  # 시간 측정(시작)
    for work in get_count(max_page, process_count):
        p = multiprocessing.Process(target=get_item_data, args=(work,))
        p.daemon = True
        p.start()  # 프로세스 시작
        process.append(p)

    for p in process:
        p.join()  # 프로세스 종료 대기
    print("[ 전체 크롤링 소요시간: %s 초 ]" % (round(time.time() - start_time, 3)))

    try:
        print("\n\n== 문제 발생 저작물 크롤링 재시도 ==")
        for err in error_list():
            print(err)
            get_item_info(err)
    except:
        pass
    cur.close()
    conn.close()


def data_reset():
    print("== 데이터 초기화 중..")
    try:
        cur.execute("DELETE FROM crawler")
        conn.commit()
        shutil.rmtree('./thumbnail/')
        shutil.rmtree('./img/')
        shutil.rmtree('./license/')
        shutil.rmtree('./log/')
    except Exception as e:
        pass

    os.mkdir("thumbnail")
    os.mkdir("img")
    os.mkdir("license")
    os.mkdir("log")
    print("== 초기화 완료")

if __name__ == "__main__":
    reset = input("데이터를 초기화 하시려면 1 입력: ")
    if reset == "1":
        data_reset()
    start()
