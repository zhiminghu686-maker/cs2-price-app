import json
import streamlit as st
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from matplotlib import font_manager
import matplotlib.pyplot as plt
import os

# ================== 字体 ==================
# 1. 找你下载的字体（名字要和你上传的一样）
font_path = Path(__file__).parent / "NotoSansCJKsc-Regular.otf"

if font_path.exists():
    # 2. 注册字体
    font_manager.fontManager.addfont(str(font_path))
    # 3. 动态获取这个字体真正的名字，避免写错
    font_prop = font_manager.FontProperties(fname=str(font_path))
    font_name = font_prop.get_name()
    # 4. 告诉 matplotlib 用这个
    plt.rcParams["font.family"] = font_name
else:
    # 本地兜底
    win_font_path = r"C:\Windows\Fonts\msyh.ttc"
    if os.path.exists(win_font_path):
        font_manager.fontManager.addfont(win_font_path)
        plt.rcParams["font.family"] = "Microsoft YaHei"
    else:
        plt.rcParams["font.sans-serif"] = ["SimHei"]

# 负号不变方块
plt.rcParams["axes.unicode_minus"] = False

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
    "M4A4 | 活色生香": "M4A4 | In Living Color (Field-Tested)",
    "AK-47 | 一发入魂": "AK-47 | Head Shot (Field-Tested)",
    "USP 消音版 | 倒吊人": "USP-S | The Traitor (Field-Tested)",
    "AWP | 迷人眼": "AWP | Chromatic Aberration (Field-Tested)",
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
    {"name": "M4A4 | 活色生香", "min_price": 0},
    {"name": "AK-47 | 一发入魂", "min_price": 0},
    {"name": "USP 消音版 | 倒吊人", "min_price": 0},
    {"name": "AWP | 迷人眼", "min_price": 0},
]

# ================== 材料枪磨损区间 ==================
WEAR_RANGE = {
    "M4A4 | 活色生香": (0.0, 0.79),
    "AK-47 | 一发入魂": (0.0, 1.0),
    "AWP | 迷人眼": (0.0, 0.70),
    "USP 消音版 | 倒吊人": (0.0, 1.0),
}

# ================== 手套固定磨损区间 + 各外观分档 ==================
GLOVE_MIN = 0.06
GLOVE_MAX = 0.80

# 手套的品质区间（这是手套专用的那套）
GLOVE_TIER = {
    "崭新出厂 (FN)": (0.06, 0.07),
    "略有磨损 (MW)": (0.07, 0.15),
    "久经沙场 (FT)": (0.15, 0.38),
    "破损不堪 (WW)": (0.38, 0.45),
    "战痕累累 (BS)": (0.45, 0.80),
}

# ================== 页面 ==================
st.set_page_config(page_title="CS2 变革/反冲炼金收益展示", layout="wide")
st.title("🎮 CS2 蛇噬/反冲炼金收益展示")

# ========== 工具函数：材料磨损 -> 手套磨损（线性反映射） ==========
def mat_float_to_glove_float(material_name: str, mat_float: float):
    if material_name not in WEAR_RANGE:
        return None
    m_min, m_max = WEAR_RANGE[material_name]
    if m_max <= m_min:
        return None
    # 夹紧到材料自身区间
    mf = max(m_min, min(m_max, mat_float))
    pos = (mf - m_min) / (m_max - m_min)  # 映射到[0,1]
    glove_f = GLOVE_MIN + pos * (GLOVE_MAX - GLOVE_MIN)
    # 再夹紧到手套区间
    glove_f = max(GLOVE_MIN, min(GLOVE_MAX, glove_f))
    return round(glove_f, 6)

def classify_glove_tier(glove_float: float):
    for tier_name, (lo, hi) in GLOVE_TIER.items():
        if lo <= glove_float <= hi:
            return tier_name
    # 落在区间边界外时给出最近的档位提示
    return None

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

def calc_max_material_float_for_glove_tier(material_name: str, target_glove_max: float):
    """
    给定：材料枪 + 想要的手套成色的上限
    返回：这把材料枪最高能用多少磨损
    """
    if material_name not in WEAR_RANGE:
        return None

    mat_min, mat_max = WEAR_RANGE[material_name]

    # 映射比例：手套目标在手套区间里的位置
    ratio = (target_glove_max - GLOVE_MIN) / (GLOVE_MAX - GLOVE_MIN)
    if ratio < 0:
        return None

    # 反推材料磨损
    mat_float = mat_min + ratio * (mat_max - mat_min)

    # 不超过材料自身最大磨损
    return min(mat_float, mat_max)

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

# ================== 主区：反推材料最大磨损 ==================
st.subheader("🧮 想要这种手套外观，我的材料枪最多能用多少磨损？")

col_a, col_b = st.columns(2)
with col_a:
    sel_mat = st.selectbox("选择材料枪：", list(WEAR_RANGE.keys()), key="mat_for_inverse")
with col_b:
    sel_tier = st.selectbox("想要的手套外观：", list(GLOVE_TIER.keys()))

tier_min, tier_max = GLOVE_TIER[sel_tier]

if st.button("计算最大可用材料磨损", key="btn_calc_inverse"):
    res = calc_max_material_float_for_glove_tier(sel_mat, tier_max)
    if res is None:
        st.error("无法计算，请检查区间。")
    else:
        st.success(
            f"要合出 **{sel_tier}** 的手套，"
            f"{sel_mat} 的磨损应 ≤ **{res:.6f}**"
        )
        st.caption("建议再多留 0.001~0.003 安全余量。")

# ========== 主区：选择5把材料枪 + 输入各自磨损 ==========
st.subheader("🧪 选择5把材料枪 + 自填磨损 → 计算合成手套磨损（线性模型）")

# 可重复选择，所以做成5行选择器
mat_sel = []
for i in range(5):
    c1, c2, c3 = st.columns([1.2, 1.0, 1.6])
    with c1:
        name = st.selectbox(
            f"第{i+1}把材料枪类型",
            list(WEAR_RANGE.keys()),
            key=f"mat_pick_{i}"
        )
    m_min, m_max = WEAR_RANGE[name]
    with c2:
        wear = st.number_input(
            f"磨损{i+1}",
            min_value=float(m_min),
            max_value=float(m_max),
            value=float(m_min),
            step=0.0001,
            format="%.6f",
            key=f"mat_wear_{i}"
        )
    with c3:
        st.caption(f"允许磨损：[{m_min:.2f} ~ {m_max:.2f}]")
    mat_sel.append((name, wear))

if st.button("计算合成手套磨损", key="btn_calc_forward"):
    mapped = []
    for (n, w) in mat_sel:
        g = mat_float_to_glove_float(n, w)
        if g is None:
            st.error(f"无法映射：{n}")
            mapped = []
            break
        mapped.append({"材料枪": n, "材料磨损": w, "映射到手套磨损": g})

    if mapped:
        # 平均得到最终手套磨损
        g_vals = [x["映射到手套磨损"] for x in mapped]
        g_avg = sum(g_vals) / len(g_vals)
        tier = classify_glove_tier(g_avg)

        st.markdown("**单把映射明细：**")
        st.dataframe(mapped, use_container_width=True)

        st.success(f"➡️ 计算得到的 **手套磨损**：**{g_avg:.6f}**")
        if tier:
            st.info(f"预计成色：**{tier}**  （区间：{GLOVE_TIER[tier][0]:.2f}~{GLOVE_TIER[tier][1]:.2f}）")
        else:
            st.warning("未能匹配到手套成色区间（可能数值越界或配置问题）")

        # 可视化：5把映射 & 平均线
        fig_fw, ax_fw = plt.subplots(figsize=(8, 2.8))
        xs = range(1, 6)
        ax_fw.bar(xs, g_vals)
        ax_fw.axhline(g_avg, linestyle="--")
        ax_fw.set_xticks(xs)
        ax_fw.set_xticklabels([f"{i}" for i in xs])
        ax_fw.set_ylabel("映射到手套磨损")
        ax_fw.set_title("5把材料映射到手套磨损（越低越好）")
        for i, v in enumerate(g_vals, start=1):
            ax_fw.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
        ax_fw.text(5.8, g_avg, f"平均：{g_avg:.3f}", ha="right", va="bottom")
        st.pyplot(fig_fw)

# ================== 主区：手套图表 ==================
st.subheader("📊 手套价格展示图(久经沙场)")

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
st.subheader("📊 炼金红皮价格展示图(久经沙场)")

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
