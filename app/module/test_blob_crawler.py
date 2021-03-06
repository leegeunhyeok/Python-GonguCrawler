# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from PIL import Image
import urllib.request
import pymysql
import os
import re
import time
import multiprocessing
import shutil
import sys
import base64
import zlib
import io

# 설정파일 관련 모듈 Import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), './common'))
import config_reader

class Crawler:
	# DB 커넥션
	conn = None

	# DB 커서
	cur = None

	# 이미지 파일 경로
	image_path = "../../img"

	# 라이선스 이미지 경로
	license_path = "../../img/license/"

	# 원본 이미지 경로
	origin_path = "../../img/origin/"

	# 썸네일 이미지 경로
	thumbnail_path = "../../img/thumbnail/"

	# 로그 파일 경로
	log_path = "../../log/"

	def __init__(self):
		# 설정 파일 불러오기
		self.config = config_reader.read()

		# 필요 디렉토리 존재 여부
		# 없을 경우 새로 생성
		if not os.path.exists(self.image_path):
			os.mkdir(self.image_path)
    
		if not os.path.exists(self.license_path):
			os.mkdir(self.license_path)

		if not os.path.exists(self.origin_path):
			os.mkdir(self.origin_path)

		if not os.path.exists(self.thumbnail_path):
			os.mkdir(self.thumbnail_path) 

		if not os.path.exists(self.log_path):
			os.mkdir(self.log_path)


	# 해당 페이지의 저작물 링크 추출
	# @param: 저작물 리스트 페이지 URL
	# @return: 추출된 링크 리스트
	def get_links(self, url):
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
			self.save_log("PAGE_URL_ERROR : {}".format(str(e) + "/" + url))
			return []

	# 마지막 페이지 추출
	# @return 마지막 페이지
	def get_max_page(self):
		url = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrt.do?menuNo=200023&wrtTy=4&depth2At=Y&pageIndex=1"
		html = urllib.request.urlopen(url)
		source = html.read()
		soup = BeautifulSoup(source, "html.parser")
		last_btn = soup.find(class_="end")
		href = last_btn.find("a").get("href")
		max = re.search("[0-9]{1,10}$", href).group()
		return int(max)

	# 저작물 링크의 저작물을 크롤링
	# work: 진행해야할 페이지 리스트(multiprocess.Array)
	# idx: 페이지 리스트의 인덱스(multiprocess.Value)
	# lock: 프로세스간 동기화를 위해 Lock 사용
	def get_item_data(self, work, idx, lock):
		conn = self.create_connection()
		cur = conn.cursor()


		# 저작물 리스트 기본 URL
		base_list_url = "https://gongu.copyright.or.kr/gongu/wrt/wrtCl/listWrt.do?menuNo=200023&wrtTy=4&depth2At=Y&pageIndex="
		
		# 프로세스 명
		process_name = multiprocessing.current_process().name

		# 크롤링 진행한 저작물 수
		count = 0

		# 일단 무한 반복
		while True: 
			page = 0 # 현재 페이지(예외 발생을 방지하기 위해 기본값 0으로 선언)
			lock.acquire() # 동기화를 위해 사용하는동안 잠시 락 
			try:
				i = idx.value # 인덱스 가져오기
				page = work[i] # 가져온 인덱스 값으로 리스트에서 페이지 가져오기
				idx.value = i + 1 # 인덱스 1 증가
			except IndexError as e: 
				# work(리스트)의 인덱스 초과시 반복 종료(작업 모두 마침)
				break
			except Exception as e:
				# 알 수 없는 오류 핸들링
				print(e)
			finally:
				lock.release() # 값 추출 및 수정 후 락 해제 
			
			# 추출된 페이지의 저작물 링크들을 대상으로 크롤링 시도
			for href in	self.get_links(base_list_url + str(page)):
				self.get_item_info(href, conn, cur)
				print("[{}] {}페이지 '{}'".format(process_name, page, href))

			count += 1

			# COUNT 페이지마다 TIME만큼 대기
			if count % self.config["SLEEP_INFO"]["COUNT"] == 0:
				time.sleep(self.config["SLEEP_INFO"]["TIME"])

		cur.close()
		conn.close()
		print("[{}] 크롤링 종료".format(process_name))

	# 저작물 이미지, 상세정보 크롤링 후 저장
	# 썸네일 이미지 생성
	# @param: 저작물 주소
	def get_item_info(self, href, conn, cur):
		# 기본 URL
		base_url = "https://gongu.copyright.or.kr"

		# 기본 URL + 받은 URL
		url = base_url + href

		# 저작물 ID 가져오기
		_id = self.getCode(url)

		# 에러 핸들링, (SQL, HTML 속성, 기타 오류)
		try:
			source = urllib.request.urlopen(url, timeout=5).read()
			soup = BeautifulSoup(source, "html.parser")

            # 저작물 이미지 src
			img_src = soup.find(class_="imgD").find("img").get("src")

            # 이미지 명
			img_name = soup.find(class_="tit_txt3").text

            # 라이선스 영역
			copy = soup.find(class_="copyD")

            # 라이선스 이미지 src
			copy_src = copy.find("img").get("src")

            # 라이선스 유형 텍스트
			copy_text = copy.text.replace("\n", "").replace("\r", "").replace("\t", "").strip()

            # 라이선스 이미지 명
			copy_file = copy_src.split("/")[-1]

			# 라이선스 이미지 받기
			copy_data = urllib.request.urlopen(base_url + copy_src).read()

			try:
				# 라이선스 이미지 해시값 저장
				cur.execute("INSERT INTO license VALUES (%s, %s, %s)", (copy_file, copy_text, copy_data))
				conn.commit()
			except pymysql.err.IntegrityError as e:
				# PK 중복 오류
				pass
			except:
				print(e)
				self.save_log("LICENSE IMAGE ERROR: {}".format(copy_file))

			if self.config["IMAGE"]["LICENSE"] and not self.duplicateCheck(copy_file, self.license_path):
				with open(self.license_path + copy_file, "wb") as license:
					license.write(copy_data)

			# 상세정보 파싱
			table = soup.find(class_="tb_bbs").find_all("tr")

			# DB 속성 (a, b, c, ...)
			attr = "(_id,filename,path,license,license_name,"

			# DB 값 (v1, v2, v3, ...)
			attrValue = '("{}","{}","{}","{}","{}",'.format(_id, img_name, self.origin_path + _id + ".png", copy_file, copy_text)

			# 컬럼 수
			cols = 0
			for info in table:

                # 상세정보 제목
				title = info.find("th").text.replace("\\s", "")  

				try:
                    # DB 컬럼명 추가
					attr += self.attrQuery(title) + ","  
					value = ""

					if (title == u"저작자"):
                        # 저작자가 이름
						authors = info.find("td").find_all("a") 

                        # 저작자가 여러명인 경우 , 문자로 구분
						for author in authors:
							value += author.text + "," 
					else:
                        # 저작자를 제외한 나머지 상세정보
						value = info.find("td").text

					value = value.strip()  # 양쪽 불필요한 공백 제거

					# DB 저장할 값 추가
					attrValue += '"{}",'.format(value.replace("\n", "").replace("\r", "").replace("\t", "").replace("\"", ""))
					cols += 1
				except RuntimeError as e:
					print("Runtime Error:", e)
					self.save_log("{} : {}".format(_id, str(e)))  # 로그에 저장

			file_name = _id + ".png"  # 원본 이미지 파일명

			# 원본 이미지 가져오기
			origin_image = urllib.request.urlopen(base_url + img_src).read()

			# 인코딩 데이터 저장
			cur.execute("INSERT INTO image VALUES (%s, %s, %s)", (_id, file_name, origin_image))
			conn.commit()

			# 설정의 원본 이미지 생성 여부가 True인 경우 이미지 생성(이미 존재할 경우 건너뜀)
			if self.config["IMAGE"]["ORIGIN"]:
				if not self.duplicateCheck(file_name, self.origin_path):
					with open(self.origin_path + file_name, "wb") as origin:
						origin.write(origin_image)
				else:
					print("> 이미 존재하는 이미지:", file_name)
			
			# 썸네일 이미지 생성 및 저장
			self.create_thumbnail(origin_image, _id, file_name, conn, cur)

			# 맨 뒤에 컬럼 수 데이터 추가
			attr += "col_size)"
			attrValue += "{})".format(cols)

			# DB 쿼리
			query = "INSERT INTO crawler {} VALUES {}".format(attr, attrValue)
			cur.execute(query)
			conn.commit()
		except AttributeError as e:  # 속성 오류
			pass
		except pymysql.err.IntegrityError as e:  # 중복, SQL 오류
			pass
		except Exception as e:
			self.save_log("{} : {}".format(_id, str(e)))  # 기타 예외사항은 로그에 기록
        

	# 게시글 URL의 wrtSn값 추출
	# @param: 게시글 URL
	# @return: 게시글 번호
	def getCode(self, url):
		try:
			m = str(re.search(r"wrtSn=\d{4,16}", url).group())
			return re.sub("[^0-9]", "", m)
		except Exception as e:
			print("게시글 번호 추출 오류:", e)
			return "error"

	# 파일 중복 체크
	# @param: 파일 명
	# @param: 디렉토리
	# @return: 중복 여부
	def duplicateCheck(self, name, dir):
		return os.path.exists(dir + name)

	# 저작물 상세정보 항목으로 DB 컬럼 조회
	# @param: 저작물 상세정보 항목
	# @return: 컬럼 명
	def attrQuery(self, title):
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

	# 해당 이미지의 썸네일 생성
	# @param: 이미지 명
	# @param: DB 커넥션
	# @param: DB 커서
	def create_thumbnail(self, origin, _id, file_name, conn, cur):
		try:
			# 원본 이미지 데이터 스트림에 보관
			origin = io.BytesIO(origin)

			# 썸네일 데이터를 저장할 다른 스트림
			thumbnail = io.BytesIO()

			# 원본 이미지 데이터가 있는 스트림 열기
			img = Image.open(origin)

			# RGB 모드가 아닐 경우 RGB 모드로 변환
			if img.mode != "RGB":
				img = img.convert("RGB")

			img.thumbnail((200, 200))
			img.save(thumbnail, format="PNG")

			# 썸네일 이미지 저장(해시값 및 이미지)
			if self.config["IMAGE"]["THUMBNAIL"]:
				if not self.duplicateCheck(file_name, self.thumbnail_path):
					img.save(file_name)
				else:
					print("> 이미 존재하는 썸네일 이미지:", file_name)

			# DB에 해시값 저장
			cur.execute("INSERT INTO thumbnail VALUES (%s, %s, %s)", (_id, file_name, thumbnail.getvalue()))
			conn.commit()

			img.close()
			origin.close()
			thumbnail.close()

		except Exception as e:
			print(e)
			self.save_log("THUMBNAIL ERROR: {}".format(file_name))

	# 해당 저작물 ID와 에러 메시지 로그에 저장
	# @param 저장할 메시지
	def save_log(self, msg):
		try:
			with open(self.log_path + self.start_time + ".log", "a", encoding="utf-8") as log:
				log.write(msg + "\n")
		except:
			print("> 로그를 저장하지 못했습니다.")

	# 저장된 로그를 읽어서 저작물 ID만 추출하여 반환
	# @return 저작물 ID 리스트
	def error_list(self):
		f = open(self.log_path + self.start_time + ".log", "r", encoding="utf-8")

		# 한 줄씩 파일 읽기 
		lines = f.readlines()
		urls = []
		for line in lines:
			# 앞 문자가 > 이면 건너뛰기
			if line[0] == ">":
				continue

			# 정규표현식으로 저작물 부분만 추출
			temp = re.search("^[0-9]{1,10}", line)
			if temp:
				urls.append("/gongu/wrt/wrt/view.do?wrtSn={}&menuNo=200023".format(temp.group()))

		return urls

	# 크롤링 시작 함수
	def start(self):
		# 프로세스 객체 저장 리스트
		process = [] 

		# 로그 파일 명(크롤러 실행 시간)
		self.start_time = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
		print("> 크롤러 실행: {}".format(self.start_time))

		# 시작 페이지
		start_page = 1
		
		# 프로세스 수
		process_count = self.config["PROCESS"]

		if self.config["AUTO_CRAWLING"]:
			# 전체 페이지 수
			max_page = self.get_max_page()
		else:
			max_page = int(input("> 크롤링 페이지를 입력해주세요: "))
		
		print("> {} ~ {} 페이지 까지 크롤링을 진행합니다.".format(start_page, max_page))


		if self.config["AUTO_RESET"]:
			print("> 설정에 의해 기존 데이터 초기화 하는 중..")
			self.data_reset()
			print("> 초기화 완료")
		else:
			if str(input("> 기존 데이터를 초기화하시겠습니까(y/n)?: ")).lower() == "y":
				print("> 초기화 진행 중..")
				self.data_reset()
				print("> 초기화 완료")
			else:
				print("> 초기화를 진행하지 않았습니다.")

		# 크롤링 시작 정보 로그에 저장
		with open(self.log_path + self.start_time + ".log", "w") as log:
			log.write("> Run at: {}\n".format(self.start_time))
			log.write(">-- CONFIG --<\n")
			log.write("> PROCESS_COUNT={}\n".format(self.config["PROCESS"]))
			log.write("> SAVE_ORIGIN_IMAGE={}\n".format(self.config["IMAGE"]["ORIGIN"]))
			log.write("> SAVE_THUMBNAIL_IMAGE={}\n".format(self.config["IMAGE"]["THUMBNAIL"]))
			log.write("> SAVE_LICENSE_IMAGE={}\n".format(self.config["IMAGE"]["LICENSE"]))
			log.write("> AUTO_RESET={}\n".format(self.config["AUTO_RESET"]))
			log.write("> AUTO_CRAWLING={}\n".format(self.config["AUTO_CRAWLING"]))
			log.write("> SLEEP: {} Pages, {} sec\n".format(self.config["SLEEP_INFO"]["COUNT"], self.config["SLEEP_INFO"]["TIME"]))
			log.write(">------------<\n\n")
			log.write("> Progress: {} ~ {} page(s)\n\n".format(start_page, max_page))

		# 프로세스간 메모리 동기화를 위해 사용
		lock = multiprocessing.Lock()

		# 시작페이지 ~ 마지막 페이지까지의 리스트 생성
		work = multiprocessing.Array("i", range(start_page, max_page+1)) 
		
		# work 리스트의 인덱스 변수
		index = multiprocessing.Value("i", 0)

		print("> {} ~ {} 페이지 크롤링 시작".format(start_page, max_page))
		
		# 시작 시간
		start_time = time.time()

		# 프로세스 수 만큼 프로세스 생성
		for i in range(process_count):
			p = multiprocessing.Process(target=self.get_item_data, args=(work, index, lock))
			p.daemon = True
			p.start()  # 프로세스 시작
			print("> {}번 프로세스 시작".format(i))
			process.append(p)

		for p in process:
			p.join()  # 프로세스 종료 대기
		
		progress_time = round(time.time() - start_time, 3)

		self.save_log("\n> Total progress time: {} sec\n".format(progress_time))

		print("> 전체 크롤링 소요시간: {} 초".format(progress_time))

		# 재시도 시작  시간
		start_time = time.time()
		if input(self.start_time + ".log 파일을 불러오겠습니까? (y/n)") == "n":
			self.start_time = input("로그파일명을 직접 입력해주세요 (.log 제외): ")
		try:
			self.save_log("\n\n\n> Trying error image crawling: {} sec\n".format(progress_time))
			print("\n\n> 문제 발생 저작물 크롤링 재시도")
			conn = self.create_connection()
			cur = conn.cursor()

			for err in self.error_list():
				print(err)
				self.get_item_info(err, conn, cur)

			cur.close()
			conn.close()
		except:
			pass
		finally:
			end_time = round(time.time() - start_time, 3)
			self.save_log("\n> END: {} sec\n".format(end_time))
			print("> 문제 발생 저작물 크롤링 종료")
			print("> 소요시간: {} 초".format(end_time))


	# DB 커넥션 생성 함수
	# config 데이터를 읽고 해당 정보로 접속
	def create_connection(self):
		host = self.config["DATABASE"]["HOST"]
		port = self.config["DATABASE"]["PORT"]
		user = self.config["DATABASE"]["USER"]
		password = self.config["DATABASE"]["PASSWORD"]
		db = self.config["DATABASE"]["DATABASE"]

		return pymysql.connect(host=host, port=port, user=user, password=password, db=db, charset="utf8", connect_timeout=5, write_timeout=5, read_timeout=5)

	# 저장된 이미지 및 DB 데이터 초기화
	def data_reset(self):
		try:
			conn = self.create_connection()
			cur = conn.cursor()

			cur.execute("DELETE FROM crawler")
			cur.execute("DELETE FROM image")
			cur.execute("DELETE FROM thumbnail")
			cur.execute("DELETE FROM license")
			conn.commit()

			cur.close()
			conn.close()
		except Exception as e:
			print(e)

		try:
			shutil.rmtree(self.thumbnail_path)
			shutil.rmtree(self.origin_path)
			shutil.rmtree(self.license_path)
		except Exception as e:
			print(e)

		os.mkdir(self.thumbnail_path)
		os.mkdir(self.origin_path)
		os.mkdir(self.license_path)


if __name__ == "__main__":
	crawler = Crawler()
	crawler.start()
