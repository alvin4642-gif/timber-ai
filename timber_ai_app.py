import streamlit as st
import re
import math

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V15")

# ================= INPUT =================
user_input = st.text_area("📥 Customer Enquiry", height=200)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    balau_rate = st.number_input("Balau $/ton", value=5500)
with col2:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)
with col3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)
with col4:
    mixed_keruing_rate = st.number_input("Mixed Keruing $/ton", value=650)
with col5:
    pure_keruing_rate = st.number_input("Pure Keruing $/ton", value=1000)

colA, colB = st.columns(2)
generate = colA.button("🚀 Generate")
refresh = colB.button("🔄 Refresh")

if refresh:
    st.rerun()

# ================= DATA =================
inch_to_mm = {1:20,2:43,3:70,4:93,6:143,8:193,12:293}

plywood_prices = {
    "marine": {6:27,9:37,12:45,15:57,18:68,25:96},
    "furniture": {3:16,6:17,9:19,12:24,15:27,18:32,25:52},
    "mr": {3:4.5,6:9.9,9:15,12:21.5,15:28,18:31}
}

def mm_to_inch(mm):
    for k,v in inch_to_mm.items():
        if abs(mm-v)<=5:
            return k
    return max(round(mm/25.4),1)

def calc(thk,wid,length,rate):
    raw = 7200/(thk*wid*length)
    pcs_per_ton = round(raw,3)
    pcs = max(math.floor(raw),1)
    price = round(rate/pcs,2)
    return pcs_per_ton, pcs, price

# ================= MAIN =================
if generate:

    text = user_input.lower()
    text = text.replace('"',' inch ')
    text = text.replace("'",' ft ')
    text = text.replace("feet",'ft')
    text = text.replace("mmx",'mm x')
    text = re.sub(r'(\d)ft(\d)', r'\1ft \2', text)
    text = re.sub(r'\s+', ' ', text)

    # 🔥 split by comma / line
    items = re.split(r',|\n', text)

    reply = []
    internal = []
    total = 0
    has_timber = False

    # ================= PROCESS EACH ITEM =================
    for item in items:
        item = item.strip()
        if not item:
            continue

        # 🔥 detect species PER ITEM
        if "kapur" in item:
            species=("Kapur", kapur_rate)
        elif "balau" in item:
            species=("Balau", balau_rate)
        elif "chengal" in item:
            species=("Chengal", chengal_rate)
        elif "mixed keruing" in item:
            species=("Mixed Keruing", mixed_keruing_rate)
        elif "pure keruing" in item:
            species=("Pure Keruing", pure_keruing_rate)
        else:
            species=None

        qty_match = re.findall(r'(\d+)\s*(pcs|nos|pieces)', item)
        qty = int(qty_match[0][0]) if qty_match else 1

        # ================= TIMBER =================
        sizes = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft', item)

        if sizes and species:
            has_timber = True

            for s in sizes:
                v1,u1,v2,u2,ft = s
                v1=int(v1); v2=int(v2); ft=int(ft)

                thk = mm_to_inch(v1) if u1=="mm" else (v1 if v1<=12 else mm_to_inch(v1))
                wid = mm_to_inch(v2) if u2=="mm" else (v2 if v2<=12 else mm_to_inch(v2))

                length = 20 if ft==19 else ft

                pcs_per_ton, pcs, price = calc(thk,wid,length,species[1])

                mm1 = inch_to_mm.get(thk, thk*25)
                mm2 = inch_to_mm.get(wid, wid*25)

                line_total = price * qty
                total += line_total

                # customer reply
                reply.append(f"{species[0]} timber (planed)")
                reply.append(f"{mm1}mm x {mm2}mm x {ft}ft @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}\n")

                # 🔥 clean internal format
                internal.append(f"{species[0]} | {thk}x{wid}x{length}ft | Pcs/Ton: {pcs_per_ton} | ${price:.2f}/pcs")

        # ================= PLYWOOD =================
        if "mm" in item:
            thk_list = re.findall(r'(\d+\.?\d*)mm', item)

            for t in thk_list:
                thickness = int(float(t))

                if "marine" in item:
                    grade="marine"
                elif "mr" in item or "floor" in item:
                    grade="mr"
                elif "plywood" in item:
                    grade="furniture"
                else:
                    continue

                if thickness in plywood_prices[grade]:

                    price = plywood_prices[grade][thickness]
                    line_total = price * qty
                    total += line_total

                    reply.append(f"{grade.upper()} plywood {thickness}mm @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}")

    # ================= OUTPUT =================
    st.text_area("🧠 Internal View (Check)", "\n".join(internal), height=200)

    reply.append(f"\nTotal: ${total:.2f}\n")

    if has_timber:
        reply.append("tolerance +-1~2mm")
        reply.append("tolerance length +-25~50mm\n")

    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Customer Reply", "\n".join(reply), height=300)