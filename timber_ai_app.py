import streamlit as st
import math
import re

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V9")

# =========================
# INPUT
# =========================
user_input = st.text_area("📥 Customer Enquiry", height=200)

col1, col2, col3 = st.columns(3)
with col1:
    balau_rate = st.number_input("Balau $/ton", value=5500)
with col2:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)
with col3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)

colA, colB = st.columns(2)
generate = colA.button("🚀 Generate")
refresh = colB.button("🔄 Refresh")

if refresh:
    st.rerun()

# =========================
# PLYWOOD PRICES
# =========================
plywood_prices = {
    "furniture": {3:16, 6:17, 9:19, 12:24, 15:27, 18:32, 25:52},
    "marine": {6:27, 9:37, 12:45, 15:57, 18:68, 25:96},
    "mr": {3:4.5, 6:9.9, 9:15, 12:21.5, 15:28, 18:31}
}

# =========================
# SIZE CONVERSION (RAW → PLANED)
# =========================
inch_to_mm = {
    1: 20,
    2: 43,
    3: 70,
    4: 93,
    6: 143,
    8: 193,
    12: 293
}

def mm_to_inch(mm):
    for inch, val in inch_to_mm.items():
        if abs(mm - val) <= 5:
            return inch
    return max(round(mm / 25.4), 1)

def safe_int(x):
    try:
        return int(x)
    except:
        return 1

def std_length(ft):
    if ft == 19:
        return 20
    return max(ft, 1)

def calc(thk, wid, length, rate):
    if thk == 0 or wid == 0 or length == 0:
        return 0, 0
    pcs = math.floor(7200 / thk / wid / length)
    if pcs <= 0:
        return 0, 0
    price = round(rate / pcs)
    return pcs, price

def pcs_color(pcs):
    if pcs < 10:
        return "🔴"
    elif pcs < 50:
        return "🟡"
    return "🟢"

# =========================
# MAIN
# =========================
if generate:

    lines = user_input.split("\n")
    current = None

    timber_data = {}
    reply_lines = []
    total = 0
    has_timber = False

    for line in lines:
        text = line.lower().strip()
        if not text:
            continue

        # detect species
        if "kapur" in text:
            current = ("Kapur", kapur_rate)
        elif "balau" in text:
            current = ("Balau", balau_rate)
        elif "chengal" in text:
            current = ("Chengal", chengal_rate)

        # qty
        qty_match = re.findall(r'(\d+)\s*(pcs|nos|pieces|sheets?)', text)
        qty = int(qty_match[0][0]) if qty_match else 1

        # ================= TIMBER =================
        size_match = re.findall(r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+)', text)

        if size_match and current:

            has_timber = True

            v1 = int(size_match[0][0])
            v2 = int(size_match[0][1])
            ft = int(size_match[0][2])

            # detect mixed / inch / mm
            if "mm" in text:
                # mm input
                thk = mm_to_inch(v1)
                wid = mm_to_inch(v2)
            else:
                # inch input or mixed → assume inch if small value
                thk = v1 if v1 <= 12 else mm_to_inch(v1)
                wid = v2 if v2 <= 12 else mm_to_inch(v2)

            length = std_length(ft)

            pcs, price = calc(thk, wid, length, current[1])

            if pcs == 0:
                reply_lines.append(f"{current[0]} timber size error → check input")
                continue

            line_total = price * qty
            total += line_total

            # convert to planed mm for customer
            mm1 = inch_to_mm.get(thk, thk * 25)
            mm2 = inch_to_mm.get(wid, wid * 25)

            timber_data.setdefault(current[0], []).append([
                f"{v1} x {v2} x {ft}",
                f"{thk}x{wid}x{length}",
                current[1],
                f"{pcs_color(pcs)} {pcs}",
                price,
                qty,
                line_total
            ])

            reply_lines.append(f"{current[0]} timber (planed)")
            reply_lines.append(f"{mm1}mm x {mm2}mm x {ft}ft @ ${price}/pcs x {qty} = ${line_total}\n")

        # ================= PLYWOOD =================
        if "plywood" in text or "plywod" in text:

            if "marine" in text:
                grade = "marine"
            elif "mr" in text or "floor" in text:
                grade = "mr"
            else:
                grade = "furniture"

            thk_match = re.findall(r'(\d+\.?\d*)mm', text)

            for t in thk_match:
                t = float(t)
                if t in [5, 5.5]:
                    t = 6
                t = int(t)

                if t in plywood_prices[grade]:

                    price = plywood_prices[grade][t]
                    line_total = price * qty
                    total += line_total

                    if grade == "mr" and t == 3 and qty < 10:
                        reply_lines.append(f"MR plywood {t}mm @ ${price}/pcs (MOQ 10pcs)")
                        reply_lines.append("⚠ MOQ not met\n")
                    else:
                        reply_lines.append(f"{grade.upper()} plywood {t}mm @ ${price}/pcs x {qty} = ${line_total}")

                    timber_data.setdefault("Plywood", []).append([
                        f"{t}mm",
                        grade.upper(),
                        "-",
                        "-",
                        price,
                        qty,
                        line_total
                    ])

    # ================= OUTPUT =================
    st.subheader("🧠 Internal View")
    for k, v in timber_data.items():
        st.markdown(f"### {k}")
        st.table([["Input", "Std", "$/ton", "pcs/ton", "$/pcs", "Qty", "Total"]] + v)

    st.subheader("📩 Customer Reply")

    reply_lines.append(f"\nTotal: ${total}\n")

    if has_timber:
        reply_lines.append("tolerance +-1~2mm")
        reply_lines.append("tolerance length +-25~50mm\n")

    reply_lines.append("Delivery / Self Collection:")
    reply_lines.append("30 Krani Loop (Blk A) #04-05")
    reply_lines.append("TimMac @ Kranji S739570")
    reply_lines.append("Self collect: 9:30–11am / 1:30–4pm")
    reply_lines.append("Closed Sat, Sun & PH")

    final_reply = "\n".join(reply_lines)

    st.text_area("Reply (Copy)", final_reply, height=300)
    st.download_button("📋 Copy", final_reply)