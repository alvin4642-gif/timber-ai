import streamlit as st
import pandas as pd
import math
import re

st.set_page_config(layout="wide")
st.title("🪵 Timber AI Assistant V22")

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
    kapur_rate = st.number_input("Kapur", value=3800)

with c2:
    balau_rate = st.number_input("Balau", value=5500)

with c3:
    chengal_rate = st.number_input("Chengal", value=6000)

with c4:
    mixed_keruing_rate = st.number_input("Mixed Keruing", value=650)

with c5:
    pure_keruing_rate = st.number_input("Pure Keruing", value=1000)

user_input = ""

# =========================
# MODE 1 TEXT INPUT
# =========================
if mode == "Customer Enquiry (Text Input)":

    user_input = st.text_area(
        "📥 Paste Customer Enquiry",
        height=200
    )

# =========================
# MODE 2 TABLE INPUT
# =========================
if mode == "Manual Timber & Plywood Table":

    st.subheader("🪵 Timber Table")

    timber_df = pd.DataFrame([{
        "Timber Species": "Kapur",
        "Thickness": 93,
        "Thickness Unit": "mm",
        "Width": 43,
        "Width Unit": "mm",
        "Length": 3,
        "Length Unit": "m",
        "Quantity": 10
    }])

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
                options=["ft", "m"]
            )
        }
    )

    st.subheader("📦 Plywood Table")

    plywood_df = pd.DataFrame([{
        "Plywood Type": "Marine",
        "Thickness (mm)": 12,
        "Quantity": 10
    }])

    plywood_table = st.data_editor(
        plywood_df,
        num_rows="dynamic",
        use_container_width=True,
        key="plywood_table",
        column_config={
            "Plywood Type": st.column_config.SelectboxColumn(
                "Plywood Type",
                options=[
                    "Marine",
                    "Furniture",
                    "MR"
                ]
            )
        }
    )

    # Convert table to V21 text format
    lines = []

    for _, row in timber_table.iterrows():

        if pd.isna(row["Quantity"]):
            continue

        species = str(row["Timber Species"]).lower()

        t = int(row["Thickness"])
        tu = row["Thickness Unit"]

        w = int(row["Width"])
        wu = row["Width Unit"]

        l = float(row["Length"])
        lu = row["Length Unit"]

        qty = int(row["Quantity"])

        # length conversion
        if lu == "m":

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

        line = f"{species} {t}{tu} x {w}{wu} x {l_ft}ft {qty}pcs"

        lines.append(line)

    for _, row in plywood_table.iterrows():

        if pd.isna(row["Quantity"]):
            continue

        grade = str(row["Plywood Type"]).lower()
        thk = int(row["Thickness (mm)"])
        qty = int(row["Quantity"])

        line = f"{grade} plywood {thk}mm {qty}pcs"

        lines.append(line)

    user_input = "\n".join(lines)

# =========================
# BUTTONS
# =========================
b1, b2 = st.columns(2)

generate = b1.button("🚀 Generate")
refresh = b2.button("🔄 Refresh")

if refresh:
    reset_all()

# =========================
# V21 CALC ENGINE
# =========================
if generate and user_input:

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

    def detect_species(line):

        if "kapur" in line:
            return ("Kapur", kapur_rate, "planed")

        if "balau" in line:
            return ("Balau", balau_rate, "planed")

        if "chengal" in line:
            return ("Chengal", chengal_rate, "planed")

        if "mixed keruing" in line:
            return ("Mixed Keruing", mixed_keruing_rate, "sawn")

        if "pure keruing" in line:
            return ("Pure Keruing", pure_keruing_rate, "sawn")

        return None

    plywood_prices = {

        "marine": {
            6: 27,
            9: 37,
            12: 45,
            15: 57,
            18: 68,
            25: 96
        },

        "furniture": {
            3: 16,
            6: 17,
            9: 19,
            12: 24,
            15: 27,
            18: 32,
            25: 52
        },

        "mr": {
            3: 4.5,
            6: 9.9,
            9: 15,
            12: 21.5,
            15: 28,
            18: 31
        }
    }

    reply = []
    internal = []
    total = 0
    current_species = None

    lines = user_input.lower().split("\n")

    for line in lines:

        if not line:
            continue

        sp = detect_species(line)

        if sp:
            current_species = sp

        qty_match = re.findall(r'(\d+)\s*(pcs)', line)

        qty = int(qty_match[0][0]) if qty_match else 1

        size_match = re.findall(
            r'(\d+)(mm|inch)?\s*x\s*(\d+)(mm|inch)?\s*x\s*(\d+)ft',
            line
        )

        if size_match and current_species:

            for s in size_match:

                v1, u1, v2, u2, ft = s

                v1 = int(v1)
                v2 = int(v2)
                ft = int(ft)

                thk = mm_to_inch(v1) if u1 == "mm" else v1
                wid = mm_to_inch(v2) if u2 == "mm" else v2

                pcs_per_ton, pcs, price = calc(
                    thk,
                    wid,
                    ft,
                    current_species[1]
                )

                mm1 = inch_to_mm.get(thk, thk * 25)
                mm2 = inch_to_mm.get(wid, wid * 25)

                line_total = price * qty
                total += line_total

                if current_species[2] == "sawn":

                    size_text = f'{thk}"x{wid}"x{ft}ft'

                else:

                    size_text = f"{mm1}mm x {mm2}mm x {ft}ft"

                reply.append(
                    f"{current_species[0]} timber"
                )

                reply.append(
                    f"{size_text} @ ${price:.2f}/pcs x {qty} = ${line_total:.2f}\n"
                )

                internal.append(
                    f"{current_species[0]} | {thk}x{wid}x{ft}ft | pcs/ton {pcs_per_ton} | ${price}/pcs"
                )

        for grade in plywood_prices:

            if grade in line:

                thk_list = re.findall(r'(\d+)mm', line)

                for t in thk_list:

                    thickness = int(t)

                    if thickness in plywood_prices[grade]:

                        price = plywood_prices[grade][thickness]

                        line_total = price * qty

                        total += line_total

                        reply.append(
                            f"{grade.upper()} plywood {thickness}mm @ ${price}/pcs x {qty} = ${line_total}"
                        )

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