import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time

# Initialize session state variables if not already present
if 'scores' not in st.session_state:
    st.session_state.scores = []

if 'times' not in st.session_state:
    st.session_state.times = [0, 0, 0]

if 'curr_debt' not in st.session_state:
    st.session_state.curr_debt = 0

if 'token_count' not in st.session_state:
    st.session_state.token_count = [0, 0, 0]


    
# Safely extract last score if available
if st.session_state.scores:
    last_score = st.session_state.scores[-1]
    adaptability = last_score[1]
    concept_correction = last_score[2]
    curiosity = last_score[3]
    cognition = last_score[4]
    spelling = last_score[5]
else:
    adaptability = concept_correction = curiosity = cognition = spelling = "N/A"

# Render sidebar
st.sidebar.markdown(f'''
### Resultados do último Tutor:
- Adaptabilidade: **{adaptability}**
- Correção de conceitos: **{concept_correction}**
- Estimulação da curiosidade: **{curiosity}**
- Níveis cognitivos: **{cognition}**
- Correção ortográfica: **{spelling}**

### Número de respostas:
- Avaliador AI: **{st.session_state.times[0]}**
- Estudante AI: **{st.session_state.times[1]}**
- Tutor AI: **{st.session_state.times[2]}**

### Número de Tokens na janela de contexto:
- Avaliador AI: **{st.session_state.token_count[0]}**
- Estudante AI: **{st.session_state.token_count[1]}**
- Tutor AI: **{st.session_state.token_count[2]}**

#### Custo da Experiência:
- Custo: {st.session_state.curr_debt:.2f} $
''')

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
               
def tokens_price_update(model, choice=0): # 0-eval; 1-student; 2-tutor
    encoding = tiktoken.get_encoding("o200k_base")
    msg = [[], [], []]
    msg[0].append({ "role": "system","content": p.prompt_avaliador})
    msg[0].extend(st.session_state.chat_log)
    msg[1].append({ "role": "system","content": st.session_state.student_prompt})
    msg[1].extend(st.session_state.student_log)
    msg[2].append({ "role": "system","content": st.session_state.prompt_text})
    msg[2].extend(st.session_state.tutor_log)

    tokens = []
    for j in range(3):    
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


def chat_with_std():
    msg = []
    msg.append({ "role": "system","content": st.session_state.student_prompt})
    msg.extend(st.session_state.student_log)
    try:
        response = client.chat.completions.create(
            model=std_model,
            messages=msg
        )
        st.session_state.times[1]+=1
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Erro ao contactar o estudante: {e}")
        if st.button("🔄 Tentar novamente"):
            st.rerun()
        st.stop()

def chat_with_tut():
    msg = []
    msg.append({ "role": "system","content": st.session_state.prompt_text})
    msg.extend(st.session_state.tutor_log)
    try:
        response = client.chat.completions.create(
            model=tut_model,
            messages=msg
        )
        st.session_state.times[2]+=1
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Erro ao contactar o tutor: {e}")
        if st.button("🔄 Tentar novamente"):
            st.rerun()
        st.stop()
def run_evaluator():
    st.session_state.response = chat_with_gpt()
    if ("SYSTEM" not in st.session_state.response) and ("TUTOR" not in st.session_state.response):
        print_routine('assistant', re.sub(r'\[.*?\]', '',st.session_state.response).strip(), EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content': "Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    st.session_state.token_count = tokens_price_update(model=eval_model, choice=0)
    
    if "[USER]" in st.session_state.response: st.session_state.phase = "user"
    elif "[STUDENT]" in st.session_state.response: st.session_state.phase = "student"
    elif "[SYSTEM]" in st.session_state.response: st.session_state.phase = "system"
    elif "[TUTOR]" in st.session_state.response: st.session_state.phase = "tutor"
    else:
        st.warning("Erro na mensagem. Repita a mensagem anterior")
        st.session_state.phase = "user"

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
    st.session_state.tutor_state = [False, False]
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
        st.session_state.token_count = tokens_price_update(model=eval_model, choice=0)
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
    if (st.session_state.student_part):
        if st.session_state.button_pressed:
            st.session_state.button_pressed = False
            run_evaluator()
            st.rerun()
    
        if st.session_state.QUIZ: st.session_state.first_quiz.append("Questionário: " + st.session_state.response.replace("[STUDENT]",""))
        if st.session_state.fQUIZ and (not st.session_state.refresh_memory):
            st.session_state.student_log.append({'role': 'user', 'content': "## Para cada questão:\n   -**RACIOCINA** se já foste ensinado pelo Professor João.\n   -Se **foste ensinado**, então deves responder **apenas** com o conhecimento que o professor João te deu.\n   -Se **não foste ensinado** deves responder da mesma forma que da primeira vez que respondeste a essa pergunta;\n   -**Não podes reagir a esta mensagem**"})
            st.session_state.refresh_memory = True
        st.session_state.student_log.append({'role': 'user', 'content': st.session_state.response.replace("[STUDENT]","")})
        
                
        student = chat_with_std()
        print_routine('assistant',student, STUDENT_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
        st.session_state.chat_log.append({'role': 'user', 'content': student})
        st.session_state.student_log.append({'role': 'assistant', 'content': student})
        st.session_state.token_count = tokens_price_update(model=std_model, choice=1)
        if st.session_state.QUIZ: st.session_state.first_quiz.append("Estudante: " + student)
        if st.session_state.fQUIZ:
            print_routine('assistant',"---------------🎯 **Último Questionário** 🎯---------------\n\n", EVALUATOR_AVATAR)
            st.session_state.session_log.append({
                'role': 'assistant',
                'content': (
                    "Avaliador: ---------------🎯 **Último Questionário** 🎯---------------\n\n"
                    )
            }) 
            st.session_state.fQUIZ=False
        st.session_state.student_part = False
        st.rerun()
    else:
        continue_pressed = st.button("➡️ Continuar")
        if continue_pressed:        
            #EVALUATOR
            if(st.session_state.QUIZ) and (st.session_state.phase == "user"):
                st.session_state.QUIZ=False
            st.session_state.student_part = True
            st.session_state.button_pressed = True
            st.rerun()
    
       
              
#SYSTEM
elif st.session_state.phase == "system":
    if "questions" in st.session_state.response.lower():
        st.session_state.chat_log.append({'role': 'user', 'content': st.session_state.questions_text})
        st.session_state.QUIZ = True
        st.session_state.session_log.append({
            'role': 'assistant',
            'content': (
                "Avaliador: ---------------🎯 **Primeiro Questionário** 🎯---------------\n\n"
                )
        })        
        
        #EVALUATOR
        run_evaluator()
        st.rerun()
    elif "metrics" in st.session_state.response.lower():
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
                
           
elif st.session_state.phase == "tutor":
    #PROMPT ASSEMBLE
    if (st.session_state.position_block == False):
        st.session_state.begining_pos[0]=len(st.session_state.chat_log)
        st.session_state.begining_pos[1]=len(st.session_state.student_log) 
        st.session_state.begining_pos[2]=len(st.session_state.session_log)
        st.session_state.position_block=True
    if(st.session_state.tutor_state[0]==False and st.session_state.tutor_state[1]==False):
        st.session_state.response = st.session_state.response.replace("[TUTOR]","")
        quiz = "\n".join(st.session_state.first_quiz)
        st.session_state.response = st.session_state.response + "\nNível de conhecimento do estudante: " + quiz + "\n\n**Instruções Importantes**\n\n Define o que é necessário melhorar no conhecimento do estudante com base nas respostas dadas por ele e não reveles esse plano. Quando terminares a conversa com o estudante, envia uma mensagem final de despedida com uma tag [END] no início da mensagem:\n   [END] Obrigado, nome do estudante! Quando precisares de ajuda, ...\nComeça já a interagir com o estudante na tua próxima resposta:\n    Olá, nome do estudante!..."
        st.session_state.tutor_log.append({'role': 'user', 'content': st.session_state.response})
        st.session_state.tutor_state[0]=True
        st.session_state.tutor_state[1]=False
        st.session_state.session_log.append({
            'role': 'assistant',
            'content': (
                "Avaliador: ---------------🎯 **Interação com Tutor** 🎯---------------\n\n"
                )
        })
        #st.session_state.student_log.append({'role': 'system', 'content': st.session_state.student_prompt})
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
            #EVALUATOR
            run_evaluator()
            st.session_state.tutor_state[0]=False
            st.session_state.tutor_state[1]=False
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
        student = chat_with_std()
        print_routine('assistant',student, STUDENT_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
        st.session_state.student_log.append({'role': 'assistant', 'content': student})
        st.session_state.tutor_log.append({'role': 'user', 'content': student})
        st.session_state.token_count = tokens_price_update(model=std_model, choice=1)
        st.session_state.interaction.append("Estudante: "+student+"\n")  
        st.session_state.tutor_state[0]=True
        st.session_state.tutor_state[1]=True
        st.rerun()
        
    #USER INTERVENTION
    elif(st.session_state.tutor_state[0]==True and st.session_state.tutor_state[1]==True):
        col1, col2 = st.columns(2)
        with col1:
            continue_pressed = st.button("➡️ Continuar")
        with col2:
            skip_pressed = st.button("⏭️ Saltar interação")
        if skip_pressed:
            st.session_state.interaction.append("Tutor: I have finished the interaction with the student. You may proceed.\n")
            tutor_interaction = "\n".join(st.session_state.interaction)
            st.session_state.chat_log.append({'role': 'user', 'content': tutor_interaction})
            run_evaluator()
            st.session_state.tutor_state[0] = False
            st.session_state.tutor_state[1] = False
            st.session_state.fQUIZ=True
            st.rerun()
        elif continue_pressed:
            st.session_state.tutor_state[0] = True
            st.session_state.tutor_state[1] = False
            st.rerun()
            
#USER
elif st.session_state.phase == "user": 
    if "[END]" in  st.session_state.response:
        if st.session_state.restart == False:
           # Edit prompt
            with st.expander("🧠 Verificar / Alterar nova prompt do tutor"):
                st.session_state.prompt_text = st.text_area("Verifica aqui a prompt:", value=st.session_state.prompt_text, height=300)
                if st.button("✅ Já verifiquei a prompt e está pronta!"):
                    st.session_state.restart = True
                    st.rerun()
                
        else:
            print_routine('assistant',"⏳ A regressar ao final do primeiro questionário... ⏳", EVALUATOR_AVATAR)
            time.sleep(5)
            st.session_state.chat_log = st.session_state.chat_log[: st.session_state.begining_pos[0]]
            st.session_state.student_log = st.session_state.student_log[: st.session_state.begining_pos[1]]
            st.session_state.session_log = st.session_state.session_log[: st.session_state.begining_pos[2]]
            st.session_state.tutor_log = []
            st.session_state.response = st.session_state.chat_log[-1]['content']
            st.session_state.restart = False
            run_evaluator()
            st.rerun()
    
    user_input = st.chat_input("Resposta")
    if user_input is None:
        st.stop() 
    print_routine('user',user_input)
    st.session_state.session_log.append({'role': 'user', 'content':"Utilizador: " + user_input})
    st.session_state.chat_log.append({'role': 'user', 'content': user_input})
    
    
    #EVALUATOR
    run_evaluator()
    st.rerun()
