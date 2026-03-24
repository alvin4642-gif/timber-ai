
import streamlit as st
import re
import math
import pandas as pd

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V22")

# -----------------------------
# INPUT MODE
# -----------------------------
mode = st.radio(
    "Select Input Mode",
    ["Customer Enquiry (Text Input)", "Manual Timber Table"],
    horizontal=True
)

# -----------------------------
# V21 RATES
# -----------------------------
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

# -----------------------------
# MODE 1 - TEXT INPUT
# -----------------------------
user_input = ""

if mode == "Customer Enquiry (Text Input)":
    user_input = st.text_area("📥 Customer Enquiry", height=200)

# -----------------------------
# MODE 2 - TABLE INPUT
# -----------------------------
if mode == "Manual Timber Table":

    st.subheader("🪵 Timber Entry")

    timber_df = pd.DataFrame([
        {
            "Timber Species": "Kapur",
            "Thickness": "",
            "Thickness Unit": "inch",
            "Width": "",
            "Width Unit": "inch",
            "Length": "",
            "Length Unit": "ft",
            "Quantity": ""
        }
    ])

    timber_table = st.data_editor(
        timber_df,
        num_rows="dynamic",
        use_container_width=True,
        key="timber_table"
    )

    st.subheader("📦 Plywood Entry")

    plywood_df = pd.DataFrame([
        {
            "Plywood Type": "Marine",
            "Thickness (mm)": "",
            "Quantity": ""
        }
    ])

    plywood_table = st.data_editor(
        plywood_df,
        num_rows="dynamic",
        use_container_width=True,
        key="plywood_table"
    )

    # convert table to text
    lines = []

    for _, row in timber_table.iterrows():
        if row["Thickness"] and row["Width"] and row["Length"] and row["Quantity"]:
            species = row["Timber Species"].lower()
            t = row["Thickness"]
            w = row["Width"]
            l = row["Length"]
            unit_l = row["Length Unit"]

            if unit_l == "m":
                l = f"{l}m"
            else:
                l = f"{l}ft"

            line = f"{species} {t}x{w}x{l} {int(row['Quantity'])}pcs"
            lines.append(line)

    for _, row in plywood_table.iterrows():
        if row["Thickness (mm)"] and row["Quantity"]:
            grade = row["Plywood Type"].lower()
            thk = row["Thickness (mm)"]
            qty = row["Quantity"]

            line = f"{grade} plywood {thk}mm {int(qty)}pcs"
            lines.append(line)

    user_input = "\n".join(lines)

# -----------------------------
# BUTTONS
# -----------------------------
colA, colB = st.columns(2)
generate = colA.button("🚀 Generate")
refresh = colB.button("🔄 Refresh")

if refresh:
    st.rerun()

# -----------------------------
# V21 ENGINE (UNCHANGED)
# -----------------------------
if generate and user_input:

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

    def detect_species(line):
        if "kapur" in line:
            return ("Kapur", kapur_rate, "planed")
        if "balau" in line:
            return ("Balau", balau_rate, "planed")
        if "chengal" in line:
            return ("Chengal", chengal_rate, "planed")
        if "mixed hardwood" in line or "mixed keruing" in line:
            return ("Mixed Keruing", mixed_keruing_rate, "sawn")
        if "pure keruing" in line:
            return ("Pure Keruing", pure_keruing_rate, "sawn")
        return None

    plywood_prices = {
        "marine": {6:27,9:37,12:45,15:57,18:68,25:96},
        "mr": {3:4.5,6:9.9,9:15,12:21.5,15:28,18:31},
        "furniture": {3:16,6:17,9:19,12:24,15:27,18:32,25:52}
    }

    def detect_ply(line):
        if "marine" in line:
            return "marine"
        if "mr" in line:
            return "mr"
        if "plywood" in line:
            return "furniture"
        return None

    lines = user_input.lower().split("\n")

    reply = []
    internal = []
    total = 0
    current_species = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        sp = detect_species(line)
        if sp:
            current_species = sp

        qty_match = re.findall(r'(\d+)\s*(pcs|nos|pieces)', line)
        qty = int(qty_match[0][0]) if qty_match else 1

        sizes = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*ft', line)

        if sizes and current_species:
            for s in sizes:
                v1,u1,v2,u2,ft = s
                v1=int(v1); v2=int(v2); ft=int(ft)

                thk = mm_to_inch(v1) if u1=="mm" else v1
                wid = mm_to_inch(v2) if u2=="mm" else v2
                length = 20 if ft==19 else ft

                pcs_per_ton, pcs, price = calc(thk,wid,length,current_species[1])

                mm1 = inch_to_mm.get(thk, thk*25)
                mm2 = inch_to_mm.get(wid, wid*25)

                line_total = price * qty
                total += line_total

                if current_species[2] == "sawn":
                    size_text = f'{thk}"x{wid}"x{ft}ft'
                else:
                    size_text = f"{mm1}mm x {mm2}mm x {ft}ft"

                reply.append(f"{current_species[0]} timber ({current_species[2]})")
                reply.append(f"{size_text} @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}\n")

                internal.append(
                    f"{current_species[0]:<15} | {thk}x{wid}x{length}ft | Pcs/Ton: {pcs_per_ton:<8} | ${price:.2f}/pcs"
                )

        grade = detect_ply(line)
        thk_list = re.findall(r'(\d+\.?\d*)mm', line)

        if grade:
            for t in thk_list:
                thickness = int(float(t))

                if thickness in plywood_prices[grade]:
                    price = plywood_prices[grade][thickness]
                    line_total = price * qty
                    total += line_total

                    reply.append(f"{grade.upper()} plywood {thickness}mm @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}")

    st.text_area("🧠 Internal View", "\n".join(internal), height=200)

    reply.append(f"\nTotal: ${total:.2f}\n")
    reply.append("tolerance +-1~2mm")
    reply.append("tolerance length +-25~50mm\n")
    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Customer Reply", "\n".join(reply), height=300)
