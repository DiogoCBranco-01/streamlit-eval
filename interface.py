import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time

if "app_started" not in st.session_state:
    st.session_state.app_started = False
if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = ""
if "student_prompt" not in st.session_state:
    st.session_state.student_prompt = p.prompt_estudante
if "selected_level" not in st.session_state:
    st.session_state.selected_level = None

placeholder = st.empty()
student_ready = False
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

        - 🤖 **Avaliador AI**
        - 🧑‍🏫 **Tutor AI**
        - 🧒 **Estudante AI**
        - 👤 **Utilizador**
        """)
        st.write("")

        st.markdown("### Como funciona?")
        st.markdown("""
        Esta aplicação oferece um ambiente conversacional num ciclo de **5 fases sequenciais**:

        1. 🧾 **Questionário Inicial**  
        O Estudante AI responde a uma lista de perguntas sugerida pelo utilizador, onde será avaliado o seu conhecimento atual.

        2. 🎓 **Interação com o Tutor AI**  
        O Tutor AI tentará preparar melhor o Estudante AI, com base no conhecimento recolhido do questionário.

        3. 📋 **Questionário Final**  
        O Estudante AI responde novamente às mesmas perguntas, por forma a medir o seu progresso.

        4. 🧠 **Avaliação do Tutor**  
        O Avaliador AI reflete sobre o desempenho do Tutor AI com base em critérios objetivos. Nesta fase será possível conversar abertamente com o Avaliador.

        5. 🛠️ **Melhoria do Tutor**  
        O Avaliador AI analisa a prompt atual do Tutor e sugere melhorias. Esta será uma fase importante para intervir e acrescentar ideias.
        """)

        st.markdown("""
        🔁 **No final o objetivo passa por repetir o processo, voltando à fase 2 para avaliar o novo Tutor!**  
            Ideal para experimentar antes de aplicar em sala de aula.
        """)
        st.write("")
        
        with open("questions.txt", "r", encoding="utf-8") as f:
            question_examples = f.read()

        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_example = f.read()
            
        st.markdown("### Primeiros passos")
        st.markdown("""
        **1-** Podes verificar o formato das **questões** que foi usado no desenvolvimento da app e, de seguida, insere as questões que aparecerão no questionário.
        """)

        # Check student questions
        with st.expander("Ler exemplo de questões"):
            st.text_area("Formato das questões", value="------------------------\nPergunta 1: ....?\nResposta Ideal: ...\nCritérios de avaliação:\n\t-O aluno referiu isto. (2 pontos)\n\t-O aluno referiu aquilo. (3 pontos)\n\t(Total: 5 pontos)\n------------------------\nPergunta 2: ...?\n...\n------------------------\n\n Pontuação Total: X pontos", height=200,key="questions_example", disabled=True)
        
        # Edit questions
        with st.expander("📋 Escrever questões"):
            st.session_state.questions_text = st.text_area("", value=st.session_state.questions_text, height=200)
        
        
        col1, col2, col3 = st.columns([0.5, 5, 0.5])
        with col2:    
            st.markdown("""
                Podes fazer download das seguintes questões-tipo e copiá-las diretamente:
            """)
        col1, col2, col3 = st.columns([1.25, 2, 1])
        with col2:
            #Download questions
            st.download_button(
                label="📥 Download 'questions.txt'",
                data=question_examples,
                file_name="questions.txt",
                mime="text/plain"
            )
        
        st.write("") 
        st.write("")
        st.write("") 
        st.write("")  
        st.markdown(""" 
        **2-** Insere a **prompt**/**instrução** que irá configurar o teu Tutor.
        """)    
        
        # Edit prompt
        with st.expander("🎓 Escrever prompt do tutor"):
            st.session_state.prompt_text = st.text_area("(ex: És um tutor do 4º ano, não deves dar as respostas diretamente, ...)", value=st.session_state.prompt_text, height=300)

        col1, col2, col3 = st.columns([0.5, 5, 0.5])
        with col2:    
            st.markdown("""
                Podes fazer download da seguinte prompt-tipo e copiá-la diretamente:
            """)
        col1, col2, col3 = st.columns([1.25, 2, 1])
        with col2:
            #Download prompt
            st.download_button(
                label="📥 Download 'prompt.txt'",
                data=prompt_example,
                file_name="prompt.txt",
                mime="text/plain"
            )
            
        st.write("") 
        st.write("")
        st.write("") 
        st.write("")
        
        st.markdown(""" 
        **3-** Por fim escolhe o **nível do Estudante AI** que pretendes para a experiência. 
        Para melhor contextualização, é possível consultar a instrução dada ao Estudante AI.
        """)
        
        
        # Check student prompt
        with st.expander("Ler prompt do estudante"):
            st.text_area("Prompt do estudante", value=st.session_state.student_prompt, height=200,key="prompt_estudante_display", disabled=True)
           
        
        # Radio options (with a placeholder)
        options = ["Nível 1", "Nível 2", "Nível 3"]

        # Set index based on previously selected level
        if st.session_state.selected_level is None:
            default_index = 0
        else:
            default_index = options.index(f"Nível {st.session_state.selected_level}")

        selected_option = st.radio(
            label="🧒 Escolher nível do Estudante",
            options=options,
            index=default_index,
            horizontal=True
        )

        # Extract level number
        selected_level = int(selected_option.split(" ")[-1])
        if st.session_state.selected_level != selected_level:
            st.session_state.selected_level = selected_level
            st.session_state.student_prompt = p.prompt_estudante + f" Nível {selected_level}"
            st.rerun()
        st.success(f"{selected_option} selecionado!")  
        student_ready = True
                  
        # Check if both fields are filled
        questions_ready = bool(st.session_state.questions_text.strip())
        prompt_ready = bool(st.session_state.prompt_text.strip())
        if( not bool(st.session_state.student_prompt.strip())): student_ready = False
        st.write("")
        st.write("")
        st.write("")
        
        # Start app (enabled only if both are written)
        if st.button("🚀 Começar", disabled=not (questions_ready and prompt_ready and student_ready)):
            st.session_state.app_started = True
        if st.session_state.app_started and not st.session_state.get("already_restarted", False):
            st.session_state.already_restarted = True  # To prevent rerunning infinitely
            placeholder.empty()
            st.rerun()

# ---------- App ----------
else:
    exec(open("app.py").read())
