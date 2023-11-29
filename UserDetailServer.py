import sqlite3
from datetime import datetime
import math
from flask import Flask, render_template
from waitress import serve
import hashlib
import configparser
import json
import time
import os

config = configparser.ConfigParser()
config.read('config.ini')
secret_phrase = config['API']['secret']

dbLoc = '/etc/x-ui/x-ui.db'

app = Flask(__name__)


def restart_xray():

    service_name = "x-ui"
    os.system("systemctl restart {}".format(service_name))


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s%s" % (s, size_name[i])


def charge_func(size_of_plan, remark):
    remain_traffic, remain_time = get_remain_traffic_time(remark)
    total_charge = size_of_plan + remain_traffic
    conn = sqlite3.connect(dbLoc)
    c = conn.cursor()
    c.execute('UPDATE inbounds SET total = ? WHERE remark = ?',
              (total_charge, remark))
    conn.commit()
    c.close()
    conn.close()
    new_time = remain_time + 2592000000  # in seconds -> + 30 days
    charge_time(new_time, remark)

    restart_xray()


def charge_time(time, remark):
    conn = sqlite3.connect(dbLoc)
    c = conn.cursor()
    c.execute(
        'UPDATE inbounds SET expiry_time = ?, enable = ?, up = ?, down = ? WHERE remark = ?', (time, 1, 0, 0, remark))
    conn.commit()
    c.close()
    conn.close()


def make_secret_phrase(remark):
    port, settings = get_port_and_settings(remark)
    uuid = (json.loads(settings)["clients"][0]["id"])
    created_combo = f"{port}{uuid}{secret_phrase}{remark}"
    created_secret = hashlib.sha256(created_combo.encode('UTF-8')).hexdigest()
    return created_secret


def check_secret(remark, client_secret):
    return make_secret_phrase(remark) == client_secret


def get_port_and_settings(remark):
    conn = sqlite3.connect(dbLoc)
    c = conn.cursor()
    c.execute("SELECT port, settings FROM inbounds WHERE remark=?", (remark,))
    result = c.fetchone()
    conn.close()
    if result is None:
        return None, None
    else:
        return result[0], result[1]


def get_remain_traffic_time(remark):
    conn = sqlite3.connect(dbLoc)
    c = conn.cursor()
    c.execute(
        "SELECT up, down, total, expiry_time FROM inbounds WHERE remark=?", (remark,))
    result = c.fetchone()
    conn.close()
    remain_traffic = (result[2] - (result[0] + result[1]))
    if (remain_traffic > 3221225472):
        remain_traffic = 3221225472
    elif (remain_traffic < 0):
        remain_traffic = 0
    if (result[3] != 0):
        remain_time = result[3] - (int(time.time() * 1000))
        if (remain_time > 259200000):
            remain_time = (int(time.time()) * 1000) + 259200000
        elif (remain_time < 0):
            remain_time = (int(time.time()) * 1000)
        else:
            remain_time = (int(time.time()) * 1000) + remain_time
    else:
        remain_traffic = remain_traffic = (result[2] - (result[0] + result[1]))
        remain_time = -2592000000

    if result is None:
        return None, None
    else:
        return remain_traffic, remain_time

# @app.route('/')
# def main():
#     return render_template('index.html')


# @app.route('/acc_checker')
# def main():
#     return render_template('index.html')

@app.route('/api/ch/<string:user>/<string:secret>/<string:size_of_plan>')
def renewal(user, secret, size_of_plan):
    if (check_secret(user, secret)):
        charge_func(int(size_of_plan), user)
        dicResult = {"status": "OK"}
        return dicResult
    else:
        dicResult = {"status": "error"}
        return dicResult


@app.route('/api/de/<string:user>')
def checker(user):
    query = f"SELECT remark,down,up,total,expiry_time,enable FROM inbounds WHERE remark='{user}';"
    con = sqlite3.connect(dbLoc)
    cur = con.cursor()
    res = cur.execute(query)
    result = res.fetchone()
    res.close()
    cur.close()
    con.close()
    userName = result[0]
    downloaded = convert_size(result[1])
    uploaded = convert_size(result[2])
    usedTraffic = convert_size(result[1] + result[2])
    if (result[3] == 0):
        totalBandwith = "Unlimited"
        remainTraffic = "Unlimited"
    else:
        totalBandwith = convert_size(result[3])
        if ((result[3] - (result[1] + result[2])) >= 0):
            remainTraffic = convert_size(result[3] - (result[1] + result[2]))
        else:
            remainTraffic = convert_size(0)
    if (result[4] == 0):
        expireDate = "Unlimited"
    else:
        expireDate = datetime.fromtimestamp(int((result[4] / 1000)))
    if (result[5] == 1):
        enable = "On"
    else:
        enable = "Off"

    dicResult = {
        "remark": userName,
        "down": downloaded,
        "up": uploaded,
        "total": totalBandwith,
        "expire_time": expireDate,
        "enable": enable,
        "used": usedTraffic,
        "remain": remainTraffic
    }
    return dicResult


if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=80)
