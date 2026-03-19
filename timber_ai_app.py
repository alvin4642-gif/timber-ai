import streamlit as st
import re
import math

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V12 (No Missing Items)")

# INPUT
user_input = st.text_area("📥 Customer Enquiry", height=200)

col1, col2, col3 = st.columns(3)
with col1:
    balau_rate = st.number_input("Balau $/ton", value=5500)
with col2:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)
with col3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)

if st.button("🚀 Generate"):

    # DATA
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

    def calc(thk,wid,len,rate):
        pcs = max(math.floor(7200/thk/wid/len),1)
        return pcs, round(rate/pcs)

    # CLEAN TEXT
    text = user_input.lower()
    text = text.replace('"',' inch ')
    text = text.replace("'",' ft ')
    text = text.replace("feet",'ft')
    text = text.replace("mmx",'mm x')
    text = re.sub(r'(\d)ft(\d)', r'\1ft \2', text)
    text = re.sub(r'\s+', ' ', text)

    reply = []
    total = 0
    has_timber = False

    # ================= TIMBER SCAN =================
    current = None

    if "kapur" in text:
        current=("Kapur",kapur_rate)
    elif "balau" in text:
        current=("Balau",balau_rate)
    elif "chengal" in text:
        current=("Chengal",chengal_rate)

    timber_sizes = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft', text)
    qty_list = re.findall(r'(\d+)\s*(pcs|nos|pieces)', text)

    qty = int(qty_list[0][0]) if qty_list else 1

    for s in timber_sizes:
        has_timber = True

        v1,u1,v2,u2,ft = s
        v1=int(v1); v2=int(v2); ft=int(ft)

        thk = mm_to_inch(v1) if u1=="mm" else (v1 if v1<=12 else mm_to_inch(v1))
        wid = mm_to_inch(v2) if u2=="mm" else (v2 if v2<=12 else mm_to_inch(v2))

        length = 20 if ft==19 else ft

        pcs,price = calc(thk,wid,length,current[1])

        mm1 = inch_to_mm.get(thk, thk*25)
        mm2 = inch_to_mm.get(wid, wid*25)

        line_total = price * qty
        total += line_total

        reply.append(f"{current[0]} timber (planed)")
        reply.append(f"{mm1}mm x {mm2}mm x {ft}ft @ ${price}/pcs x {qty} = ${line_total}\n")

    # ================= PLYWOOD SCAN (SEPARATE) =================
    plywood_blocks = re.findall(r'(marine|mr|furniture)?\s*plywood\s*(\d+\.?\d*)mm\s*(\d+)?', text)

    for block in plywood_blocks:
        grade = block[0] if block[0] else "furniture"
        thickness = int(float(block[1]))
        qty = int(block[2]) if block[2] else 1

        if thickness in plywood_prices[grade]:

            price = plywood_prices[grade][thickness]
            line_total = price * qty
            total += line_total

            if grade=="mr" and thickness==3 and qty<10:
                reply.append(f"MR plywood {thickness}mm @ ${price}/pcs (MOQ 10pcs)")
                reply.append("⚠ MOQ not met\n")
            else:
                reply.append(f"{grade.upper()} plywood {thickness}mm @ ${price}/pcs x {qty} = ${line_total}")

    # OUTPUT
    reply.append(f"\nTotal: ${total}\n")

    if has_timber:
        reply.append("tolerance +-1~2mm")
        reply.append("tolerance length +-25~50mm\n")

    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Reply", "\n".join(reply), height=350)