# 北京地铁通勤时间计算

一个纯前端网页应用，基于高德地图（AMap）的北京地铁线网数据，估算地铁通勤所需时间。

## 在线访问

部署在 GitHub Pages 后，直接打开仓库的 Pages 链接即可使用（入口 `index.html` 会自动跳转到主页面）。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `地铁查询.html` | 主页面，打开即用 |
| `index.html` | 入口页，自动跳转到主页面 |
| `amap_config.js` | 高德地图 Key 配置（前端 Key，浏览器中本就可见，靠高德控制台「域名白名单」保护）|
| `beijing_subway.js` | 北京地铁线网数据（由脚本生成）|
| `beijing_subway_raw.json` | 高德接口返回的原始数据 |
| `fetch_beijing_subway.py` | 抓取并生成 `beijing_subway.js` 的脚本，运行 `python3 fetch_beijing_subway.py` 可刷新数据 |

## 安全说明

`amap_config.js` 中的高德 Web 端 Key 属于前端密钥，任何访问网页的人都能在浏览器里看到，这是高德 JS API 的固有特性，无法隐藏。
正确的保护方式是在 [高德控制台](https://console.amap.com/) 为该 Key 设置 **域名白名单（Referer 白名单）**，只允许本站的 GitHub Pages 域名调用。
