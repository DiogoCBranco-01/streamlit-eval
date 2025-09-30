import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time
import base64

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

if "choice_made" not in st.session_state:
    st.session_state.choice_made = False
if "final_path" not in st.session_state:
    st.session_state.final_path = ""
if "path" not in st.session_state:
    st.session_state.path = ""
if "questions_text" not in st.session_state:
    st.session_state.questions_text = ""
if "student_number" not in st.session_state:
    st.session_state.student_number = ""

placeholder = st.empty()
# ---------- FRONT COVER ----------
if not st.session_state.choice_made:
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #fffff;
        color: dark grey;
        border: none;
        cursor: pointer;
        width: 70%;
        font-size: 40px !important;
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)
    with placeholder.container():
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
        
        col1, col2, col3 = st.columns([3, 3, 3])
        with col2:
            st.image("TrustyTutors.png", use_container_width=True)
        
        st.write("")
        st.markdown("<h2 style='text-align: center; font-size: 17px; font-weight: 300; font-family: Arial, sans-serif;'>Bem vindo! Seleciona a tua função para começar:</h2>", unsafe_allow_html=True)
        st.write("")
        col1, col2, col3, col4 = st.columns([0.5, 2, 0.5,2])
                      
        with col2:
            if st.button("Aluno"):
                st.session_state.choice_made = True
                st.session_state.path = "student"
                
        with col4:
            if st.button("Professor"):
                st.session_state.choice_made = True
                st.session_state.path = "user"
            
        st.write("")            
        
        if st.session_state.choice_made and not st.session_state.get("already_restarted0", False):
            st.session_state.already_restarted0 = True  # To prevent rerunning infinitely
            placeholder.empty()
            st.rerun()

# ---------- App ----------
else:
    if st.session_state.final_path == "":
        st.markdown("""
        <style>
        div.stButton > button {
            background-color: #fffff;
            color: dark grey;
            border: none;
            cursor: pointer;
            font-size: 40px !important; 
        }
        </style>
        """, unsafe_allow_html=True)
        with placeholder.container():
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
            
            col1, col2, col3 = st.columns([3, 3, 3])
            with col2:
                st.image("TrustyTutors.png", use_container_width=True)
            
            st.write("")
            st.markdown("<h2 style='text-align: center; font-size: 17px; font-weight: 300; font-family: Arial, sans-serif;'> Escolhe a opção que gostarias de experimentar:</h2>", unsafe_allow_html=True)
            st.write("")
                
            col1, col2, col3, col4 = st.columns([0.75, 2, 0.25,2])
            if st.session_state.path == "user":
                with col2:
                    if st.button("Dados simulados"):
                        st.session_state.final_path = "user1"
                        st.rerun()
                with col4:
                    if st.button("Dados reais"):
                        st.session_state.final_path = "user2"
                        st.rerun()

            elif st.session_state.path == "student":
                with col2:
                    if st.button("Português"):
                        st.session_state.choice_made = True
                        with open("Q1.txt", "r", encoding="utf-8") as f:
                            st.session_state.questions_text = f.read()
                        st.session_state.final_path = "student"
                        st.session_state.student_number = "PT"
                        st.rerun()
                with col4:
                    if st.button("Estudo do Meio"):
                        st.session_state.choice_made = True
                        with open("Q2.txt", "r", encoding="utf-8") as f:
                            st.session_state.questions_text = f.read()
                        st.session_state.final_path = "student"
                        st.session_state.student_number = "EM"
                        st.rerun()
            
            
            col1, col2, col3 = st.columns([2.5, 2, 1])
            with col2:
                reset_clicked = st.button("⟵", key="reset2_button")
                if reset_clicked:
                    keys_to_delete = [key for key in st.session_state]
                    for key in keys_to_delete:
                        del st.session_state[key]
                    st.session_state.already_restarted0 = True  # To prevent rerunning infinitely
                    placeholder.empty()      
                    st.rerun()
            
    elif st.session_state.final_path == "student":
        exec(open("student.py").read())
    elif st.session_state.final_path == "user1":
        exec(open("interface.py").read())
    elif st.session_state.final_path == "user2":
        exec(open("interface_std_data.py").read())
