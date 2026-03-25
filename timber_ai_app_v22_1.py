import streamlit as st
import pandas as pd
import re
import math

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V22.2")

# =========================
# RESET
# =========================
def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# =========================
# MODE
# =========================
mode = st.radio(
    "Select Mode",
    ["Customer Enquiry", "Manual Table"],
    horizontal=True
)

# =========================
# RATES
# =========================
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    balau_rate = st.number_input("Balau $/ton", value=5500)
with c2:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)
with c3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)
with c4:
    mixed_keruing_rate = st.number_input("Mixed Keruing $/ton", value=650)
with c5:
    pure_keruing_rate = st.number_input("Pure Keruing $/ton", value=1000)

# =========================
# CONSTANTS
# =========================
inch_to_mm = {1:20,2:43,3:70,4:93,6:143,8:193}
plywood_prices = {
    "Marine": {6:27,9:37,12:45,15:57,18:68,25:96},
    "Furniture": {3:16,6:17,9:19,12:24,15:27,18:32,25:52},
    "MR": {3:4.5,6:9.9,9:15,12:21.5,15:28,18:31}
}

def mm_to_inch(mm):
    for k,v in inch_to_mm.items():
        if abs(mm-v)<=5:
            return k
    return max(round(mm/25.4),1)

def m_to_ft(m):
    if m <= 2.4:
        return 8
    elif m <= 3:
        return 10
    return round(m * 3.28)

def calc(thk,wid,length,rate):
    raw = 7200/(thk*wid*length)
    pcs_per_ton = round(raw,3)
    pcs = max(math.floor(raw),1)
    price = round(rate/pcs,2)
    return pcs_per_ton, pcs, price

def is_keruing(species):
    return species in ["Mixed Keruing","Pure Keruing"]

# =========================
# INPUT MODE 1
# =========================
if mode == "Customer Enquiry":
    user_input = st.text_area("📥 Customer Enquiry", height=200)

# =========================
# INPUT MODE 2
# =========================
if mode == "Manual Table":

    st.subheader("Timber Table")

    timber_df = pd.DataFrame([{
        "Species":"Kapur",
        "Thickness":None,
        "T Unit":"mm",
        "Width":None,
        "W Unit":"mm",
        "Length":None,
        "L Unit":"m",
        "Qty":None
    }])

    timber_table = st.data_editor(
        timber_df,
        num_rows="dynamic",
        use_container_width=True,
        key="timber",
        column_config={
            "Species": st.column_config.SelectboxColumn(options=["Kapur","Balau","Chengal","Mixed Keruing","Pure Keruing"]),
            "T Unit": st.column_config.SelectboxColumn(options=["mm","inch"]),
            "W Unit": st.column_config.SelectboxColumn(options=["mm","inch"]),
            "L Unit": st.column_config.SelectboxColumn(options=["m","ft"])
        }
    )

    st.subheader("Plywood Table")

    ply_df = pd.DataFrame([{
        "Type":"Marine",
        "Thickness":None,
        "Qty":None
    }])

    plywood_table = st.data_editor(
        ply_df,
        num_rows="dynamic",
        use_container_width=True,
        key="plywood",
        column_config={
            "Type": st.column_config.SelectboxColumn(options=["Marine","Furniture","MR"])
        }
    )

# =========================
# BUTTONS
# =========================
cA, cB = st.columns(2)
generate = cA.button("🚀 Generate")
refresh = cB.button("🔄 Refresh")

if refresh:
    reset_all()

# =========================
# ENGINE
# =========================
if generate:

    internal = []
    reply = []
    total = 0

    # =========================
    # TEXT MODE (V21 upgraded)
    # =========================
    if mode == "Customer Enquiry":

        lines = user_input.lower().split("\n")
        current_species = None

        def detect_species(line):
            if "kapur" in line: return ("Kapur",kapur_rate)
            if "balau" in line: return ("Balau",balau_rate)
            if "chengal" in line: return ("Chengal",chengal_rate)
            if "mixed" in line: return ("Mixed Keruing",mixed_keruing_rate)
            if "pure keruing" in line: return ("Pure Keruing",pure_keruing_rate)
            return None

        for line in lines:
            if not line.strip(): continue

            sp = detect_species(line)
            if sp:
                current_species = sp

            qty_match = re.findall(r'(\d+)\s*(pcs|nos|pieces)', line)
            qty = int(qty_match[0][0]) if qty_match else 1

            sizes = re.findall(r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+\.?\d*)\s*(ft|m)', line)

            for s in sizes:
                v1,u1,v2,u2,v3,u3 = s
                v1=int(v1); v2=int(v2); v3=float(v3)

                thk = mm_to_inch(v1) if u1=="mm" else v1
                wid = mm_to_inch(v2) if u2=="mm" else v2
                length = m_to_ft(v3) if u3=="m" else int(v3)
                if length==19: length=20

                pcs_per_ton, pcs, price = calc(thk,wid,length,current_species[1])

                if is_keruing(current_species[0]):
                    size_text = f'{thk}" x {wid}" x {length}ft'
                else:
                    size_text = f"{inch_to_mm.get(thk,thk*25)}mm x {inch_to_mm.get(wid,wid*25)}mm x {length}ft"

                line_total = round(price*qty,2)
                total += line_total

                internal.append(
                    f"{current_species[0]} | {size_text}\npcs/ton {pcs_per_ton}\n${current_species[1]}/ton\n${price}/pcs\nQty {qty}\nTotal ${line_total}\n----------------------"
                )

                reply.append(
                    f"{current_species[0]} timber\n{size_text} @ ${price}/pcs x {qty} = ${line_total}\n"
                )

    # =========================
    # TABLE MODE
    # =========================
    if mode == "Manual Table":

        for _,row in timber_table.iterrows():

            if pd.isna(row["Thickness"]) or pd.isna(row["Width"]) or pd.isna(row["Length"]) or pd.isna(row["Qty"]):
                continue

            species = row["Species"]
            t = int(row["Thickness"])
            w = int(row["Width"])
            l = float(row["Length"])
            qty = int(row["Qty"])

            thk = mm_to_inch(t) if row["T Unit"]=="mm" else t
            wid = mm_to_inch(w) if row["W Unit"]=="mm" else w
            length = m_to_ft(l) if row["L Unit"]=="m" else int(l)
            if length==19: length=20

            rate = {
                "Kapur":kapur_rate,
                "Balau":balau_rate,
                "Chengal":chengal_rate,
                "Mixed Keruing":mixed_keruing_rate,
                "Pure Keruing":pure_keruing_rate
            }[species]

            pcs_per_ton, pcs, price = calc(thk,wid,length,rate)

            if is_keruing(species):
                size_text = f'{thk}" x {wid}" x {length}ft'
            else:
                size_text = f"{inch_to_mm.get(thk,thk*25)}mm x {inch_to_mm.get(wid,wid*25)}mm x {length}ft"

            line_total = round(price*qty,2)
            total += line_total

            internal.append(
                f"{species} | {size_text}\npcs/ton {pcs_per_ton}\n${rate}/ton\n${price}/pcs\nQty {qty}\nTotal ${line_total}\n----------------------"
            )

            reply.append(
                f"{species} timber\n{size_text} @ ${price}/pcs x {qty} = ${line_total}\n"
            )

        for _,row in plywood_table.iterrows():

            if pd.isna(row["Thickness"]) or pd.isna(row["Qty"]):
                continue

            grade = row["Type"]
            thk = int(row["Thickness"])
            qty = int(row["Qty"])

            if grade=="MR" and thk==3 and qty<10:
                qty=10
                note="Minimum order for MR 3mm is 10pcs"
            else:
                note=""

            if thk not in plywood_prices[grade]:
                continue

            price = plywood_prices[grade][thk]
            line_total = round(price*qty,2)
            total += line_total

            internal.append(
                f"{grade} plywood | {thk}mm\n${price}/pcs\nQty {qty}\nTotal ${line_total}\n----------------------"
            )

            reply.append(
                f"{grade} plywood {thk}mm @ ${price}/pcs x {qty} = ${line_total}"
            )

            if note:
                reply.append(note)

    # =========================
    # OUTPUT
    # =========================
    st.text_area("🧠 Internal View","\n\n".join(internal),height=300)

    reply.append(f"\nTotal: ${round(total,2)}")
    reply.append("\ntolerance +-1~2mm")
    reply.append("tolerance length +-25~50mm\n")
    reply.append("Delivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.text_area("📩 Customer Reply","\n".join(reply),height=350)