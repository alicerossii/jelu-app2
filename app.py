
import streamlit as st
import pandas as pd
import asyncio
import os
from estrattore_contatti import main as estrattore_main
from postino import extract_text_from_homepage, generate_email_with_gemini, invia_email, process_csv

st.set_page_config(layout="wide")
st.title("📬 Automazione JELU: da Excel all'email ✨")

file = st.file_uploader("📎 Carica il file Excel con le aziende", type=["xls"])

if "mittente" not in st.session_state:
    st.session_state["mittente"] = ""
if "password" not in st.session_state:
    st.session_state["password"] = ""

st.session_state["mittente"] = st.text_input("📤 Email del mittente", st.session_state["mittente"])
st.session_state["password"] = st.text_input("🔐 Password dell'app", type="password", value=st.session_state["password"])

if file:
    try:
        if os.path.exists("risultati.csv"):
            os.remove("risultati.csv")

        df = pd.read_excel(file, sheet_name="Risultati", usecols=["Ragione sociale"])
        aziende = df["Ragione sociale"].dropna().unique().tolist()
        st.success(f"✅ {len(aziende)} aziende caricate correttamente.")

        temp_file = "aziende_temp.csv"
        pd.DataFrame(aziende, columns=["Azienda"]).to_csv(temp_file, index=False)

        if st.button("🚀 Estrai contatti"):
            st.info("⏳ Estrazione in corso...")
            asyncio.run(estrattore_main(csv_path=temp_file))
            st.success("✅ Estrazione completata. File generato: risultati.csv")

        if os.path.exists("risultati.csv"):
            df_result = pd.read_csv("risultati.csv")
            st.session_state["df_result"] = df_result

            if "Azienda" in df_result.columns and "Sito" in df_result.columns and "Email" in df_result.columns:
                st.subheader("📨 Email generate automaticamente (modificabili)")

                emails_da_inviare = []

                for i, row in df_result.iterrows():
                    azienda = row["Azienda"]
                    email = row["Email"]
                    sito = row["Sito"]

                    if pd.isna(email) or not str(sito).startswith("http"):
                        continue

                    text = extract_text_from_homepage(sito)
                    corpo_email = generate_email_with_gemini(azienda, text) if text else ""

                    with st.expander(f"📩 {azienda} ({email})"):
                        invia = st.checkbox(f"Invia a {azienda}", key=f"invia_{i}", value=True)
                        subject = st.text_input("Oggetto", value="Proposta di collaborazione con JELU Consulting", key=f"subject_{i}")
                        corpo = st.text_area("Corpo dell'email", value=corpo_email, height=200, key=f"body_{i}")

                        if invia:
                            emails_da_inviare.append({
                                "azienda": azienda,
                                "email": email,
                                "subject": subject,
                                "body": corpo
                            })

                if emails_da_inviare and st.button("📨 Invia Email Selezionate"):
                    mittente = st.session_state.get("mittente", "")
                    password = st.session_state.get("password", "")

                    for email in emails_da_inviare:
                        success = invia_email(
                            mittente,
                            password,
                            email["email"],
                            email["subject"],
                            email["body"]
                        )
                        if success:
                            st.success(f"✅ Email inviata a {email['azienda']}")
                        else:
                            st.error(f"❌ Errore invio a {email['azienda']}")
    except Exception as e:
        st.error(f"❌ Errore durante la lettura del file: {e}")
else:
    st.info("Carica un file Excel per iniziare.")
