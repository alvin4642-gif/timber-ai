import streamlit as st
import pandas as pd
import math
import re

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V22.1")

# =========================
# RESET FUNCTION
# =========================
def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# =========================
# MODE
# =========================
mode = st.radio(
    "Select Input Mode",
    ["Customer Enquiry (Text Input)", "Manual Timber & Plywood Table"],
    horizontal=True
)

# =========================
# RATES
# =========================
st.subheader("💰 Timber $/Ton Rate")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    kapur_rate = st.number_input("Kapur $/ton", value=3800)

with c2:
    balau_rate = st.number_input("Balau $/ton", value=5500)

with c3:
    chengal_rate = st.number_input("Chengal $/ton", value=6000)

with c4:
    mixed_keruing_rate = st.number_input("Mixed Keruing $/ton", value=650)

with c5:
    pure_keruing_rate = st.number_input("Pure Keruing $/ton", value=1000)

user_input = ""

# =========================
# MODE 1
# =========================
if mode == "Customer Enquiry (Text Input)":

    user_input = st.text_area(
        "📥 Paste Customer Enquiry",
        height=200
    )

# =========================
# MODE 2
# =========================
if mode == "Manual Timber & Plywood Table":

    st.subheader("🪵 Timber Table")

    timber_df = pd.DataFrame([
        {
            "Timber Species": "Kapur",
            "Thickness": None,
            "Thickness Unit": "mm",
            "Width": None,
            "Width Unit": "mm",
            "Length": None,
            "Length Unit": "m",
            "Quantity": None
        }
    ])

    timber_table = st.data_editor(
        timber_df,
        num_rows="dynamic",
        use_container_width=True,
        key="timber_table",
        column_config={
            "Timber Species": st.column_config.SelectboxColumn(
                "Timber Species",
                options=[
                    "Kapur",
                    "Chengal",
                    "Balau",
                    "Mixed Keruing",
                    "Pure Keruing"
                ]
            ),
            "Thickness Unit": st.column_config.SelectboxColumn(
                "Thickness Unit",
                options=["mm", "inch"]
            ),
            "Width Unit": st.column_config.SelectboxColumn(
                "Width Unit",
                options=["mm", "inch"]
            ),
            "Length Unit": st.column_config.SelectboxColumn(
                "Length Unit",
                options=["m", "ft"]
            )
        }
    )

    st.subheader("📦 Plywood Table")

    plywood_df = pd.DataFrame([
        {
            "Plywood Type": "Marine",
            "Thickness (mm)": None,
            "Quantity": None
        }
    ])

    plywood_table = st.data_editor(
        plywood_df,
        num_rows="dynamic",
        use_container_width=True,
        key="plywood_table",
        column_config={
            "Plywood Type": st.column_config.SelectboxColumn(
                "Plywood Type",
                options=["Marine", "Furniture", "MR"]
            )
        }
    )

# =========================
# BUTTONS
# =========================
b1, b2 = st.columns(2)

generate = b1.button("🚀 Generate")
refresh = b2.button("🔄 Refresh")

if refresh:
    reset_all()

# =========================
# CALCULATION ENGINE
# =========================
if generate:

    inch_to_mm = {
        1: 20,
        2: 43,
        3: 70,
        4: 93,
        6: 143,
        8: 193
    }

    def mm_to_inch(mm):

        for inch, val in inch_to_mm.items():

            if abs(mm - val) <= 5:
                return inch

        return max(round(mm / 25.4), 1)

    def calc(thk, wid, length, rate):

        raw = 7200 / (thk * wid * length)

        pcs_per_ton = round(raw, 3)

        pcs = max(math.floor(raw), 1)

        price = round(rate / pcs, 2)

        return pcs_per_ton, pcs, price

    plywood_prices = {

        "Marine": {
            6: 27,
            9: 37,
            12: 45,
            15: 57,
            18: 68,
            25: 96
        },

        "Furniture": {
            3: 16,
            6: 17,
            9: 19,
            12: 24,
            15: 27,
            18: 32,
            25: 52
        },

        "MR": {
            3: 4.5,
            6: 9.9,
            9: 15,
            12: 21.5,
            15: 28,
            18: 31
        }
    }

    internal = []
    reply = []
    total = 0

    # =========================
    # TABLE MODE
    # =========================
    if mode == "Manual Timber & Plywood Table":

        for _, row in timber_table.iterrows():

            species = row["Timber Species"]
            t = row["Thickness"]
            w = row["Width"]
            l = row["Length"]
            qty = row["Quantity"]

            if pd.isna(t) or pd.isna(w) or pd.isna(l) or pd.isna(qty):

                internal.append(
                    f"⚠ {species} | Missing data"
                )

                continue

            t_unit = row["Thickness Unit"]
            w_unit = row["Width Unit"]
            l_unit = row["Length Unit"]

            t = int(t)
            w = int(w)
            l = float(l)
            qty = int(qty)

            if l_unit == "m":

                if l <= 2.4:
                    l_ft = 8

                elif l <= 3:
                    l_ft = 10

                else:
                    l_ft = round(l * 3.28)

            else:
                l_ft = int(l)

            if l_ft == 19:
                l_ft = 20

            thk = mm_to_inch(t) if t_unit == "mm" else t
            wid = mm_to_inch(w) if w_unit == "mm" else w

            rate = {
                "Kapur": kapur_rate,
                "Balau": balau_rate,
                "Chengal": chengal_rate,
                "Mixed Keruing": mixed_keruing_rate,
                "Pure Keruing": pure_keruing_rate
            }[species]

            pcs_per_ton, pcs, price = calc(thk, wid, l_ft, rate)

            mm1 = inch_to_mm.get(thk, thk * 25)
            mm2 = inch_to_mm.get(wid, wid * 25)

            line_total = price * qty
            total += line_total

            internal.append(
                f"{species} | {mm1}mm x {mm2}mm x {l_ft}ft | pcs/ton {pcs_per_ton} | ${rate}/ton | ${price}/pcs | Qty {qty} | Total ${line_total}"
            )

            reply.append(
                f"{species} timber\n{mm1}mm x {mm2}mm x {l_ft}ft @ ${price}/pcs x {qty} = ${line_total}\n"
            )

        for _, row in plywood_table.iterrows():

            grade = row["Plywood Type"]
            thk = row["Thickness (mm)"]
            qty = row["Quantity"]

            if pd.isna(thk) or pd.isna(qty):

                internal.append(
                    f"⚠ {grade} plywood | Missing data"
                )

                continue

            thk = int(thk)
            qty = int(qty)

            if thk not in plywood_prices[grade]:
                continue

            price = plywood_prices[grade][thk]

            line_total = price * qty
            total += line_total

            internal.append(
                f"{grade} plywood | {thk}mm | ${price}/pcs | Qty {qty} | Total ${line_total}"
            )

            reply.append(
                f"{grade} plywood {thk}mm @ ${price}/pcs x {qty} = ${line_total}"
            )

    # =========================
    # OUTPUT
    # =========================
    st.subheader("🧠 Internal View")

    st.text_area(
        "",
        "\n".join(internal),
        height=200
    )

    reply.append(f"\nTotal: ${total}")
    reply.append("\ntolerance +-1~2mm")
    reply.append("tolerance length +-25~50mm")
    reply.append("\nDelivery / Self Collection:")
    reply.append("30 Krani Loop (Blk A) #04-05")
    reply.append("TimMac @ Kranji S739570")

    st.subheader("📩 Customer Reply")

    st.text_area(
        "",
        "\n".join(reply),
        height=300
    )