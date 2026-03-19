import streamlit as st
import math
import re

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V10")

# ================= INPUT =================
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

# ================= DATA =================
inch_to_mm = {1:20, 2:43, 3:70, 4:93, 6:143, 8:193, 12:293}

plywood_prices = {
    "mr": {3:4.5, 6:9.9, 9:15, 12:21.5, 15:28, 18:31}
}

# ================= FUNCTIONS =================
def mm_to_inch(mm):
    for k,v in inch_to_mm.items():
        if abs(mm-v) <=5:
            return k
    return max(round(mm/25.4),1)

def calc(thk,wid,len,rate):
    pcs = max(math.floor(7200/thk/wid/len),1)
    return pcs, round(rate/pcs)

def clean(text):
    text = text.lower()
    text = text.replace('"',' inch ')
    text = text.replace("'",' ft ')
    text = text.replace("feet",'ft')
    text = text.replace("mmx",'mm x')
    text = re.sub(r'\s+',' ',text)
    return text

def extract(text):
    pattern = r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft'
    return re.findall(pattern,text)

# ================= MAIN =================
if generate:

    lines = user_input.split("\n")
    reply = []
    total = 0
    current = None
    has_timber = False

    for line in lines:
        text = clean(line)

        if "kapur" in text:
            current=("Kapur",kapur_rate)
        elif "balau" in text:
            current=("Balau",balau_rate)
        elif "chengal" in text:
            current=("Chengal",chengal_rate)

        qty = 1
        q = re.findall(r'(\d+)\s*(pcs|nos|pieces|sheets?)',text)
        if q:
            qty=int(q[0][0])

        sizes = extract(text)

        for s in sizes:
            has_timber=True

            v1,u1,v2,u2,ft = s
            v1=int(v1); v2=int(v2); ft=int(ft)

            if u1=="mm":
                thk=mm_to_inch(v1)
            else:
                thk=v1 if v1<=12 else mm_to_inch(v1)

            if u2=="mm":
                wid=mm_to_inch(v2)
            else:
                wid=v2 if v2<=12 else mm_to_inch(v2)

            length=20 if ft==19 else ft

            pcs,price=calc(thk,wid,length,current[1])

            mm1=inch_to_mm.get(thk,thk*25)
            mm2=inch_to_mm.get(wid,wid*25)

            line_total=price*qty
            total+=line_total

            reply.append(f"{current[0]} timber (planed)")
            reply.append(f"{mm1}mm x {mm2}mm x {ft}ft @ ${price}/pcs x {qty} = ${line_total}\n")

        # plywood
        if "plywood" in text or "plywod" in text:
            t=re.findall(r'(\d+\.?\d*)mm',text)
            for x in t:
                t=int(float(x))
                if t in plywood_prices["mr"]:
                    price=plywood_prices["mr"][t]
                    line_total=price*qty
                    total+=line_total
                    reply.append(f"MR plywood {t}mm @ ${price}/pcs x {qty} = ${line_total}")

    reply.append(f"\nTotal: ${total}\n")

    if has_timber:
        reply.append("tolerance +-1~2mm")
        reply.append("tolerance length +-25~50mm\n")

    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Reply", "\n".join(reply), height=350)