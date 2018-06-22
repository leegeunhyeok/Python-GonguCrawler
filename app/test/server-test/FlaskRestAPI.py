# REST API 서버 테스트
# 모든 응답 데이터는 JSON으로 변환하여 전달

import base64
import pymysql
from flask import Flask, request, render_template, json, send_file
app = Flask (__name__)

# DB 커넥션 생성
conn = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="python", charset="utf8", connect_timeout=5, write_timeout=5, read_timeout=5)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# GET /
@app.route('/',methods=['GET'])
def index(): 
    return render_template("./index.html")

# GET /info/DataCount
@app.route('/info/DataCount', methods=['GET'])
def data_count():
    # 저장된 데이터 수
    cursor.execute("SELECT count(*) AS count FROM crawler")
    result = cursor.fetchone()
    return json.dumps({"count": result["count"]})

# GET /info/ConfigInfo
@app.route('/info/ConfigInfo', methods=['GET'])
def config_info(): 
    # 설정정보 (임시 데이터)
    return json.dumps({"process": 8, "create_origin": True, "create_thumbnail": False, "create_license": True, "auto_reset": False, "auto_crawling": False, "sleep_count": 10, "sleep_time": 1})

# GET /info/ResorceSize
@app.route('/info/ResorceSize', methods=['GET'])
def resorce_size():
    # 지정 테이블의 용량
    query = """SELECT 
    table_name,
    table_rows,
    round(data_length/(1024*1024),2) as 'size',
    round(index_length/(1024*1024),2) as 'INDEX_SIZE(MB)'
    FROM information_schema.TABLES
    where table_schema = 'python'
    GROUP BY table_name 
    ORDER BY data_length DESC;"""
    cursor.execute(query)
    result = cursor.fetchall()
    send_data = {}
    for r in result:
        if r["table_name"] == "image":
            send_data["origin"] = str(r["size"])
        elif r["table_name"] == "thumbnail":
            send_data["thumbnail"] = str(r["size"])
        elif r["table_name"] == "license":
            send_data["license"] = str(r["size"])
        elif r["table_name"] == "crawler":
            send_data["info"] = str(r["size"])
    print(send_data)
    return json.dumps(send_data)

# GET /data
@app.route('/data', methods=['GET'])
def get_data_all(): 
    return json.dumps({"result": "전체 데이터 GET"})

# GET /image
@app.route('/image', methods=['GET'])
def get_image(): 
    return send_file("./1.png", mimetype="image/png")

# DELETE /data
@app.route('/data', methods=['DELETE'])
def del_data_all(): 
    return json.dumps({"result": "전체 데이터 DELETE"})

# GET /data/:id
@app.route('/data/<id>', methods=['GET'])
def get_data(id):
    cursor.execute("SELECT _id AS id, image AS hash FROM image WHERE _id={}".format(id))
    result = cursor.fetchone()

    # 조회 결과가 없을 경우 빈 객체 리턴
    if result is None:
        return json.dumps({})

    # base64로 인코딩한 후 응답 (또한, Bytes 타입에서 String 타입으로 변환)
    result["hash"] = str(base64.b64encode(result["hash"]))[2:-1]

    # 상세정보 SELECT
    cursor.execute("SELECT * FROM crawler WHERE _id={}".format(id))
    result2 = cursor.fetchone()
    result["info"] = result2
    return json.dumps(result)

# DELETE /data/:id
@app.route('/data/<id>', methods=['DELETE'])
def del_data(id):
    image_del = cursor.execute("DELETE FROM image WHERE _id={}".format(id))
    info_del = cursor.execute("DELETE FROM crawler WHERE _id={}".format(id))
    # conn.commit() #삭제 작업 커밋

    deleted = False
    if image_del != 0 and info_del != 0:
        deleted = True

    return json.dumps({"id": id, "deleted": deleted})

if __name__ == "__main__":
    app.run(debug=True)