import streamlit as st
import re
import math

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V19 (Production Stable)")

# INPUT
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

if st.button("🚀 Generate"):

    inch_to_mm = {1:20,2:43,3:70,4:93,6:143,8:193,12:293}

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

    # CLEAN TEXT
    text = user_input.lower()
    text = text.replace('"',' inch ')
    text = text.replace("'",' ft ')
    text = text.replace("feet",'ft')
    text = text.replace("mmx",'mm x')
    text = re.sub(r'\s+', ' ', text)

    # SPECIES LIST
    species_map = {
        "kapur": ("Kapur", kapur_rate),
        "balau": ("Balau", balau_rate),
        "chengal": ("Chengal", chengal_rate),
        "mixed hardwood": ("Mixed Keruing", mixed_keruing_rate),
        "mixed keruing": ("Mixed Keruing", mixed_keruing_rate),
        "pure keruing": ("Pure Keruing", pure_keruing_rate)
    }

    # FIND ALL TIMBER ITEMS
    timber_pattern = r'((?:kapur|balau|chengal|mixed hardwood|mixed keruing|pure keruing)?\s*\d+\s*(?:mm|inch)?\s*x\s*\d+\s*(?:mm|inch)?\s*x\s*\d+\s*ft\s*\d*\s*(?:pcs)?)'
    timber_items = re.findall(timber_pattern, text)

    reply = []
    internal = []
    total = 0

    for item in timber_items:

        # detect species
        sp = None
        for key in species_map:
            if key in item:
                sp = species_map[key]

        if not sp:
            continue

        qty_match = re.findall(r'(\d+)\s*pcs', item)
        qty = int(qty_match[0]) if qty_match else 1

        size = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft', item)

        if size:
            v1,u1,v2,u2,ft = size[0]
            v1=int(v1); v2=int(v2); ft=int(ft)

            thk = mm_to_inch(v1) if u1=="mm" else v1
            wid = mm_to_inch(v2) if u2=="mm" else v2
            length = 20 if ft==19 else ft

            pcs_per_ton, pcs, price = calc(thk,wid,length,sp[1])

            mm1 = inch_to_mm.get(thk, thk*25)
            mm2 = inch_to_mm.get(wid, wid*25)

            line_total = price * qty
            total += line_total

            reply.append(f"{sp[0]} timber (planed)")
            reply.append(f"{mm1}mm x {mm2}mm x {ft}ft @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}\n")

            internal.append(f"{sp[0]} | {thk}x{wid}x{length}ft | Pcs/Ton: {pcs_per_ton} | ${price:.2f}/pcs")

    # ===== PLYWOOD =====
    plywood_prices = {
        "marine": {6:27,9:37,12:45,15:57,18:68,25:96},
        "mr": {3:4.5,6:9.9,9:15,12:21.5,15:28,18:31},
        "furniture": {3:16,6:17,9:19,12:24,15:27,18:32,25:52}
    }

    ply_pattern = r'(marine|mr|plywood)[^\d]*(\d+)\s*mm\s*(\d*)\s*(pcs)?'
    ply_items = re.findall(ply_pattern, text)

    for g,t,q,_ in ply_items:
        thickness = int(t)
        qty = int(q) if q else 1

        grade = "mr" if g=="mr" else ("marine" if g=="marine" else "furniture")

        if thickness in plywood_prices[grade]:
            price = plywood_prices[grade][thickness]
            line_total = price * qty
            total += line_total

            reply.append(f"{grade.upper()} plywood {thickness}mm @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}")

    # OUTPUT
    st.text_area("🧠 Internal View", "\n".join(internal), height=200)

    reply.append(f"\nTotal: ${total:.2f}\n")
    reply.append("tolerance +-1~2mm")
    reply.append("tolerance length +-25~50mm\n")
    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Customer Reply", "\n".join(reply), height=300)