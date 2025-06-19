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

with col1:
    # Back to front page resetting everything
    reset_clicked = st.button("⟵", help="Voltar a página anterior", key="reset_button")
    if reset_clicked:
        keys_to_keep = {"curr_debt", "choice_made"}
        keys_to_delete = [key for key in st.session_state if key not in keys_to_keep]
        for key in keys_to_delete:
            del st.session_state[key]
        st.session_state.choice_made = False
        st.rerun()
 
with col3:
    st.image("TrustyTutors.png", use_container_width=True)
    

#with col2:
#    st.write("")  # Padding
#    st.write("")
#    st.title("Trusty Tutors")
        

EVALUATOR_AVATAR = "👨🏻‍💼"
TUTOR_AVATAR = "🧔🏻‍♂️"
STUDENT_AVATAR = "🙂" #"👤" #"🧒"

eval_model = "gpt-4.1"
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


def create_log_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{st.session_state.student_number}_session_logs_{timestamp}"

def parse_log(log, roles):
    data = []
    for entry in log:
        for role in roles:
            if entry.startswith(role + ": "):
                remetente = role
                mensagem = entry.removeprefix(f"{role}: ").strip()
                data.append({"Remetente": remetente, "Mensagem": mensagem})
                break
    return pd.DataFrame(data)

def parse_log_dict(log):
    data = []
    for entry in log:
        content = entry.get("content", "")
        for role in ["Estudante", "Avaliador", "Tutor"]:
            if content.startswith(role + ": "):
                remetente = role
                mensagem = content.removeprefix(f"{role}: ").strip()
                data.append({"Remetente": remetente, "Mensagem": mensagem})
                break
    return pd.DataFrame(data)

def generate_zip_bytes():
    folder = create_log_folder()
    memory_zip = io.BytesIO()

    with zipfile.ZipFile(memory_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add CSVs directly to zip from memory
        dfs = {
            "interaction.csv": parse_log(st.session_state.interaction, ["Tutor", "Estudante"]),
            "first_quiz.csv": parse_log(st.session_state.first_quiz, ["Avaliador", "Estudante"]),
            "final_quiz.csv": parse_log(st.session_state.final_quiz, ["Avaliador", "Estudante"]),
            "session_log.csv": parse_log_dict(st.session_state.session_log),
        }

        # Create the costs.csv DataFrame
        costs_df = pd.DataFrame([{
            "debt": st.session_state.curr_debt if 'curr_debt' in st.session_state else 0,
            "eval_times": st.session_state.times[0] if 'times' in st.session_state else 0,
            "tutor_times": st.session_state.times[1] if 'times' in st.session_state else 0,
            "eval_tokens": st.session_state.token_count[0] if 'token_count' in st.session_state else 0,
            "tutor_tokens": st.session_state.token_count[1] if 'token_count' in st.session_state else 0
        }])

        # Add costs.csv to the dict
        dfs["costs.csv"] = costs_df
        
        for filename, df in dfs.items():
            csv_bytes = df.to_csv(index=False,sep=';').encode("utf-8")
            zipf.writestr(f"{folder}/{filename}", csv_bytes)

    memory_zip.seek(0)
    return memory_zip, f"{folder}.zip"

def print_routine(role, text, avatar=None):
    text = text.replace("\n", "<br>")
    formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    formatted_content = re.sub(r'__([A-Za-z0-9][^_]{0,})__', r'<u>\1</u>', formatted_content)
    if avatar == None:
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
    else:
        st.markdown(
            f"""
            <div style='display: flex; justify-content: flex-start; align-items: center; margin: 10px 0;'>
                <div style='margin-right: 8px; font-size: 28px;'>{avatar}</div>
                <div style='background-color: #f1f0f0; padding: 10px 15px; border-radius: 10px; max-width: 60%;'>
                    {formatted_content}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
          
    
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)
               
def tokens_price_update(model, choice=0): # 0-eval; 1-student; 2-tutor
    encoding = tiktoken.get_encoding("o200k_base")
    msg = [[], []]
    msg[0].append({ "role": "system","content": p.prompt_avaliador_light})
    msg[0].extend(st.session_state.chat_log)
    msg[1].append({ "role": "system","content": p.prompt_tutor})
    msg[1].extend(st.session_state.tutor_log)

    tokens = []
    for j in range(2):    
        total_tokens=0
        size = len(msg[j])
        for i,entry in enumerate(msg[j]):
            # Each message follows this format:
            tokens_round = 0
            tokens_round += 4  # Every message has some overhead in the OpenAI API
            tokens_round += len(encoding.encode(entry["role"]))
            tokens_round += len(encoding.encode(entry["content"]))
            if j == choice:
                if i < size-3: st.session_state.curr_debt += tokens_round * model_dicts[model][0] / 1000000 #cache price
                elif i < size-1: st.session_state.curr_debt += tokens_round * model_dicts[model][1] / 1000000 #input price
                else: st.session_state.curr_debt += tokens_round * model_dicts[model][2] / 1000000 #output price
            total_tokens += tokens_round
        if j==choice: st.session_state.curr_debt += 2*model_dicts[model][0] / 1000000 # Additional tokens for the assistant's reply priming
        tokens.append(total_tokens+2)
    return tokens

def chat_with_gpt():#ALTERAR AQUI
    msg = []
    msg.append({ "role": "system","content": p.prompt_avaliador_light})
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
            st.experimental_rerun()
        st.stop()

def chat_with_tut():
    msg = []
    msg.append({ "role": "system","content": p.prompt_tutor})
    msg.extend(st.session_state.tutor_log)
    try:
        response = client.chat.completions.create(
            model=tut_model,
            messages=msg
        )
        st.session_state.times[1]+=1
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Erro ao contactar o tutor: {e}")
        if st.button("🔄 Tentar novamente"):
            st.experimental_rerun()
        st.stop()

def run_evaluator():
    st.session_state.response = chat_with_gpt()
    if (("SYSTEM" not in st.session_state.response) and ("TUTOR" not in st.session_state.response)):
        print_routine('assistant', re.sub(r'\[.*?\]', '',st.session_state.response).strip(), EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content': "Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    st.session_state.token_count = tokens_price_update(model=eval_model, choice=0)

    if "[STUDENT]" in st.session_state.response: st.session_state.phase = "student"
    elif "[SYSTEM]" in st.session_state.response: st.session_state.phase = "system"
    elif "[TUTOR]" in st.session_state.response: st.session_state.phase = "tutor"
    else: st.session_state.phase = None
    
    if "[END]" in st.session_state.response:st.session_state.phase = "end"
        
if "page_ready" not in st.session_state:
    st.session_state.page_ready = True
    st.rerun()
     
if "initialized" in st.session_state:
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
                                              
#Initialize Session Variables
if "initialized" not in st.session_state:
    #Memory Logs
    st.session_state.session_log = []
    st.session_state.chat_log = []
    st.session_state.tutor_log = []
    st.session_state.student_log = []
    #Specific stage logs
    st.session_state.clicked = False
    st.session_state.QUIZ = False
    st.session_state.fQUIZ = False
    st.session_state.print_state = True
    st.session_state.restart = False
    st.session_state.position_block = False
    st.session_state.tutor_state = [False, False]
    st.session_state.first_quiz = []
    st.session_state.final_quiz = []
    st.session_state.interaction = []
    #Cost Parameters
    st.session_state.times = [0,0]
    st.session_state.curr_debt = 0  
    st.session_state.token_count = [0,0]
    
    try:
        #Single run task
        intro = client.chat.completions.create(
            model=eval_model,
            messages=[{"role": "system", "content": p.prompt_avaliador_light}]
        )
        st.session_state.response = intro.choices[0].message.content.strip()
        st.session_state.times[0] += 1
        print_routine('assistant',re.sub(r'\[.*?\]', '',st.session_state.response).strip(), EVALUATOR_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
        st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
        st.session_state.token_count = tokens_price_update(model=eval_model, choice=0)
        st.session_state.initialized = True
        st.session_state.phase = "student"
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao inicializar o avaliador: {e}")
        st.warning("Não foi possível contactar o modelo de avaliação.")
        if st.button("🔄 Tentar novamente"):
            st.rerun()
        st.stop()
        
#STUDENT   
if st.session_state.phase == "student": 
    
    student = st.chat_input("Resposta")
    if student is None:
        st.stop()
    
    if st.session_state.QUIZ: st.session_state.first_quiz.append("Avaliador: " + st.session_state.response.replace("[STUDENT]",""))
    if st.session_state.fQUIZ: st.session_state.final_quiz.append("Avaliador: " + st.session_state.response.replace("[STUDENT]",""))

    st.session_state.student_log.append({'role': 'user', 'content': st.session_state.response.replace("[STUDENT]","")})
    st.session_state.phase = None   
    print_routine('user',student)
    st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
    st.session_state.chat_log.append({'role': 'assistant', 'content': student})
    st.session_state.student_log.append({'role': 'assistant', 'content': student})

    if st.session_state.QUIZ: st.session_state.first_quiz.append("Estudante: " + student)
    if st.session_state.fQUIZ: st.session_state.final_quiz.append("Estudante: " + student)
    if st.session_state.fQUIZ and st.session_state.print_state:
        st.session_state.print_state = False
        #print_routine('assistant',"---------------🎯 **Último Questionário** 🎯---------------\n\n", EVALUATOR_AVATAR)
        #st.session_state.session_log.append({
        #    'role': 'assistant',
        #    'content': (
        #        "Avaliador: ---------------🎯 **Último Questionário** 🎯---------------\n\n"
        #        )
        #}) 
    #EVALUATOR
    run_evaluator()
    if(st.session_state.QUIZ) and (st.session_state.phase == "tutor"):
        st.session_state.QUIZ=False
    st.rerun()   
              
#SYSTEM
elif st.session_state.phase == "system":
    if "questions" in st.session_state.response.lower():
        st.session_state.phase = None
        st.session_state.chat_log.append({'role': 'user', 'content': st.session_state.questions_text})
        st.session_state.QUIZ = True
        #st.session_state.session_log.append({
        #    'role': 'assistant',
        #    'content': (
        #        "Avaliador: ---------------🎯 **Primeiro Questionário** 🎯---------------\n\n"
        #        )
        #})        
        
        #EVALUATOR
        #print_routine("user", "---------------🎯 **Primeiro Questionário** 🎯---------------\n\n",EVALUATOR_AVATAR)
        run_evaluator()
        st.rerun()
           
elif st.session_state.phase == "tutor":
    #PROMPT ASSEMBLE
    if(st.session_state.tutor_state[0]==False and st.session_state.tutor_state[1]==False):
        st.session_state.response = st.session_state.response.replace("[TUTOR]","")
        quiz = "\n".join(st.session_state.first_quiz)
        st.session_state.response = "\nNível de conhecimento do estudante: " + quiz + "\n\n# **Instruções Importantes**\n\n Define o que é necessário melhorar no conhecimento do aluno com base nos erros cometidos por ele no questionário e não reveles esse plano.\n Quando terminares a conversa com o aluno, envia uma mensagem final de despedida com uma tag [END] no início a mensagem, referindo que vais passar a palavra ao teu colega:\n   [END] ...\n\nComeça já a interagir com o estudante na tua próxima resposta.\n"
        st.session_state.tutor_log.append({'role': 'user', 'content': st.session_state.response})
        st.session_state.tutor_state[0]=True
        st.session_state.tutor_state[1]=False
        #st.session_state.session_log.append({
        #    'role': 'assistant',
        #    'content': (
        #        "Avaliador: ---------------🎯 **Interação com Tutor** 🎯---------------\n\n"
        #        )
        #}) 
        st.rerun()
        
    #TUTOR
    elif(st.session_state.tutor_state[0]==True and st.session_state.tutor_state[1]==False):
        tutor = chat_with_tut()
        st.session_state.tutor_log.append({'role': 'assistant', 'content': tutor})
        st.session_state.token_count = tokens_price_update(model=tut_model, choice=2)
        if "[END]" in tutor:
            print_routine('assistant',tutor.replace("[END] ", ""), TUTOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Tutor: " + tutor.replace("[END] ", "")})
            st.session_state.interaction.append("Tutor: "+tutor.replace("[END] ", "")+"\n")
            tutor_interaction = "\n".join(st.session_state.interaction)
            st.session_state.chat_log.append({'role': 'user', 'content': tutor_interaction})
            st.session_state.tutor_state[0]=False
            st.session_state.tutor_state[1]=False
            #EVALUATOR
            run_evaluator()
            st.session_state.fQUIZ=True   
        else:
            print_routine('assistant',tutor, TUTOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Tutor: " + tutor})
            st.session_state.student_log.append({'role': 'user', 'content': tutor})
            st.session_state.interaction.append("Tutor: "+tutor+"\n")
            st.session_state.tutor_state[0]=False
            st.session_state.tutor_state[1]=True
        st.rerun()
    
    #STUDENT  
    elif(st.session_state.tutor_state[0]==False and st.session_state.tutor_state[1]==True):    
        student = st.chat_input("Resposta")
        if student is None:
            st.stop()  
        print_routine('user',student)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
        st.session_state.student_log.append({'role': 'assistant', 'content': student})
        st.session_state.tutor_log.append({'role': 'user', 'content': student})
        
        st.session_state.interaction.append("Estudante: "+student+"\n")  
        st.session_state.tutor_state[0]=True
        st.session_state.tutor_state[1]=False
        st.rerun()

if st.session_state.phase == "end":
    st.session_state.fQUIZ = False
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
        exec(open("cover.py").read())
        st.rerun()