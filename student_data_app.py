import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time
import pandas as pd
import zipfile
from datetime import datetime
import io
import streamlit.components.v1 as components


# Initialize session state variables if not already present
if 'scores' not in st.session_state:
    st.session_state.scores = []

if 'times' not in st.session_state:
    st.session_state.times = [0, 0, 0]

if 'curr_debt' not in st.session_state:
    st.session_state.curr_debt = 0

if 'token_count' not in st.session_state:
    st.session_state.token_count = [0, 0, 0]

# Back to front page resetting everything
reset_clicked = st.button("Back", help="Voltar a página anterior", key="reset_button")
if reset_clicked:
    keys_to_keep = {"poor_knowledge","selected_level","final_path","curr_debt","prompt_text", "questions_text", "choice_made", "student_prompt"}
    keys_to_delete = [key for key in st.session_state if key not in keys_to_keep]
    for key in keys_to_delete:
        del st.session_state[key]
    st.session_state.app_started = False
    st.rerun()
        
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    st.image("TrustyTutorsLight.png", use_container_width=True)
    

with col2:
    st.write("")  # Padding
    st.write("")
    st.title("Trusty Tutors")
        

EVALUATOR_AVATAR = "👨🏻‍💼"
TUTOR_AVATAR = "🧔🏻‍♂️"
STUDENT_AVATAR = "🧒"
USER_AVATAR = "👤"

eval_model = "gpt-4.1"
std_model = "gpt-4.1"
tut_model = "gpt-4.1"

client = OpenAI(
    api_key = st.secrets["openai"]["api_key"]  
)

model_dicts = {
    "gpt-4o":[2.5,5,20],        
    "gpt-4o-mini":[0.3,0.6,2.4],
    "gpt-4.1":[2.0,0.5,8],
    "gpt-4.1-mini":[0.4,0.1,1.6],
    "gpt-4.1-nano":[0.1,0.025,0.4]
}

def print_routine(role, text, avatar=None):
    if avatar != None:
        with st.chat_message(role,avatar=avatar ):
            st.write_stream(response_generator(text))
    else:
        with st.chat_message(role,avatar = USER_AVATAR):
            st.markdown(text)

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def chat_with_gpt():#ALTERAR AQUI
    msg = []
    msg.append({ "role": "system","content": p.prompt_avaliador})
    msg.extend(st.session_state.chat_log)
    try:
        response = client.chat.completions.create(
            model=eval_model,
            messages=msg
        )
        st.session_state.times[0]+=1
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Erro ao contactar o avaliador: {e}")
        if st.button("🔄 Tentar novamente"):
            st.rerun()
        st.stop()
        
def run_evaluator():
    st.session_state.response = chat_with_gpt()
    if ("SYSTEM" not in st.session_state.response) and ("TUTOR" not in st.session_state.response) and ("STUDENT" not in st.session_state.response):
        print_routine('assistant', re.sub(r'\[.*?\]', '',st.session_state.response).strip(), EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content': "Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    
    if "[USER]" in st.session_state.response: st.session_state.phase = "user"
    elif "[STUDENT]" in st.session_state.response: st.session_state.phase = "student"
    elif "[SYSTEM]" in st.session_state.response: st.session_state.phase = "system"
    elif "[TUTOR]" in st.session_state.response: st.session_state.phase = "tutor"
    else:
        st.warning("Erro na mensagem. Repita a mensagem anterior")
        st.session_state.phase = "user"

def recreate_session_log_from_csv(csv_path):
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    session_log = []
    for _, row in df.iterrows():
        remetente = row["Remetente"]
        mensagem = row["Mensagem"]
        content = f"{remetente}: {mensagem}"
        session_log.append({"role": "user", "content": content})
    return session_log

def recreate_chat_log_from_session_log(csv_path):
    df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    interaction_activated = False
    chat_log = []
    
    interaction = []
    for i, (_, row) in enumerate(df.iterrows()):
        if(i == len(df)-1):
            chat_log.append({"role": "assistant", "content": "[USER] Agora que já testei o conhecimento do aluno, podemos passar para a fase seguinte, onde irei avaliar o desempenho do Tutor de acordo com métricas específicas?"})
            return chat_log
        
        remetente = row["Remetente"]
        mensagem = row["Mensagem"]
        if remetente.lower() == "avaliador":
            if (interaction_activated):
                tutor_interaction = "\n".join(interaction)
                chat_log.append({"role": "assistant", "content": tutor_interaction})
                interaction_activated = False
            if(mensagem.startswith("[STUDENT]")):
                chat_log.append({"role": "assistant", "content": mensagem})
            elif(mensagem.startswith("[TUTOR]")):
                chat_log.append({"role": "assistant", "content": mensagem})

        elif remetente.lower() == "estudante":
            if interaction_activated:
                interaction.append("Estudante: "+mensagem+"\n")
            else:
                chat_log.append({"role": "user", "content": mensagem})
                
        elif remetente.lower() == "tutor":
            interaction_activated = True
            interaction.append("Tutor: "+mensagem+"\n")
            
    return chat_log

if "page_ready" not in st.session_state:
    st.session_state.page_ready = True
    st.rerun()
     
# Display chat messages from history on app rerun
if "initialized" in st.session_state:
    for message in st.session_state.session_log:
        if message["content"].lower().startswith("estudante"):
            with st.chat_message(message["role"],avatar=STUDENT_AVATAR):
                st.markdown(message["content"].removeprefix("Estudante: "))
        elif message["content"].lower().startswith("tutor"):
            with st.chat_message(message["role"],avatar=TUTOR_AVATAR):
                st.markdown(message["content"].removeprefix("Tutor: "))
        if message["content"].lower().startswith("avaliador"):
            if (("SYSTEM" not in message["content"]) and ("TUTOR" not in message["content"])):                
                with st.chat_message(message["role"],avatar=EVALUATOR_AVATAR):
                    st.markdown(re.sub(r'\[.*?\]', '', message["content"].removeprefix("Avaliador: ")).strip())
        elif message["content"].lower().startswith("utilizador"):
            with st.chat_message(message["role"],avatar=USER_AVATAR):
                st.markdown(message["content"].removeprefix("Utilizador: "))

                                      
#Initialize Session Variables
if "initialized" not in st.session_state:
    #Memory Logs
    st.session_state.session_log = []
    st.session_state.chat_log = []
    st.session_state.tutor_log = []
    st.session_state.student_log = []
    st.session_state.refresh_memory = False
    st.session_state.button_pressed = False
    #Specific stage logs
    st.session_state.student_part = True
    st.session_state.QUIZ = False
    st.session_state.fQUIZ = False
    st.session_state.restart = False
    st.session_state.position_block = False
    st.session_state.tutor_state = [True, False]
    st.session_state.first_quiz = []
    st.session_state.interaction = []
    st.session_state.begining_pos = [0,0,0]     # for chat_log, student_log and session_log checkpoints
    #History track Parameters
    st.session_state.scores = []
    st.session_state.times = [0,0,0]
    st.session_state.curr_debt = 0  
    st.session_state.token_count = [0,0,0]
    
    try:
        #Single run task
        intro = client.chat.completions.create(
            model=eval_model,
            messages=[{"role": "system", "content": p.prompt_avaliador}]
        )
        st.session_state.response = intro.choices[0].message.content.strip()
        st.session_state.times[0] += 1
        print_routine('assistant',re.sub(r'\[.*?\]', '',st.session_state.response).strip(), EVALUATOR_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
        st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
        st.session_state.initialized = True
        st.session_state.phase = "user"
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao inicializar o avaliador: {e}")
        st.warning("Não foi possível contactar o modelo de avaliação.")
        if st.button("🔄 Tentar novamente"):
            st.rerun()
        st.stop()

#STUDENT   
if st.session_state.phase == "student": 
        st.session_state.chat_log.pop()
        st.session_state.session_log.pop()
        st.session_state.chat_log.extend(recreate_chat_log_from_session_log(st.session_state.csv_path))
        st.rerun()      
#SYSTEM
elif st.session_state.phase == "system":
    if "metrics" in st.session_state.response.lower():
        try:
            with open("metrics.txt", "r", encoding="utf-8") as file:
                prompt_metrics = file.read()
        except FileNotFoundError:
            st.error("Erro: O ficheiro 'metrics.txt' não foi encontrado.")
            st.stop()
        st.session_state.chat_log.append({'role': 'user', 'content': prompt_metrics})
        
        #EVALUATOR
        run_evaluator()   
        st.rerun() 
    elif "prompt" in st.session_state.response.lower():#prompt
        st.session_state.chat_log.append({'role': 'user', 'content': st.session_state.prompt_text})
        st.session_state.session_log.append({
            'role': 'assistant',
            'content': (
                "Avaliador: ---------------🎯 **Melhoria do Tutor** 🎯---------------\n\n"
                )
        })        
        
        #EVALUATOR
        run_evaluator()
        st.rerun()
    else:#Scores
        match = re.search(r'Scores\s+\[([^\]]+)\]', st.session_state.response)
        if match:
            parts = match.group(1).split(';')
            parts[5]=parts[5].replace(',','.')
            try:
                scores = list(map(int, parts[:5])) + [float(parts[5])]
                entry = [st.session_state.prompt_text] + scores
                if 'scores' not in st.session_state:
                    st.session_state.scores = []
                st.session_state.scores.append(entry)
            except (ValueError, IndexError):
                st.warning("⚠️ Failed to parse score values correctly.")
            
            #EVALUATOR
            st.session_state.chat_log.append({'role': 'user', 'content': "Correctly Saved"})
            run_evaluator()
            st.rerun()
        else:
            st.warning("⚠️ No valid score pattern found in the input text.")

elif st.session_state.phase == "user": 
    if "[END]" in  st.session_state.response:
        st.session_state.phase = "end"
    user_input = st.chat_input("Resposta")
    if user_input is None:
        st.stop() 
    print_routine('user',user_input)
    st.session_state.session_log.append({'role': 'user', 'content':"Utilizador: " + user_input})
    st.session_state.chat_log.append({'role': 'user', 'content': user_input})
    
    
    #EVALUATOR
    run_evaluator()
    st.rerun()

elif st.session_state.phase == "end":
    zip_file, zip_name = generate_zip_bytes()
    
    if "clicked" not in st.session_state:
        st.session_state.clicked = False
        
    st.success("✅ Sessão finalizada. Carrega no botão abaixo:")
    if(st.download_button(
        label="⬇️ Logs da Sessão",
        data=zip_file,
        file_name=zip_name,
        mime="application/zip"
    )): st.session_state.clicked = True
        
    if st.session_state.clicked == True:
        keys_to_delete = [key for key in st.session_state]
        for key in keys_to_delete:
            del st.session_state[key]
        #exec(open("cover.py").read())
        st.rerun()