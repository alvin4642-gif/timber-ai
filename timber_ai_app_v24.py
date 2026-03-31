import streamlit as st
import pandas as pd
import re
import math

# ==============================
# PAGE
# ==============================
st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V24")

# ==============================
# RESET
# ==============================
def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

# ==============================
# MODE
# ==============================
mode = st.radio(
    "Select Mode",
    ["Customer Enquiry", "Manual Table"],
    horizontal=True
)

# ==============================
# RATES
# ==============================
st.subheader("Rates ($/ton)")

kapur_rate = st.number_input("Kapur", value=3800)
balau_rate = st.number_input("Balau", value=5500)
chengal_rate = st.number_input("Chengal", value=6000)
mixed_keruing_rate = st.number_input("Mixed Keruing", value=650)
pure_keruing_rate = st.number_input("Pure Keruing", value=1000)

# ==============================
# CONSTANTS
# ==============================
inch_to_mm = {
    1:20,
    2:43,
    3:70,
    4:93,
    6:143,
    8:193,
    12:293
}

plywood_prices = {
    "Marine": {
        6:25.5,
        9:37.0,
        12:45,
        15:56,
        18:68.5,
        25:95
    },
    "Furniture": {
        3:15,
        6:17.5,
        9:19.5,
        12:23.8,
        15:26.8,
        18:31.5,
        25:45
    },
    "MR": {
        3:4.1,
        6:6.8,
        9:10.5,
        12:15,
        15:19.5,
        18:21.7
    }
}

species_rate = {
    "Kapur": kapur_rate,
    "Balau": balau_rate,
    "Chengal": chengal_rate,
    "Mixed Keruing": mixed_keruing_rate,
    "Pure Keruing": pure_keruing_rate
}

# ==============================
# FUNCTIONS
# ==============================
def mm_to_inch(mm):
    for inch, val in inch_to_mm.items():
        if abs(mm - val) <= 5:
            return inch
    return max(round(mm/25.4),1)

def m_to_ft(m):
    if m <= 2.4:
        return 8
    elif m <= 3:
        return 10
    else:
        return round(m * 3.28)

def calc(thk, wid, length, rate):
    raw = 7200 / (thk * wid * length)
    pcs_per_ton = round(raw, 3)
    pcs = max(math.floor(raw),1)
    price = round(rate / pcs, 2)
    return pcs_per_ton, pcs, price

def is_keruing(species):
    return species in ["Mixed Keruing", "Pure Keruing"]

# ==============================
# FORM
# ==============================
with st.form("main_form"):

    if mode == "Customer Enquiry":
        enquiry = st.text_area("Customer Enquiry", height=200)

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
                "Species": st.column_config.SelectboxColumn(
                    options=["Kapur","Balau","Chengal","Mixed Keruing","Pure Keruing"]
                ),
                "T Unit": st.column_config.SelectboxColumn(
                    options=["mm","inch"]
                ),
                "W Unit": st.column_config.SelectboxColumn(
                    options=["mm","inch"]
                ),
                "L Unit": st.column_config.SelectboxColumn(
                    options=["m","ft"]
                )
            }
        )

        st.subheader("Plywood Table")

        plywood_df = pd.DataFrame([{
            "Type":"Marine",
            "Thickness":None,
            "Qty":None
        }])

        plywood_table = st.data_editor(
            plywood_df,
            num_rows="dynamic",
            use_container_width=True,
            key="plywood",
            column_config={
                "Type": st.column_config.SelectboxColumn(
                    options=["Marine","Furniture","MR"]
                )
            }
        )

    colA, colB = st.columns(2)
    generate = colA.form_submit_button("Generate")
    refresh = colB.form_submit_button("Refresh")

# ==============================
# ACTIONS
# ==============================
if refresh:
    reset_all()

# ==============================
# ENGINE
# ==============================
if generate:

    internal_view = []
    customer_reply = []
    grand_total = 0

    # ------------------------------
    # CUSTOMER ENQUIRY (TIMBER ONLY)
    # ------------------------------
    if mode == "Customer Enquiry":

        lines = enquiry.lower().split("\n")
        current_species = None

        for line in lines:

            if "kapur" in line:
                current_species = "Kapur"
            elif "balau" in line:
                current_species = "Balau"
            elif "chengal" in line:
                current_species = "Chengal"
            elif "mixed" in line:
                current_species = "Mixed Keruing"
            elif "pure keruing" in line:
                current_species = "Pure Keruing"

            if not current_species:
                continue

            qty_match = re.findall(r'(\d+)\s*(pcs|nos|pieces)', line)
            qty = int(qty_match[0][0]) if qty_match else 1

            size_match = re.findall(
                r'(\d+)\s*(mm|inch)?\s*x\s*(\d+)\s*(mm|inch)?\s*x\s*(\d+\.?\d*)\s*(m|ft)',
                line
            )

            for s in size_match:

                v1,u1,v2,u2,v3,u3 = s

                v1 = int(v1)
                v2 = int(v2)
                v3 = float(v3)

                thk = mm_to_inch(v1) if u1 == "mm" else v1
                wid = mm_to_inch(v2) if u2 == "mm" else v2
                length = m_to_ft(v3) if u3 == "m" else int(v3)

                if length == 19:
                    length = 20

                rate = species_rate[current_species]

                pcs_per_ton, pcs, price = calc(thk, wid, length, rate)

                if is_keruing(current_species):
                    size_text = f'{thk}" x {wid}" x {length}ft'
                else:
                    size_text = f"{inch_to_mm.get(thk, thk*25)}mm x {inch_to_mm.get(wid, wid*25)}mm x {length}ft"

                line_total = round(price * qty, 2)
                grand_total += line_total

                internal_view.append(
f"""{current_species} timber
{size_text}

$/ton : {rate}
pcs/ton : {pcs_per_ton}
$/pcs : {price}

Qty : {qty}
Total : ${line_total}

------------------------"""
                )

                customer_reply.append(
f"""{current_species} timber
{size_text} @ ${price}/pcs x {qty} = ${line_total}
"""
                )

    # ------------------------------
    # MANUAL TABLE
    # ------------------------------
    if mode == "Manual Table":

        for _, row in timber_table.iterrows():

            if pd.isna(row["Thickness"]) or pd.isna(row["Width"]) or pd.isna(row["Length"]) or pd.isna(row["Qty"]):
                continue

            species = row["Species"]

            t = int(row["Thickness"])
            w = int(row["Width"])
            l = float(row["Length"])
            qty = int(row["Qty"])

            thk = mm_to_inch(t) if row["T Unit"] == "mm" else t
            wid = mm_to_inch(w) if row["W Unit"] == "mm" else w
            length = m_to_ft(l) if row["L Unit"] == "m" else int(l)

            if length == 19:
                length = 20

            rate = species_rate[species]

            pcs_per_ton, pcs, price = calc(thk, wid, length, rate)

            if is_keruing(species):
                size_text = f'{thk}" x {wid}" x {length}ft'
            else:
                size_text = f"{inch_to_mm.get(thk, thk*25)}mm x {inch_to_mm.get(wid, wid*25)}mm x {length}ft"

            line_total = round(price * qty, 2)
            grand_total += line_total

            internal_view.append(
f"""{species} timber
{size_text}

$/ton : {rate}
pcs/ton : {pcs_per_ton}
$/pcs : {price}

Qty : {qty}
Total : ${line_total}

------------------------"""
            )

            customer_reply.append(
f"""{species} timber
{size_text} @ ${price}/pcs x {qty} = ${line_total}
"""
            )

        # PLYWOOD (MANUAL ONLY)
        for _, row in plywood_table.iterrows():

            if pd.isna(row["Thickness"]) or pd.isna(row["Qty"]):
                continue

            grade = row["Type"]
            thk = int(row["Thickness"])
            qty = int(row["Qty"])

            if grade == "MR" and thk == 3 and qty < 10:
                qty = 10

            if thk not in plywood_prices[grade]:
                continue

            price = plywood_prices[grade][thk]
            line_total = round(price * qty, 2)
            grand_total += line_total

            internal_view.append(
f"""{grade} plywood
{thk}mm

$/pcs : {price}

Qty : {qty}
Total : ${line_total}

------------------------"""
            )

            customer_reply.append(
f"""{grade} plywood {thk}mm @ ${price}/pcs x {qty} = ${line_total}"""
            )

    st.text_area("Internal View", "\n\n".join(internal_view), height=350)

    customer_reply.append(f"\nTotal : ${round(grand_total,2)}")
    customer_reply.append("\ntolerance +-1~2mm")
    customer_reply.append("tolerance length +-25~50mm")
    customer_reply.append("\nDelivery / Self Collection:")
    customer_reply.append("30 Krani Loop (Blk A) #04-05")
    customer_reply.append("TimMac @ Kranji S739570")

    st.text_area("Customer Reply", "\n".join(customer_reply), height=350)
