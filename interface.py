import streamlit as st
from openai import OpenAI
import prompts as p
import re
import tiktoken
import os
import time

st.title("Quizmania")
EVALUATOR_AVATAR = "🤖"
TUTOR_AVATAR = "🧑‍🏫"
STUDENT_AVATAR = "🧒🏼"

eval_model = "gpt-4o"
std_model = "gpt-4o-mini"
tut_model = "gpt-4o"

client = OpenAI(
    api_key = st.secrets["openai"]["api_key"]  
)

tokens = []

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
        with st.chat_message(role):
            st.markdown(text)

def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)
               
def tokens_price_update(model="gpt-4o", choice=0): # 0-eval; 1-student; 2-tutor
    encoding = tiktoken.encoding_for_model(model)
    msg = [[], [], []]
    msg[0].append({ "role": "system","content": p.prompt_avaliador})
    msg[0].extend(st.session_state.chat_log)
    msg[1].append({ "role": "system","content": p.prompt_estudante})
    msg[1].extend(st.session_state.student_log)
    msg[2].append({ "role": "system","content": p.prompt_tutor})
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
    global times
    msg.append({ "role": "system","content": p.prompt_avaliador})
    msg.extend(st.session_state.chat_log)
    response = client.chat.completions.create(
        model=eval_model,
        messages=msg
    )
    st.session_state.times[0]+=1
    return response.choices[0].message.content.strip()

def chat_with_std():
    msg = []
    msg.append({ "role": "system","content": p.prompt_estudante})
    msg.extend(st.session_state.student_log)
    response = client.chat.completions.create(
        model=std_model,
        messages=msg
    )
    st.session_state.times[1]+=1
    return response.choices[0].message.content.strip()

def chat_with_tut():
    msg = []
    msg.append({ "role": "system","content": p.prompt_tutor})
    msg.extend(st.session_state.tutor_log)
    response = client.chat.completions.create(
        model=tut_model,
        messages=msg
    )
    st.session_state.times[2]+=1
    return response.choices[0].message.content.strip()

def extract_tutor_prompt():
    path = "prompt.txt"
    try:
        if os.path.getsize(path) <= 0:
            print("O ficheiro está vazio. Tenta de novo.\n")
        else:
            with open(path, "r", encoding="utf-8") as file:
                p.prompt_tutor = file.read()
    except FileNotFoundError:
        print("O ficheiro não existe. Tenta de novo.\n")
                
                
#Initialize Session Variables
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    #Memory Logs
    st.session_state.response = "empty"
    st.session_state.session_log = []
    st.session_state.chat_log = []
    st.session_state.tutor_log = []
    st.session_state.student_log = []
    st.session_state.begining_pos = [0,0,0]     # for chat_log, student_log and session_log checkpoints
    st.session_state.first_quiz = []
    st.session_state.interaction = []
    #Specific stage logs
    st.session_state.QUIZ = False
    st.session_state.first_quiz = []
    st.session_state.interaction = []
    #Cost Parameters
    st.session_state.times = [0,0,0]
    st.session_state.curr_debt = 0  
     
    #Single run task
    intro = client.chat.completions.create(
        model='gpt-4o',
        messages=[{"role": "system", "content": p.prompt_avaliador}]
    )
    st.session_state.response = intro.choices[0].message.content.strip()
    st.session_state.times[0] += 1
    print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    tokens = tokens_price_update(model=eval_model, choice=0)

# Display chat messages from history on app rerun
for message in st.session_state.session_log:
    if message["content"].lower().startswith("estudante"):
        print_routine(message["role"],message["content"].removeprefix("Estudante: "),STUDENT_AVATAR)
    elif message["content"].lower().startswith("tutor"):
        print_routine(message["role"],message["content"].removeprefix("Tutor: "),TUTOR_AVATAR)
    elif message["content"].lower().startswith("avaliador"):
        print_routine(message["role"],message["content"].removeprefix("Avaliador: "),EVALUATOR_AVATAR)
    elif message["content"].lower().startswith("utilizador"):
        print_routine(message["role"],message["content"].removeprefix("Utilizador: "))
        
        
if "[SYSTEM]" in st.session_state.response:
    if "questions" in st.session_state.response.lower():
        #SYSTEM
        with open("questions.txt", "r", encoding="utf-8") as file:
            prompt_questions = file.read()
        st.session_state.chat_log.append({'role': 'user', 'content': prompt_questions})
        #print("\nQuestions returned\n")
        st.session_state.QUIZ = True
        
        #EVALUATOR
        st.session_state.response = chat_with_gpt()
        print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
        st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
        tokens = tokens_price_update(model=eval_model, choice=0)
    else:
        #SYSTEM
        with open("metrics.txt", "r", encoding="utf-8") as file:
            prompt_metrics = file.read()
        st.session_state.chat_log.append({'role': 'user', 'content': prompt_metrics})
        #print("\nMetrics returned\n")
        
        #EVALUATOR
        st.session_state.response = chat_with_gpt()
        print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
        st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
        tokens = tokens_price_update(model=eval_model, choice=0)        
        
        

elif "[TUTOR]" in st.session_state.response:
    #PROMPT ASSEMBLE
    st.session_state.response = st.session_state.response.replace("[TUTOR]","")
    quiz = "\n".join(st.session_state.first_quiz)
    st.session_state.response = st.session_state.response + "\nNível de conhecimento do estudante: " + quiz + "\n\n**Instruções Importantes**\n\n Define o que é necessário melhorar no conhecimento do estudante com base nas respostas dadas por ele e não reveles esse plano. Quando terminares a conversa com o estudante, envia uma mensagem final de despedida com uma tag [END] no início a mensagem:\n   [END] Obrigado, nome do estudante! Quando precisares de ajuda, ...\nComeça já a interagir com o estudante na tua próxima resposta:\n    Olá, nome do estudante!..."
    st.session_state.tutor_log.append({'role': 'user', 'content': st.session_state.response})
    while(True):
        #TUTOR
        tutor = chat_with_tut()
        st.session_state.tutor_log.append({'role': 'assistant', 'content': tutor})
        tokens = tokens_price_update(model=tut_model, choice=2)
        if "[END]" in tutor:
            print_routine('assistant',tutor.replace("[END] ", ""), TUTOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Tutor: " + tutor.replace("[END] ", "")})
            st.session_state.interaction.append("Tutor: "+tutor.replace("[END] ", "")+"\n")
            tutor_interaction = "\n".join(st.session_state.interaction)
            st.session_state.chat_log.append({'role': 'user', 'content': tutor_interaction})
            
            #EVALUATOR
            st.session_state.response = chat_with_gpt()
            print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
            st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
            tokens = tokens_price_update(model=eval_model, choice=0)  
            break 
        print_routine('assistant',tutor, TUTOR_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Tutor: " + tutor})
        st.session_state.interaction.append("Tutor: "+tutor+"\n")
 
        #USER INTERVENTION
        user_input = st.chat_input("[Enter to continue]/[\"skip\" to skip rest of interaction]")
        if user_input.lower() in ["skip"]:
            st.session_state.interaction.append("Tutor: "+"I have finished the interaction with the student. You may proceed."+"\n")
            tutor_interaction = "\n".join(st.session_state.interaction)
            st.session_state.chat_log.append({'role': 'user', 'content': tutor_interaction})
            
            #EVALUATOR
            st.session_state.response = chat_with_gpt()
            print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
            st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
            tokens = tokens_price_update(model=eval_model, choice=0)
            break
        
        #STUDENT
        st.session_state.student_log.append({'role': 'user', 'content': tutor})
        student = chat_with_std()
        print_routine('assistant',student, STUDENT_AVATAR)
        st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
        st.session_state.student_log.append({'role': 'assistant', 'content': student})
        st.session_state.tutor_log.append({'role': 'user', 'content': student})
        tokens = tokens_price_update(model=std_model, choice=1)
        st.session_state.interaction.append("Estudante: "+student+"\n")  
        
       #USER INTERVENTION
        user_input = st.chat_input("Enter to continue / \"skip\" to skip rest of interaction")
        if user_input.lower() in ["skip"]:
            st.session_state.interaction.append("Tutor: "+"I have finished the interaction with the student. You may proceed."+"\n")
            tutor_interaction = "\n".join(st.session_state.interaction)
            st.session_state.chat_log.append({'role': 'user', 'content': tutor_interaction})
            
            #EVALUATOR
            st.session_state.response = chat_with_gpt()
            print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
            st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
            st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
            tokens = tokens_price_update(model=eval_model, choice=0)
            break
                
elif "[STUDENT]" in st.session_state.response: 
    if st.session_state.QUIZ: st.session_state.first_quiz.append("Questionário: " + st.session_state.response.replace("[STUDENT]",""))
    st.session_state.student_log.append({'role': 'user', 'content': st.session_state.response.replace("[STUDENT]","")})
    
    #STUDENT
    student = chat_with_std()
    print_routine('assistant',student, STUDENT_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content':"Estudante: " + student})
    st.session_state.student_log.append({'role': 'assistant', 'content': student})
    tokens = tokens_price_update(model=std_model, choice=1)
    if st.session_state.QUIZ: st.session_state.first_quiz.append("Estudante: " + student)
    
    #USER INTERVENTION
    user_input = st.chat_input("\nEnter to continue\n")
    
    #EVALUATOR
    st.session_state.chat_log.append({'role': 'user', 'content': student})
    st.session_state.response = chat_with_gpt()
    print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    tokens = tokens_price_update(model=eval_model, choice=0)

    if (st.session_state.QUIZ) and ("[USER]" in st.session_state.response):
        st.session_state.QUIZ=False
        st.session_state.begining_pos[0]=len(st.session_state.chat_log)
        st.session_state.begining_pos[1]=len(st.session_state.student_log) 
        st.session_state.begining_pos[2]=len(st.session_state.session_log)      
                
else: #expecting user to react
    if "[END]" in  st.session_state.response:
        match = re.search(r'prompt:\s*"(.*)\s*\[END\]',  st.session_state.response)
        if match:
            full_content = match.group(1).rstrip()
            if full_content.endswith('"'):
                full_content = full_content[:-1]
            with open("prompt.txt", "w") as file:
                file.write(full_content)
        else: 
            print_routine('assistant',"Não foi possível guardar automaticamente a prompt. Guarda-a manualmente no ficheiro \"prompt.txt\"", EVALUATOR_AVATAR)
        while(True):
            user_input = st.chat_input("Escreve \"pronto\" depois de teres verificado que a prompt está certa")
            if (user_input.lower() in ["pronto"]):
                extract_tutor_prompt()
                break
        print_routine('assistant',"A regressar ao final do primeiro questionário...", EVALUATOR_AVATAR)
        
        st.session_state.chat_log = st.session_state.chat_log[: st.session_state.begining_pos[0]]
        st.session_state.student_log = st.session_state.student_log[: st.session_state.begining_pos[1]]
        st.session_state.session_log = st.session_state.session_log[: st.session_state.begining_pos[2]]
        st.session_state.tutor_log = []
        st.session_state.response = st.session_state.chat_log[-1]['content']
        print_routine('assistant',st.session_state.response, EVALUATOR_AVATAR) #may not be necessary due to session_log update!!!!!!!!!!!!!!!!!
        
    user_input = st.chat_input("Resposta")
    print_routine('user',user_input)
    st.session_state.session_log.append({'role': 'user', 'content':"Utilizador: " + user_input})
    st.session_state.chat_log.append({'role': 'user', 'content': user_input})
    if user_input.lower() in ["quit", "exit", "bye"]:
        print_routine('Assistant', "Nº Total de Tokens para contexto [Avaliador, Estudante, Tutor]: " + tokens + "\n" + "Custo acumulado: " + st.session_state.curr_debt + "$\n" +  "Número de respostas dadas [Avaliador, Estudante, Tutor]: " + st.session_state.times + "\n",)
        #EXIT function
    
    #EVALUATOR
    st.session_state.response = chat_with_gpt()
    print_routine('assistant',st.session_state.response,EVALUATOR_AVATAR)
    st.session_state.session_log.append({'role': 'assistant', 'content':"Avaliador: " + st.session_state.response})
    st.session_state.chat_log.append({'role': 'assistant', 'content': st.session_state.response})
    tokens = tokens_price_update(model=eval_model,choice=0)
            


        
