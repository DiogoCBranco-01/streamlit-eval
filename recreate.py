import streamlit as st
from openai import OpenAI
import prompts as p
import tiktoken
import time
import pandas as pd
import os
import zipfile
from datetime import datetime
import io
import re
import base64

#student_exp/session_log_santi_19_06_3PT.csv
#student_exp/session_log_santi_19_06_2.csv
#student_exp/session_log_santi_19_06_1.csv

#student_exp/session_log_goya_20_06.csv          - A
#student_exp/session_log_andre_20_06.csv         - B
#student_exp/session_log_beatriz_20_06.csv         .
#student_exp/session_log_francisca_20_06.csv       . 
#student_exp/session_log_ines_20_06.csv            .
#student_exp/session_log_luz_20_06.csv
#student_exp/session_log_mateus_20_06.csv
#student_exp/session_log_neville_20_06.csv
#student_exp/session_log_salvador_20_06.csv
#student_exp/session_log_salwa_23_06.csv
#student_exp/session_log_barbara_23_06.csv
#ines_E4
#student_exp/session_log_joaquim_23_06.csv
#student_exp/session_log_monica_23_06.csv
#student_exp/session_log_danish_23_06.csv

path = "student_exp/session_log_mateus_20_06.csv"
def recreate_session_log_from_csv(csv_path):
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    session_log = []
    for _, row in df.iterrows():
        remetente = row["Remetente"]
        mensagem = row["Mensagem"]
        content = f"{remetente}: {mensagem}"
        session_log.append({"role": "user", "content": content})
    return session_log
    
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img_base64 = get_base64_image("background.png")
st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
            
col1, col2, col3 = st.columns([2, 3, 2])
 
with col3:
    st.image("TrustyTutors.png", use_container_width=True)
        

EVALUATOR_AVATAR = "👨🏻‍💼"
TUTOR_AVATAR = "🧔🏻‍♂️"
STUDENT_AVATAR = "🙂" #"👤" #"🧒"


if "session_log" not in st.session_state:
    st.session_state.session_log = recreate_session_log_from_csv(path)
     
for message in st.session_state.session_log:
    if message["content"].lower().startswith("estudante"):
        content_html = (
            message["content"]
            .removeprefix("Estudante: ")
            .replace("\n", "<br>")
        )
        formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content_html)
        formatted_content = re.sub(r'__([A-Za-z0-9][^_]{0,})__', r'<u>\1</u>', formatted_content)
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-end; margin: 10px 0;'>
                <div style='background-color: #dcf8c6; padding: 10px 15px; border-radius: 10px; max-width: 60%;'>
                    {formatted_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )      
    elif message["content"].lower().startswith("tutor"):
        content_html = (
            message["content"]
            .removeprefix("Tutor: ")
            .replace("\n", "<br>")
        )
        formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content_html)
        formatted_content = re.sub(r'__([A-Za-z0-9][^_]{0,})__', r'<u>\1</u>', formatted_content)
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-start; align-items: center; margin: 10px 0;'>
                <div style='margin-right: 8px; font-size: 28px;'>{TUTOR_AVATAR}</div>
                <div style='background-color: #f1f0f0; padding: 10px 15px; border-radius: 10px; max-width: 60%;'>
                    {formatted_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    if message["content"].lower().startswith("avaliador"):
        if (("SYSTEM" not in message["content"]) and ("TUTOR" not in message["content"])):   
            cleaned_content = re.sub(r'\[.*?\]', '', message["content"].removeprefix("Avaliador: ")).strip()
            formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned_content)
            formatted_content = re.sub(r'__([A-Za-z0-9][^_]{0,})__', r'<u>\1</u>', formatted_content)
            st.markdown(
                f"""
                <div style='display: flex; justify-content: flex-start; align-items: center; margin: 10px 0;'>
                    <div style='margin-right: 8px; font-size: 28px;'>{EVALUATOR_AVATAR}</div>
                    <div style='background-color: #f1f0f0; padding: 10px 15px; border-radius: 10px; max-width: 60%;'>
                        {formatted_content}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
                                              
