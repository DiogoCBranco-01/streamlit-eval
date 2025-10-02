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
if "poor_knowledge" not in st.session_state:
    st.session_state.poor_knowledge = ""
if "stage" not in st.session_state:
    st.session_state.stage = ""
    
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

        - 👨🏻‍💼 **Diretor/Formador Alfredo (AI)**
        - 🧔🏻‍♂️ **Tutor Estagiário João (AI)**
        - 🧒 **Aluno Pedro (AI)**
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
        🔁 **No final, o objetivo passa por repetir o processo, voltando à fase 2 para testar o novo e melhorado Tutor João!**  
            Ideal para experimentar antes de aplicar em sala de aula.
        """)
        st.write("")
        
        with open("questions.txt", "r", encoding="utf-8") as f:
            question_examples = f.read()
        
        with open("Q1.txt", "r", encoding="utf-8") as f:
            question_pt = f.read()
        
        with open("Q2.txt", "r", encoding="utf-8") as f:
            question_em = f.read()

        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_example = f.read()
            
        st.markdown("### Primeiros passos")
        st.markdown("""
        **1-** Verifique o formato das **questões** que foi usado no desenvolvimento da app e, de seguida, insira as questões que aparecerão no questionário.
        """)

        # Check student questions
        with st.expander("Ler um formato de questões possível"):
            st.text_area("",value="------------------------\nPergunta 1: ....?\nResposta Ideal: ...\nPontuações:\n\t-O aluno referiu isto. (2 pontos)\n\t-O aluno referiu aquilo. (3 pontos)\nPontuação total: (5 pontos)\n------------------------\nPergunta 2: ...?\n...\n------------------------\n\n Pontuação Final: Soma das pontuações totais de cada pergunta - (0.5 por cada erro ortográfico cometido)", height=200,key="questions_example", disabled=True)
        
        # Edit questions
        with st.expander("📋 Escrever questões"):
            st.session_state.questions_text = st.text_area("", value=st.session_state.questions_text, height=200)
        
        
        col1, col2, col3 = st.columns([2, 5, 0.5])
        with col2:    
            st.markdown("""
                **Pré-preencher** as questões com:
            """)
            
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        with col2:
            if st.button("📖 Português 4º ano"):
                st.session_state.questions_text = question_pt
                st.rerun()
        with col3:
            if st.button("🍃 Estudo do Meio 4º ano"):
                st.session_state.questions_text = question_em
                st.rerun()
                
        st.write("") 
        st.write("")
        st.write("") 
        st.write("")  
        st.markdown(""" 
        **2-** Insira a **prompt**/**instrução** que irá configurar o seu Tutor.
        """)    
        
        # Edit prompt
        with st.expander("🎓 Escrever prompt do tutor"):
            st.session_state.prompt_text = st.text_area("(ex: És um tutor do 4º ano, não deves dar as respostas diretamente, ...)", value=st.session_state.prompt_text, height=300)

        col1, col2, col3 = st.columns([2, 5, 0.5])
        with col2:    
            st.markdown("""
                **Pré-preencher** a prompt com:
            """)
            
            
        col1, col2, col3 = st.columns([1.4, 2, 1])
        with col2:
            if st.button("֎ Instrução Avançada"):
                st.session_state.prompt_text = p.prompt_tutor
                st.rerun()
            
        st.write("") 
        st.write("")
        st.write("") 
        st.write("")
        
        st.markdown(""" 
        **3-** Por fim escolha o **nível do Aluno AI** que pretende para a experiência. 
        """)
           
        
        # Radio options (with a placeholder)
        options = ["Nível 1", "Nível 2", "Nível 3"]

        # Set index based on previously selected level
        if st.session_state.selected_level is None:
            default_index = 0
        else:
            default_index = options.index(f"Nível {st.session_state.selected_level}")

        selected_option = st.radio(
            label="🧒 Escolher nível do Pedro",
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
        
        if selected_level == 3:
            with st.expander("Escrever matéria/s que aluno não deverá saber (opcional)"):
                st.session_state.poor_knowledge = st.text_area("Garante a existência de **pelo menos** uma **matéria** onde o aluno terá **dificuldades**. (ex.: Graus dos adjetivos)", value=st.session_state.poor_knowledge, height=200,key="prompt_poor_knowledge_display", disabled=False)
            if st.session_state.poor_knowledge.strip():
                st.session_state.student_prompt =  p.prompt_estudante + f" Nível {selected_level}" + " e ainda não aprendeu nada sobre " + "**" + st.session_state.poor_knowledge + "**" + ", mantendo o **resto do seu conhecimento compatível com o nível atribuído**."

        
        # Check student prompt
        with st.expander("Instrução do Pedro"):
            st.text_area("Prompt do aluno", value=st.session_state.student_prompt, height=200,key="prompt_estudante_display", disabled=True)
                    
        # Check if both fields are filled
        questions_ready = bool(st.session_state.questions_text.strip())
        prompt_ready = bool(st.session_state.prompt_text.strip())
        if( not bool(st.session_state.student_prompt.strip())): student_ready = False
        st.write("")
        st.write("")
        st.write("")
        
        # Start app (enabled only if both are written)
        col1, col2, col3, col4 = st.columns([1.4, 2, 1, 1])
        with col1:
            if st.button("🚀 Começar", disabled=not (questions_ready and prompt_ready and student_ready)):
                st.session_state.stage = "normal"
                st.session_state.app_started = True
        '''
        with col2:
            if st.button("Começar exp0", disabled=not (questions_ready and prompt_ready and student_ready)):
                st.session_state.stage = "exp0"
                st.session_state.app_started = True
        with col3:
            if st.button("Começar exp1", disabled=not (questions_ready and prompt_ready and student_ready)):
                st.session_state.stage = "exp1"
                st.session_state.app_started = True
        with col4:
            if st.button("Começar exp2", disabled=not (questions_ready and prompt_ready and student_ready)):
                st.session_state.stage = "exp2"
                st.session_state.app_started = True
        '''
        
        if st.session_state.app_started and not st.session_state.get("already_restarted", False):
            st.session_state.already_restarted = True  # To prevent rerunning infinitely
            placeholder.empty()
            st.rerun()

# ---------- App ----------
else:
    #st.warning("Here it is: " + st.session_state.stage)
    if st.session_state.stage == "exp0":
        exec(open("extract_log_tutor_1.py").read())
    elif st.session_state.stage == "exp1":
        exec(open("extract_log_tutor_2.py").read())  
    elif st.session_state.stage == "exp2":
        exec(open("extract_log_tutor_3.py").read())
    elif st.session_state.stage == "normal":
        exec(open("app.py").read())
