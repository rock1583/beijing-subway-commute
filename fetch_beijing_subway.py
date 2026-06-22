# -*- coding: utf-8 -*-
"""
从高德地图（AMap）拉取北京地铁线网数据，转换成网页可直接使用的数据文件。

用法：
    python3 fetch_beijing_subway.py

会生成：beijing_subway.js  —— 其中定义全局变量 window.SUBWAY_DATA，
供 地铁查询.html 通过 <script src="beijing_subway.js"> 加载（本地双击打开即可，无跨域问题）。

数据来源：高德地铁图公开接口
    https://map.amap.com/service/subway?_<时间戳>&srhdata=<城市码>_drw_<城市拼音>.json
    北京：城市码 1100，文件名 1100_drw_beijing.json

说明：
- 该接口提供线路、站点顺序、站点经纬度、换乘信息，但【不提供站间运行时间】。
- 因此本脚本按"站间地理距离 ÷ 平均运行速度"估算每段耗时（含停站，约 36 km/h），
  这样郊区长间距自然比市区更耗时，比"固定每站 2 分钟"更贴近真实。
- 估算速度、最小段耗时均为常量，可按需调整。
"""

import json
import math
import os
import time
import urllib.request

# ---- 可调参数 ----
CITY_ADCODE = "1100"          # 北京城市码
CITY_PINYIN = "beijing"
AVG_KMPH = 36.0               # 地铁平均运行速度（含停站），用于由距离估算耗时
MIN_SEG_MIN = 2               # 每段最小耗时（分钟），与"默认每站 2 分钟"对齐
OUT_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beijing_subway.js")
RAW_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beijing_subway_raw.json")


def fetch_raw():
    """拉取高德地铁原始 JSON（若本地已有缓存则直接复用）。"""
    if os.path.exists(RAW_JSON) and os.path.getsize(RAW_JSON) > 1000:
        print(f"使用本地缓存：{RAW_JSON}")
        with open(RAW_JSON, "r", encoding="utf-8") as f:
            return json.load(f)

    url = (f"https://map.amap.com/service/subway?_{int(time.time()*1000)}"
           f"&srhdata={CITY_ADCODE}_drw_{CITY_PINYIN}.json")
    print(f"拉取：{url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    with open(RAW_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def haversine_km(a, b):
    """两个 (lng, lat) 点之间的球面距离（公里）。"""
    (lng1, lat1), (lng2, lat2) = a, b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def parse_sl(sl):
    """解析 '116.17,39.92' -> (116.17, 39.92)，失败返回 None。"""
    try:
        lng, lat = sl.split(",")
        return (float(lng), float(lat))
    except Exception:
        return None


def build():
    raw = fetch_raw()
    lines = {}
    total_stations = 0

    for idx, ln in enumerate(raw["l"]):
        name = ln.get("ln", f"线路{idx+1}")
        color = "#" + ln.get("cl", "888888")  # 高德颜色不带 #
        stations, coords = [], []

        for st in ln["st"]:
            stations.append(st["n"])
            coords.append(parse_sl(st.get("sl", "")))

        # 估算相邻站点耗时
        times = []
        for i in range(len(stations) - 1):
            a, b = coords[i], coords[i + 1]
            if a and b:
                km = haversine_km(a, b)
                minutes = max(MIN_SEG_MIN, round(km / AVG_KMPH * 60))
            else:
                minutes = MIN_SEG_MIN
            times.append(int(minutes))

        lines[f"L{idx}"] = {
            "name": name,
            "color": color,
            "stations": stations,
            # 经纬度保留为 [lng,lat]，便于将来画地图；当前算法只用 times
            "coords": [[round(c[0], 6), round(c[1], 6)] if c else None for c in coords],
            "times": times,
        }
        total_stations += len(stations)

    city = {
        "name": "北京",
        "source": "高德地图 AMap（公开地铁图接口）",
        "avgKmph": AVG_KMPH,
        "lines": lines,
    }

    # 写成 JS 数据文件（赋值给 window.SUBWAY_DATA），<script src> 加载不受跨域限制
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("// 自动生成：北京地铁线网数据（来源：高德地图）。请勿手改，重新运行 fetch_beijing_subway.py 刷新。\n")
        f.write("window.SUBWAY_DATA = ")
        json.dump(city, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # 统计换乘站
    name2lines = {}
    for lk, ln in lines.items():
        for s in ln["stations"]:
            name2lines.setdefault(s, set()).add(lk)
    transfers = sum(1 for s, ls in name2lines.items() if len(ls) > 1)

    print(f"完成：{len(lines)} 条线路，{len(name2lines)} 个站点（{transfers} 个换乘站）")
    print(f"已写入：{OUT_JS}")


if __name__ == "__main__":
    build()
