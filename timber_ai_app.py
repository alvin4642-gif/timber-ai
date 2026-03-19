import streamlit as st
import re
import math

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V11 (Full System)")

# ================= INPUT =================
user_input = st.text_area("📥 Customer Enquiry", height=200)

col1, col2, col3 = st.columns(3)
with col1:
    balau_rate = st.number_input("Balau $/ton", value=5500)
with col2:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)
with col3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)

if st.button("🚀 Generate"):

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

    def calc(thk,wid,len,rate):
        pcs = max(math.floor(7200/thk/wid/len),1)
        return pcs, round(rate/pcs)

    # ================= CLEAN INPUT =================
    text = user_input.lower()
    text = text.replace('"',' inch ')
    text = text.replace("'",' ft ')
    text = text.replace("feet",'ft')
    text = text.replace("mmx",'mm x')
    text = re.sub(r'(\d)ft(\d)', r'\1ft \2', text)   # FIX 10ft10pcs
    text = re.sub(r'\s+', ' ', text)

    # ================= SPLIT ITEMS =================
    items = re.split(r',| and |\n', text)

    reply = []
    total = 0
    current = None
    has_timber = False

    for item in items:
        item = item.strip()
        if not item:
            continue

        # detect species
        if "kapur" in item:
            current=("Kapur",kapur_rate)
        elif "balau" in item:
            current=("Balau",balau_rate)
        elif "chengal" in item:
            current=("Chengal",chengal_rate)

        # qty
        qty = 1
        q = re.findall(r'(\d+)\s*(pcs|nos|pieces|sheets?)', item)
        if q:
            qty = int(q[0][0])

        # ================= TIMBER =================
        size = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft', item)

        if size and current:
            has_timber = True

            for s in size:
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

        # ================= PLYWOOD =================
        if "plywood" in item or "plywod" in item:

            if "marine" in item:
                grade="marine"
            elif "mr" in item or "floor" in item:
                grade="mr"
            else:
                grade="furniture"

            t = re.findall(r'(\d+\.?\d*)mm', item)

            for x in t:
                t = int(float(x))
                if t in plywood_prices[grade]:

                    price = plywood_prices[grade][t]
                    line_total = price * qty
                    total += line_total

                    if grade=="mr" and t==3 and qty<10:
                        reply.append(f"MR plywood {t}mm @ ${price}/pcs (MOQ 10pcs)")
                        reply.append("⚠ MOQ not met\n")
                    else:
                        reply.append(f"{grade.upper()} plywood {t}mm @ ${price}/pcs x {qty} = ${line_total}")

    # ================= OUTPUT =================
    reply.append(f"\nTotal: ${total}\n")

    if has_timber:
        reply.append("tolerance +-1~2mm")
        reply.append("tolerance length +-25~50mm\n")

    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Reply", "\n".join(reply), height=350)