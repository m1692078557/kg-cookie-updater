import os
import time
from flask import Flask, request, render_template
import requests
import json
import pymysql
from kg_login import Login

app = Flask(__name__)

# 微信推送
class WeComtAlert():
    def __init__(self, corpid, corpsecret, agentid):
        self.url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        self.corpid = corpid
        self.corpsecret = corpsecret
        self.agentid = agentid

    def get_token(self):
        url = self.url
        values = {'corpid': self.corpid,
                  'corpsecret': self.corpsecret,
                  }
        req = requests.get(url, params=values)
        data = json.loads(req.text)
        if data["errcode"] == 0:
            return data["access_token"]
        else:
            print("企业微信access_token获取失败: " + str(data))
            return None
        return None

    def send_msg(self, touser, msgtype, content, title="默认标题", user_url="URL"):
        token = self.get_token()
        if token is None:
            return
        url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=" + token

        values = {
            "touser": touser,
            "toparty": "",
            "totag": "",
            "msgtype": msgtype,
            "agentid": self.agentid,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        if msgtype == "text":
            values["text"] = {"content": content}
        elif msgtype == "textcard":
            values["textcard"] = {
                "title": title,
                "description": content,
                "url": user_url,
                "btntxt": "详情"
            }
        elif msgtype == "markdown":
            values["markdown"] = {"content": content}

        resp = requests.post(url, json=values)
        data = json.loads(resp.text)
        if data["errcode"] != 0:
            print("企业微信消息发送失败: " + str(data))

# 获取uid
def get_uid(cookie):
    uid = cookie.split(";")
    t_uuid = ""
    for i in uid:
        # if i.find("muid=") >= 0:
        #     continue
        if i.split("=")[0].replace(" ", "") == "uid":
            t_uuid = i.split("=")[1]
    return t_uuid.replace(';', '').replace(' ', '')

# 获取cookie
def get_cookie(cookie):
    ck = cookie.split("; ")
    t_muid = ""
    t_openid = ""
    t_openkey = ""
    t_opentype = ""
    t_uuid = ""
    for i in ck:
        i = i.replace(" ", "")
        if i.split("=")[0] == "muid":
            t_muid = i.split("=")[1].replace(';', '')
        else:
            t_muid = "63999482202e308e34"
        if i.split("=")[0] == "openid":
            t_openid = i.split("=")[1].replace(';', '')
        elif i.split("=")[0] == "openkey":
            t_openkey = i.split("=")[1].replace(';', '')
        elif i.split("=")[0] == "opentype":
            t_opentype = i.split("=")[1].replace(';', '')
        elif i.split("=")[0] == "uid":
            t_uuid = i.split("=")[1].replace(';', '')
    # print(f"cookie是muid={t_muid}; openid={t_openid}; openkey={t_openkey}; opentype={t_opentype}; uid={t_uuid};")
    return f"muid={t_muid}; openid={t_openid}; openkey={t_openkey}; opentype={t_opentype}; uid={t_uuid};".strip()

# 是否在房间
def isJoin(cookie, r):
    url = 'https://node.kg.qq.com/webgo/webapp/tme?cmd=ktv_small_town.farm_webapp.enter_user_room_farm'
    headers = {
        # 'user-agent': 'Mozilla/5.0 (Linux; Android 8.0.0; MI 6 Build/OPR1.170623.027; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/71.0.3578.99 Mobile Safari/537.36 QQJSSDK/1.3 BridgeChannel/3  qua/V1_AND_KG_7.26.38_278_73387_X qmkege/7.26.38 bits/64',
        'user-agent': 'Mozilla/5.0 (iPad; CPU OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 QQJSSDK/1.0.0 qua/V1_IPH_KG_8.9.38_278_APP_A qmkege/8.9.38 GDTMobSDK/4.550.1  WKWebView model/iPad11,1',
        'cookie': cookie
    }
    # proxy = [
    #     {'http': '117.69.232.221:8089'},
    #     {'http': '114.103.81.69:8089'},
    #     {'http': '117.69.237.66:8089'},
    #     {'http': '114.103.81.69:8089'},
    # ]

    data = '{"ns":"proto_ktv_small_town","cmd":"ktv_small_town.farm_webapp.enter_user_room_farm","data":{"strRoomId":"room_id"},"mapExt":{"cmdName":"EnterUserRoomFarmReq"},"project":"kg","service":"ktv_small_town.farm_webapp.enter_user_room_farm"}'
    data = data.replace('room_id', r)
    try:
        # p = random.choice(proxy)
        # print("现在的ip是：", p)
        k = requests.post(url=url,headers=headers,data=data).json()
        print(k)
        if k["code"] == 0:
            return "登录成功"
        else:
            return "登录失败"
    except Exception as e:
        print(e)
        print("出错，重试")
        raise Exception

# 链接数据库
def connect():
    db = pymysql.connect(
        host='81.68.209.235',
        port=3378,
        user='kg',
        password='root',
        db='kg',
        charset='utf8'
    )
    cursor = db.cursor()
    return db, cursor

# 关闭数据库
def close(db, cursor):
    db.commit()
    cursor.close()
    db.close()

# def get_geolocation(ip):
#   r = requests.get('https://searchplugin.csdn.net/api/v1/ip/get?ip=' + ip).json()
#   print(r)
#   return {'ip': r["data"]["ip"], 'address': r["data"]["address"]}
#
def get_address(ip):
    url = "http://81.68.209.235/getaddress.php?ip=" + ip
    print(url)
    k = requests.get(url).json()
    print(k)
    return k
# 格式化地址
def format_address(ip):

    # result = json.loads(result)
    result = get_address(ip)
    # print(result)
    # location = f"{result['country']}{result['province']}{result['city']}{result['area']}"
    # network = f"{result['isp']}{result['net']}"
    return result['address']

user = Login()
uid = ""

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    global user
    user = Login()
    user.getQRcode()
    # user.showQRcode()
    result = {
        "url": user.qr_url
    }
    # result = {
    #     "url": "http://kg.qq.com/m.html?sig=98BD12A9348B7EAF476D14C8B80F247F&code=6acb98ea2c7935d9614970d7ddc098996ce0f39ce5d5eba196b13cfc62f0ec925c8cfb60"
    # }
    return render_template("scan_login.html", **result)

@app.route("/test")
def test():
    print("开始测试")
    return render_template("test.html")

@app.route("/check_login")
def check_login():
    global user, uid
    result = user.checkLogin(uid)
    uid = result["uid"]
    return json.dumps(result)
@app.route("/state")
def state():
    sql_state = "SELECT user.name,user.cookie, user.sta, user.up_time FROM " \
                "(user INNER JOIN sun_farm ON user.name=sun_farm.name) " \
                "INNER JOIN town_farm ON user.name=town_farm.name " \
                "WHERE sun_farm.switch=1 or town_farm.switch=1 ORDER BY user.sta,user.up_time DESC"
    db, cursor = connect()
    cursor.execute(sql_state)
    res = cursor.fetchall()
    close(db, cursor)
    # print(res)
    print(len(res))
    states = []
    for i, user in enumerate(res):
        # if user[0] == "东方14":
        #     break
        if user[2] == "1":
            st = "登录失败"
        else:
            st = "登录成功"
        up_time = user[3]
        timeArray = time.localtime(up_time)
        up_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        states.append({
            "id": i+1,
            "name": user[0],
            "state": st,
            "up_time": up_time
        })
    print(states)
    return render_template("state.html", lb = states)

@app.route("/video")
def video():
    device = request.args.get("device")
    print(device)
    videos = {
        "android": "http://81.68.209.235:8888/down/GrWqpdBIkC98",
        "apple": "http://81.68.209.235:8888/down/3B9W3ZfbjRZw"
    }
    video_url = {}
    video_url["url"] = videos[f"{device}"]
    return render_template("video.html", **video_url)

@app.route("/do", methods=['GET'])
def visitor():
    info = request.args
    print(info)
    cookie = info["cookie"]
    ip = info["localIP"]
    print("ip是：", ip)
    from_url = "手动录入"
    if "login?login=%E6%89%AB%E7%A0%81%E7%99%BB%E5%BD%95" in request.headers.get("referer"):
        cookie = cookie.replace("jiahao", "+")
        from_url = "扫码登录"
    uid = get_uid(cookie)
    print("uid是：",uid)
    print(cookie)
    print(from_url)
    db, cursor = connect()
    sql = "SELECT name, cookie FROM user WHERE uid = %s LIMIT 1"
    cursor.execute(sql, uid)
    res = cursor.fetchall()
    close(db, cursor)
    print(res)
    print(len(res))
    if len(res) == 1:
        r = res[0]
        new_cookie = get_cookie(cookie)
        if new_cookie == r[1]:
            rs = {
                "name": r[0]
            }
            return render_template('refresh.html', **rs)
        print("新cookie是", new_cookie)
        state = isJoin(new_cookie, "249f948127283788364675b0b3cfc9c568b5f79fb6bf82e6c1eb10db4f")
        result = "更新失败"
        print(state)
        if state == "登录成功":
            up_time = int(time.time())
            db, cursor = connect()
            sql2 = "UPDATE user SET cookie=%s,sta=%s,up_time=%s " \
                 "WHERE uid=%s"
            cursor.execute(sql2, (new_cookie, "0", up_time, uid))
            close(db, cursor)
            result = "更新成功"
        result = {"name": f"{r[0]}",
                  "state": f"{state}",
                  "referer": f"{from_url}",
                  "result": f"{result}"}
    else:
        result = {"name": "未知账号",
                  "state": "未知状态",
                  "referer": f"{from_url}",
                  "result": "录入失败"}
    QYWX = WeComtAlert("ww9991f71009451382", "njz0Ky9yfESCOys4B65ED8EtMWGeGush7tg-lhJhtqM", "1000002")
    now = int(time.time())
    timeArray = time.localtime(now)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    try:
        ipadd = format_address(ip)
    except:
        ipadd = "未知"
    # f"ip地址：{ipadd['ip']} {ipadd['address']}\n" \
    message = f"{otherStyleTime}\n\n" \
              f"名字：{result['name']}\n" \
              f"状态：{result['state']}\n" \
              f"结果：{result['result']}\n" \
              f"方式：{from_url}\n" \
              f"ip地址：{ipadd}\n" \
              f"cookie：{cookie}"
    QYWX.send_msg('@all', 'textcard', message, 'k歌更新cookie')
    return render_template('cool_result.html', **result)

# 酷安主页
@app.route("/cool_index")
def cool_index():
    db, cursor = connect()
    sql_get = "SELECT * FROM cool_apk WHERE id=1"
    cursor.execute(sql_get)
    res = cursor.fetchall()
    close(db, cursor)
    print(res[0])
    result = {"token": f"{res[0][1]}",
              "product_id": f"{res[0][2]}",
              "firstItem": f"{res[0][3]}",
              "price": f"{res[0][4]}",
              "switch_value": f"{res[0][5]}"}
    return render_template("cool_index.html", **result)

# 酷安上传token
@app.route("/coolapk_do", methods=['GET'])
def coolapk_index():
    info = request.args
    print(info)
    token = info["token"]
    product_id = info["product_id"]
    price = info["price"]
    switch = info["switch"]
    db, cursor = connect()
    sql_update = "UPDATE cool_apk SET token=%s, product_id=%s, price=%s,switch=%s WHERE id=1"
    cursor.execute(sql_update, (token,product_id,price,switch))
    sql_get = "SELECT * FROM cool_apk WHERE id=1"
    cursor.execute(sql_get)
    res = cursor.fetchall()
    close(db, cursor)
    print(res[0])
    result = {"token": f"{res[0][1]}"[:10],
              "product_id": f"{res[0][2]}",
              "firstItem": f"{res[0][3]}",
              "price": f"{res[0][4]}",
              "switch": f"{res[0][5]}"}
    QYWX = WeComtAlert("ww9991f71009451382", "ZbOhYA3_qE3X2BTApct-YGXUzZyYBVZ7_keM8PyM5QE", "1000003")
    now = int(time.time())
    timeArray = time.localtime(now)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    message = f"{otherStyleTime}\n\n" \
              f"token：{res[0][1]}\n" \
              f"product_id：{res[0][2]}\n" \
              f"firstItem：{res[0][3]}\n" \
              f"price：{res[0][4]}\n" \
              f"switch：{res[0][5]}\n"
    QYWX.send_msg('@all', 'textcard', message, '酷安更新token')
    return render_template('cool_result.html', **result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    app.run(host='0.0.0.0', port=port, debug=False)
