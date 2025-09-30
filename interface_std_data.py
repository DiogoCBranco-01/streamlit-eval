import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time
import pandas as pd


if "app_started" not in st.session_state:
    st.session_state.app_started = False
if "use_experiment" not in st.session_state:
    st.session_state.use_experiment = False
if "csv_path" not in st.session_state:    
    st.session_state.csv_path = ""
if "stage" not in st.session_state:
    st.session_state.stage = ""

placeholder = st.empty()
# ---------- FRONT COVER ----------
if not st.session_state.app_started:
    with placeholder.container():
        # Back to front page resetting everything
        reset_clicked = st.button("Voltar", help="Voltar a página anterior", key="reset1_button")
        if reset_clicked:
            keys_to_delete = [key for key in st.session_state]
            for key in keys_to_delete:
                del st.session_state[key]
            st.session_state.choice_made = False
            st.rerun()
            
        st.markdown( #efeff1
            """
            <style>
            [data-testid="stAppViewContainer"] {
                background-color: #efeff1; /* Light grey-blue background */
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns([2, 3, 1])
        with col3:
            st.image("TrustyTutors.png", use_container_width=True)

        with col1:
            st.write("")
            st.write("")
            st.write("")
            st.markdown("### Bem-vindo!")
            
        st.markdown("""
        **Trusty Tutors** é uma plataforma criada para **avaliar e melhorar o desempenho de Tutores AI** em contextos educativos reais.

        Sabemos que é crucial garantir que estas ferramentas agem de acordo com os critérios **pedagógicos** e **sociais** exigidos numa sala de aula. Por isso, esta aplicação oferece um ambiente controlado, mas realista, onde será possível testar e afinar o comportamento de um Tutor AI gerado através de prompts/instruções por texto.
        """)
        st.markdown("""
        A experiência contará com a atuação dos seguintes **participantes**:

        - 👨🏻‍💼 **Diretor/Formador Alfredo (AI)**
        - 🧔🏻‍♂️ **Tutor Estagiário João (AI)**
        - 🧒 **Aluno (H)**
        - 👤 **Utilizador (H)**
        """)
        st.write("")

        st.markdown("### Como funciona?")
        st.markdown("""
        Esta aplicação oferece um ambiente conversacional num ciclo de **5 fases sequenciais**:

        1. 🧾 **Questionário ao Aluno AI**  
        O aluno Pedro vai responder a uma lista de perguntas, onde será avaliado o seu conhecimento atual.

        2. 🎓 **Interação entre o Tutor AI e o Aluno AI**  
        O Tutor João tentará preparar melhor o Pedro, com base no conhecimento recolhido do questionário.

        3. 📋 **Repetição do Questionário ao Aluno AI**  
        O Pedro responderá novamente às mesmas perguntas, para ser possível medir o seu progresso.

        4. 🧠 **Avaliação do Tutor AI**  
        O Direto Alfredo refletirá sobre o desempenho do Tutor João com base em critérios objetivos. Nesta fase será possível conversar abertamente com o Diretor Alfredo.

        5. 🛠️ **Melhoria do Tutor AI**  
        O Diretor Alfredo irá analisar a instrução atual dada ao Tutor João e sugere melhorias. Esta será uma fase importante para intervir e acrescentar ideias.
        """)

        st.markdown("""
        🔁 **No final, como a análise do desempenho do Tutor acontece com alunos humanos, não podemos repetir a experiência para melhorar o Tutor.**  
            Ideal para teste unitário ao comportamento do Tutor com dados de alunos reais voluntários, antes de escalar para a turma toda!
        """)
        st.write("")            
            
        st.markdown("### Antes de Começar:")
        st.markdown("""
        **1-** Será necessário fazer o carregamento de um ficheiro "session_log.csv" gerado numa experiência com um aluno real.
        """)
        
        uploaded_file = st.file_uploader(
            label="Carregue ou arraste o seu ficheiro aqui",  # replaces "Drag and drop..."
            type=["csv"],
            help="Limite de 200 MB por ficheiro. Formatos permitidos: CSV"  # replaces hint text
        )
        if uploaded_file is not None:
            with open("temp.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.session_state.csv_path = os.path.abspath("temp.csv")
            st.success(f"✅ Ficheiro '{uploaded_file.name}' carregado com sucesso!")
            
        col1, col2, col3 = st.columns([2.8, 5, 0.5])
        with col2:    
            st.markdown("""
                Utilizar ficheiro real:
            """)
        
        col1, col2, col3 = st.columns([1.0, 2, 1])
        with col2:
            if st.button("🧒 Experiência com Estudante Real"):
                st.session_state.csv_path = "session_log_salwa_23_06.csv"
                st.rerun()
                
                
        st.write("") 
        st.write("")
        st.write("") 
        st.write("")  
                            
        # Check if both fields are filled
        student_data_ready = bool(st.session_state.csv_path.strip())
        st.write("")
        st.write("")
        st.write("")
        
        # Start app (enabled only if both are written)
        col1, col2, col3, col4 = st.columns([1.4, 2, 1, 1])
        with col1:
            if st.button("🚀 Começar", disabled=not (student_data_ready)):
                st.session_state.stage = "students"
                st.session_state.app_started = True
        
        if st.session_state.app_started and not st.session_state.get("already_restarted", False):
            st.session_state.already_restarted = True  # To prevent rerunning infinitely
            placeholder.empty()
            st.rerun()

# ---------- App ----------
else:
    #st.warning("Here it is: " + st.session_state.stage)
    if st.session_state.stage == "students":
        exec(open("student_data_app.py").read())
