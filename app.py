import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

# ================== 基础配置 ==================
API_KEY = st.secrets["API_KEY"]
PRICE_URL = "https://open.steamdt.com/open/cs2/v1/price/single"
DATA_FILE = Path("gloves.json")

# ================== 名称映射（手套 + 四把枪） ==================
STEAMDT_NAME_MAP = {
    # 手套
    "裹手 | 沙漠头巾": "★ Hand Wraps | Desert Shamagh (Field-Tested)",
    "裹手 | 长颈鹿": "★ Hand Wraps | Giraffe (Field-Tested)",
    "裹手 | 蟒蛇": "★ Hand Wraps | Constrictor (Field-Tested)",
    "摩托手套 | 第三特种兵连": "★ Moto Gloves | 3rd Commando Company (Field-Tested)",
    "驾驶手套 | 美洲豹女王": "★ Driver Gloves | Queen Jaguar (Field-Tested)",
    "狂牙手套 | 黄色斑纹": "★ Broken Fang Gloves | Yellow-banded (Field-Tested)",
    "狂牙手套 | 针尖": "★ Broken Fang Gloves | Needle Point (Field-Tested)",
    "狂牙手套 | 精神错乱": "★ Broken Fang Gloves | Unhinged (Field-Tested)",
    "狂牙手套 | 翡翠": "★ Broken Fang Gloves | Jade (Field-Tested)",
    "驾驶手套 | 绯红列赞": "★ Driver Gloves | Rezan the Red (Field-Tested)",
    "驾驶手套 | 西装革履": "★ Driver Gloves | Black Tie (Field-Tested)",
    "驾驶手套 | 雪豹": "★ Driver Gloves | Snow Leopard (Field-Tested)",
    "摩托手套 | 终点线": "★ Moto Gloves | Finish Line (Field-Tested)",
    "摩托手套 | 小心烟雾弹": "★ Moto Gloves | Smoke Out (Field-Tested)",
    "摩托手套 | 血压": "★ Moto Gloves | Blood Pressure (Field-Tested)",
    "专业手套 | 陆军少尉长官": "★ Specialist Gloves | Lt. Commander (Field-Tested)",
    "专业手套 | 一线特工": "★ Specialist Gloves | Field Agent (Field-Tested)",
    "专业手套 | 老虎精英": "★ Specialist Gloves | Tiger Strike (Field-Tested)",
    "专业手套 | 渐变大理石": "★ Specialist Gloves | Marble Fade (Field-Tested)",
    "裹手 | 警告！": "★ Hand Wraps | CAUTION! (Field-Tested)",
    "运动手套 | 大型猎物": "★ Sport Gloves | Big Game (Field-Tested)",
    "运动手套 | 猩红头巾": "★ Sport Gloves | Scarlet Shamagh (Field-Tested)",
    "运动手套 | 弹弓": "★ Sport Gloves | Slingshot (Field-Tested)",
    "运动手套 | 夜行衣": "★ Sport Gloves | Nocts (Field-Tested)",
    # 四把枪
    "M4A4 | 反冲精英 (久经沙场)": "M4A4 | Temukau (Field-Tested)",
    "AK-47 | 一发入魂 (久经沙场)": "AK-47 | Head Shot (Field-Tested)",
    "USP 消音版 | 印花集 (久经沙场)": "USP-S | Printstream (Field-Tested)",
    "AWP | 迷人眼 (久经沙场)": "AWP | Chromatic Aberration (Field-Tested)",
}

# ================== 默认数据 ==================
DEFAULT_GLOVES = [
    {"name": "裹手 | 沙漠头巾", "min_price": 354},
    {"name": "裹手 | 长颈鹿", "min_price": 372.5},
    {"name": "裹手 | 蟒蛇", "min_price": 391.5},
    {"name": "摩托手套 | 第三特种兵连", "min_price": 350},
    {"name": "驾驶手套 | 美洲豹女王", "min_price": 405},
    {"name": "狂牙手套 | 黄色斑纹", "min_price": 404},
    {"name": "狂牙手套 | 针尖", "min_price": 386.5},
    {"name": "狂牙手套 | 精神错乱", "min_price": 430},
    {"name": "驾驶手套 | 绯红列赞", "min_price": 564.5},
    {"name": "摩托手套 | 终点线", "min_price": 701.5},
    {"name": "摩托手套 | 小心烟雾弹", "min_price": 849},
    {"name": "狂牙手套 | 翡翠", "min_price": 690},
    {"name": "专业手套 | 陆军少尉长官", "min_price": 900},
    {"name": "摩托手套 | 血压", "min_price": 969.5},
    {"name": "专业手套 | 一线特工", "min_price": 1041.5},
    {"name": "驾驶手套 | 西装革履", "min_price": 1066.5},
    {"name": "裹手 | 警告！", "min_price": 950},
    {"name": "专业手套 | 老虎精英", "min_price": 1600},
    {"name": "专业手套 | 渐变大理石", "min_price": 1179},
    {"name": "运动手套 | 大型猎物", "min_price": 1231.5},
    {"name": "运动手套 | 猩红头巾", "min_price": 1769},
    {"name": "运动手套 | 弹弓", "min_price": 3809},
    {"name": "驾驶手套 | 雪豹", "min_price": 2219},
    {"name": "运动手套 | 夜行衣", "min_price": 4744},
]

DEFAULT_WEAPONS = [
    {"name": "M4A4 | 反冲精英 (久经沙场)", "min_price": 0},
    {"name": "AK-47 | 一发入魂 (久经沙场)", "min_price": 0},
    {"name": "USP 消音版 | 印花集 (久经沙场)", "min_price": 0},
    {"name": "AWP | 迷人眼 (久经沙场)", "min_price": 0},
]

# ================== 字体 ==================
font_path = r"C:\Windows\Fonts\msyh.ttc"
try:
    font_manager.fontManager.addfont(font_path)
    plt.rcParams["font.family"] = "Microsoft YaHei"
except Exception:
    plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

# ================== 页面 ==================
st.set_page_config(page_title="CS2 变革/反冲炼金收益展示", layout="wide")
st.title("🎮 CS2 变革/反冲炼金收益展示")

# ================== 文件读写 ==================
def load_data():
    if not DATA_FILE.exists():
        return DEFAULT_GLOVES, DEFAULT_WEAPONS
    with DATA_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, DEFAULT_WEAPONS
    return data.get("gloves", DEFAULT_GLOVES), data.get("weapons", DEFAULT_WEAPONS)

def save_data(gloves, weapons):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump({"gloves": gloves, "weapons": weapons}, f, ensure_ascii=False, indent=2)

if "gloves" not in st.session_state or "weapons" not in st.session_state:
    g, w = load_data()
    st.session_state.gloves, st.session_state.weapons = g, w

# ================== 拉价 ==================
def fetch_lowest_price(market_hash):
    try:
        r = requests.get(
            PRICE_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            params={"marketHashName": market_hash},
            timeout=10,
        )
        data = r.json()
        if not data.get("success"):
            return None
        prices = [p.get("sellPrice") for p in data.get("data", []) if p.get("sellPrice")]
        return min(prices) if prices else None
    except Exception:
        return None

def update_all(items):
    updated = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {
            ex.submit(fetch_lowest_price, STEAMDT_NAME_MAP.get(i["name"])): i
            for i in items
            if i["name"] in STEAMDT_NAME_MAP
        }
        for fut in as_completed(futs):
            item = futs[fut]
            p = fut.result()
            if p:
                item["min_price"] = float(p)
                updated += 1
    return updated

# ================== Sidebar：手套 ==================
st.sidebar.subheader("🧤 手套操作")
glove_names = [g["name"] for g in st.session_state.gloves]
sel_glove = st.sidebar.selectbox("选择手套：", glove_names)
cur_glove = next(g for g in st.session_state.gloves if g["name"] == sel_glove)

glove_val = st.sidebar.number_input(
    "手套最低价（手动）",
    0.0, 99999.0,
    float(cur_glove["min_price"]),
    1.0,
    key="glove_input"
)

col1, col2 = st.sidebar.columns(2)
btn_g1 = col1.button("🧤 刷新当前")
btn_g2 = col2.button("🔁 刷新全部")

if btn_g1:
    en = STEAMDT_NAME_MAP.get(cur_glove["name"])
    if en:
        p = fetch_lowest_price(en)
        if p:
            cur_glove["min_price"] = float(p)
            st.sidebar.success(f"✅ 手套已更新：{p}")
        else:
            st.sidebar.error("❌ 手套没拉到价格")
    else:
        st.sidebar.error("❌ 没配置映射")

if btn_g2:
    with st.spinner("⚙️ 正在刷新所有手套..."):
        n = update_all(st.session_state.gloves)
    st.sidebar.success(f"✅ 已刷新 {n} 只手套")
else:
    # 没点按钮就是手动改
    cur_glove["min_price"] = glove_val

st.sidebar.markdown(f"当前手套价：**{cur_glove['min_price']:.2f}** 元")

# ================== Sidebar：枪 ==================
st.sidebar.markdown("---")
st.sidebar.subheader("🔫 枪操作")
weapon_names = [w["name"] for w in st.session_state.weapons]
sel_weapon = st.sidebar.selectbox("选择枪：", weapon_names)
cur_weapon = next(w for w in st.session_state.weapons if w["name"] == sel_weapon)

weapon_val = st.sidebar.number_input(
    "枪最低价（手动）",
    0.0, 99999.0,
    float(cur_weapon["min_price"]),
    1.0,
    key="weapon_input"
)

col3, col4 = st.sidebar.columns(2)
btn_w1 = col3.button("🔫 刷新当前枪")
btn_w2 = col4.button("💥 刷新全部枪")

if btn_w1:
    en = STEAMDT_NAME_MAP.get(cur_weapon["name"])
    if en:
        p = fetch_lowest_price(en)
        if p:
            cur_weapon["min_price"] = float(p)
            st.sidebar.success("✅ 当前这把枪已更新")
        else:
            st.sidebar.error("❌ 枪没拉到价格")
    else:
        st.sidebar.error("❌ 这把枪没配置映射")

if btn_w2:
    with st.spinner("⚙️ 正在刷新所有枪..."):
        n = update_all(st.session_state.weapons)
    st.sidebar.success(f"✅ 已刷新 {n} 把枪")
else:
    cur_weapon["min_price"] = weapon_val

st.sidebar.markdown(f"当前枪价：**{cur_weapon['min_price']:.2f}** 元")

# 保存到文件
save_data(st.session_state.gloves, st.session_state.weapons)

# ================== 主区：手套图表 ==================
st.subheader("📊 手套价格展示图")

# 计算手套平均价
g_names = [g["name"] for g in st.session_state.gloves]
g_prices = [g["min_price"] for g in st.session_state.gloves]
avg_glove_price = sum(g_prices) / len(g_prices) if g_prices else 0

fig, ax = plt.subplots(figsize=(10, 4))
ax.bar(g_names, g_prices, color="#66b3ff")

# ✅ 正确设置刻度和标签
ax.set_xticks(range(len(g_names)))
ax.set_xticklabels(g_names, rotation=45, ha="right")

ax.set_ylabel("价格 (¥)")
ax.set_title("手套价格展示")

# 在每个柱子上标出价格
for i, v in enumerate(g_prices):
    ax.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)

# 画平均线
ax.axhline(avg_glove_price, color="red", linestyle="--", linewidth=1)
ax.text(
    len(g_names) - 0.5,
    avg_glove_price,
    f"平均价：{avg_glove_price:.1f}",
    color="red",
    ha="right",
    va="bottom",
    fontsize=8,
)

st.pyplot(fig)


# ================== 主区：枪价格图表 ==================
st.subheader("📊 炼金红皮价格展示图")

# 原来的四把枪
w_names = [w["name"] for w in st.session_state.weapons]
w_prices = [w["min_price"] for w in st.session_state.weapons]

# 手套平均价 ÷ 5
avg_glove_div_5 = avg_glove_price / 5 if avg_glove_price else 0

# 合并成一个列表再排序（从左到右价格依次增大）
combined = list(zip(w_names, w_prices))
combined.sort(key=lambda x: x[1])

sorted_names = [c[0] for c in combined]
sorted_prices = [c[1] for c in combined]

fig2, ax2 = plt.subplots(figsize=(6, 3))
x = range(len(sorted_names))
ax2.bar(x, sorted_prices, color="#ff9966")

# ✅ 先设置刻度
ax2.set_xticks(x)
ax2.set_xticklabels(sorted_names, rotation=30, ha="right")
ax2.set_ylabel("价格 (¥)")
ax2.set_title("枪械价格展示")

# 在每个柱子上标出价格
for i, v in enumerate(sorted_prices):
    ax2.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)

# ✅ 加一条红色虚线表示“手套平均价 ÷ 5”
ax2.axhline(avg_glove_div_5, color="red", linestyle="--", linewidth=1)
ax2.text(
    len(sorted_names) - 0.2,
    avg_glove_div_5,
    f"炼金平均价格：{avg_glove_div_5:.1f}",
    color="red",
    ha="right",
    va="bottom",
    fontsize=8,
)

st.pyplot(fig2)

# ================== 主区：表格 ==================
st.subheader("🧤 手套价格表")
st.dataframe(
    [
        {"手套": g["name"], "最低价": g["min_price"]}
        for g in st.session_state.gloves
    ]
)

st.subheader("🔫 炼金红皮价格表")
st.dataframe(
    [
        {"枪": w["name"], "最低价": w["min_price"]}
        for w in st.session_state.weapons
    ]
)

