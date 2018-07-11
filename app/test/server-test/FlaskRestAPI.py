# REST API 서버 테스트
# 모든 응답 데이터는 JSON으로 변환하여 전달

import base64
import pymysql
from flask import Flask, request, render_template, json

app = Flask (__name__)

import time

# DB 커넥션 생성
def get_connection():
    return pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="python", charset="utf8", connect_timeout=5, write_timeout=5)

# GET /
@app.route('/', methods=['GET'])
def index(): 
    return render_template("./index.html")

# GET /info/datacount
@app.route('/info/datacount', methods=['GET'])
def data_count():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    # 저장된 데이터 수
    cursor.execute("SELECT count(*) AS count FROM crawler")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return json.dumps({"count": result["count"]})

# GET /info/setting
@app.route('/info/setting', methods=['GET'])
def config_info(): 
    # 설정정보 (임시 데이터)
    return json.dumps({"process": 8, "create_origin": True, "create_thumbnail": False, "create_license": True, "auto_reset": False, "auto_crawling": False, "sleep_count": 10, "sleep_time": 1})

# GET /info/datarange
@app.route('/info/datarange', methods=['GET'])
def get_data_all():
    result = []
    start = request.args.get("start")
    count = request.args.get("count")
    if start and count: 
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        start_time = time.time() 
        cursor.execute("""
            SELECT image._id AS id, image.hash_ AS hash 
            FROM (SELECT _id FROM image LIMIT {}, {}) t 
            JOIN image
            ON image._id = t._id
            """.format(start, count))
        result_image = cursor.fetchall()
        print(time.time() - start_time)
        for image in result_image:
            temp = image
            temp["hash"] = str(base64.b64encode(temp["hash"]))[2:-1]
            cursor.execute("SELECT * FROM crawler WHERE _id=%s", (image["id"], ))
            result_info = cursor.fetchone()
            temp["info"] = result_info
            result.append(temp)
        cursor.close()
        conn.close()
        return json.dumps({"list": result})
    else:
        return json.dumps({"list": []})

# GET /info/original
@app.route('/info/original', methods=['GET'])
def get_image():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT * FROM crawler WHERE _id=" + request.args.get("id")
    result = cursor.execute(query)
    info = cursor.fetchone()
    cursor.close()
    conn.close()
    if result is 0:
        return json.dumps({})
    return json.dumps(info)

# GET /info/hash/original
@app.route('/info/hash/original', methods=['GET'])
def get_image_hash():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    result = cursor.execute("SELECT _id AS id, filename, hash_ AS hashimg FROM image WHERE _id=%s", (request.args.get("id"), ))
    hash_data = cursor.fetchone()
    hash_data["hashimg"] = str(base64.b64encode(hash_data["hashimg"]))[2:-1]
    cursor.close()
    conn.close()
    if result is 0:
        return json.dumps({})
    return json.dumps(hash_data)

# GET /info/license
@app.route('/info/license', methods=['GET'])
def get_license():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    result = cursor.execute("SELECT license_name AS licensename, license AS filename FROM crawler WHERE _id=%s", (request.args.get("id")))
    
    license_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if result is 0:
        return json.dumps({})
    return json.dumps(license_data)
    
# GET /info/hash/license
@app.route('/info/hash/license', methods=['GET'])
def get_license_hash():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    result = cursor.execute("""
    SELECT l.license AS id, l.license_name AS license_name, l.hash_ AS hashlicense 
    FROM license l, crawler c WHERE l.license=c.license AND c._id=%s
    """, (request.args.get("id")))

    license_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if result is 0:
        return json.dumps({})

    license_data["hashlicense"] = str(base64.b64encode(license_data["hashlicense"]))[2:-1]
    return json.dumps(license_data)

# GET /info/hash/thumbnail
@app.route('/info/hash/thumbnail', methods=['GET'])
def get_thumbnail_hash():
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    result = cursor.execute("SELECT _id AS id, filename, hash_ AS hashthumbnail FROM thumbnail WHERE _id=%s", (request.args.get("id")))

    thumbnail_data = cursor.fetchone()
    if not thumbnail_data:
        return json.dumps({})

    cursor.close()
    conn.close()

    thumbnail_data["hashthumbnail"] = str(base64.b64encode(thumbnail_data["hashthumbnail"]))[2:-1]
    return json.dumps(thumbnail_data)

# DELETE /delete/image
@app.route('/delete/image', methods=['DELETE'])
def del_data_all(): 
    return json.dumps({"result": "데이터 DELETE"})

if __name__ == "__main__":
    app.run(debug=True)
    conn.close()