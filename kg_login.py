import re
import json
import time
import requests
import pyqrcode

class Login():
    def __init__(self):
        self.sig = ""
        self.code = ""
        self.qr_url = ""
        self.session = requests.session()
        self.session.headers = {
            "referer": "https://kg.qq.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
        }
    # 解密，获取g_tk_qrsig
    def get_qrsig(self, qrsig):
        t = 5381
        for qr in qrsig:
            t += (t << 5) + ord(qr)
        return 2147483647 & t

    # 获取二维码
    def getQRcode(self):
        url = "https://node.kg.qq.com/cgi/fcgi-bin/fcg_login_code?"
        data = {
            "jsonpCallback": "callback_0",
            "g_tk": "5381",
            "outCharset": "utf-8",
            "format": "jsonp",
            "g_tk_openkey": "5381",
            "_": f"{int(round(time.time() * 1000))}"
        }
        url2 = ""
        for d in data:
            url2 += "&" + d + "=" + data[d]
        # print(url2[1:])
        url = url + url2[1:]
        html = self.session.get(url).text
        k = html.replace("callback_0(", "").replace(")", "")
        k = json.loads(k)
        # print(k)
        self.sig = k["data"]["sig"]
        self.code = k["data"]["code"]
        self.qr_url = "http://kg.qq.com/m.html?sig=" + self.sig + "&code=" + self.code
        # print(self.qr_url)

    # 显示二维码图片
    def showQRcode(self):
        qr = pyqrcode.create(self.qr_url)
        # qr.png("static/scan_qr.png", scale=5)
        qr.svg('static/scan_qr.svg', scale=4, background="white", module_color="black")
        # qr.show()

    def checkLogin(self, uid):
        qrsig = self.session.cookies.get("qrsig")
        cookie = "aaaaaa"
        if qrsig == None:
            return {
                "code": 0,
                "uid": uid,
                "cookie": cookie
            }
        wait_url = "https://node.kg.qq.com/cgi/fcgi-bin/fcg_scan_login?g_tk=5381"
        data = [
            ('g_tk', '5381'),
            ('outCharset', 'utf-8'),
            ('format', 'json'),
            ('code', f'{self.code}'),
            ('sig', f'{self.sig}'),
            ('g_tk_qrsig', f'{self.get_qrsig(qrsig)}'),
            ('g_tk_openkey', '5381'),
        ]
        wait_res = self.session.post(url=wait_url, data=data).json()
        print(wait_res)
        if wait_res["code"] == 0:
            head_url = wait_res["data"]["head"]
            pat_uid = r"ttsing/([0-9]+)/"
            uid = re.findall(pat_uid, head_url)[0]
            print(uid)
        if wait_res["code"] == 1000 or wait_res["code"] == 0:
            return {
                "code": 0,
                "uid": uid,
                "cookie": cookie
            }
        if wait_res["code"] == -17108:
            return {
                "code": 1,
                "uid": uid,
                "cookie": cookie
            }
        if uid:
            c = self.session.cookies.get_dict()
            cookie = f"muid={c['muid']}; openid={c['openid']}; openkey={c['openkey']}; opentype={c['opentype']}; uid={uid};"
            print(cookie)
            return {
                "code": 2,
                "uid": uid,
                "cookie": cookie.replace("+", "jiahao")
            }

    def start(self):
        self.getQRcode()
        self.showQRcode()
        qrsig = self.session.cookies.get("qrsig")
        uid = ""
        while True:
            time.sleep(2)
        #     print(self.qr_url.split("?"))
            wait_url = "https://node.kg.qq.com/cgi/fcgi-bin/fcg_scan_login?g_tk=5381"
            data = [
                ('g_tk', '5381'),
                ('outCharset', 'utf-8'),
                ('format', 'json'),
                ('code', f'{self.code}'),
                ('sig', f'{self.sig}'),
                ('g_tk_qrsig', f'{self.get_qrsig(qrsig)}'),
                ('g_tk_openkey', '5381'),
            ]
            wait_res = self.session.post(url=wait_url,data=data).json()
            print(wait_res)
            if wait_res["code"] == 0:
                head_url = wait_res["data"]["head"]
                pat_uid = r"ttsing/([0-9]+)/"
                uid = re.findall(pat_uid, head_url)[0]
            if wait_res["code"] == 1000 or wait_res["code"] == 0:
                continue
            c = self.session.cookies.get_dict()
            cookie = f"muid={c['muid']}; openid={c['openid']}; openkey={c['openkey']}; opentype={c['opentype']}; uid={uid};"
            print(cookie)
            break

if __name__ == "__main__":
    Login().start()
