import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN IDENTICO AO SEU PROGRAMA ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #004a99 !important; }
    .stTextInput>div>div>input { background-color: white !important; color: black !important; height: 28px !important; font-size: 14px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 14px !important; margin-bottom: -2px !important; }
    .stButton>button { height: 35px; font-weight: bold; width: 100%; border-radius: 4px; }
    /* Cores dos Botões */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #90ee90 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #a2d2ff !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_atual" not in st.session_state: st.session_state.curso_atual = ""

# --- FUNÇÃO DE TRADUÇÃO (DISPARADA AO DAR ENTER) ---
def traduzir_curso():
    # Pega o que o usuário acabou de digitar
    valor_digitado = st.session_state.campo_curso.strip()
    
    # Se o valor for um dos códigos (0-10)
    if valor_digitado in CODIGOS_CURSOS:
        nome_do_curso = CODIGOS_CURSOS[valor_digitado]
        
        # Se já tiver algo escrito, adiciona o " + "
        if st.session_state.curso_atual:
            st.session_state.curso_atual += f" + {nome_do_curso}"
        else:
            st.session_state.curso_atual = nome_do_curso
            
    # Se não for código, mas o usuário digitou um nome manual, ele aceita
    elif valor_digitado != "":
        st.session_state.curso_atual = valor_digitado.upper()
    
    # Limpa o campo de digitação para o próximo
    st.session_state.campo_curso = ""

# --- INTERFACE ---
with st.sidebar:
    st.title("SISTEMA EAD")
    aba = st.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        # Campos de Cadastro
        id_aluno = st.text_input("ID")
        aluno = st.text_input("Aluno")
        t_resp = st.text_input("Tel. Responsável")
        t_alu = st.text_input("Tel. Aluno")
        cpf = st.text_input("CPF Responsável")
        cidade = st.text_input("Cidade")
        
        # O CAMPO DE CURSO CONTRATADO
        # Ele exibe o 'curso_atual' e quando você digita algo e dá Enter, roda a função 'traduzir_curso'
        st.text_input("Curso Contratado (Digite o código e dê Enter)", 
                      value=st.session_state.curso_atual, 
                      key="campo_curso", 
                      on_change=traduzir_curso)
        
        # Botão pequeno para limpar o curso se errar
        if st.button("Limpar Curso"):
            st.session_state.curso_atual = ""
            st.rerun()

        pagto = st.text_input("Forma de Pagamento")
        vend = st.text_input("Vendedor")
        dt_mat = st.date_input("Data da Matrícula", value=date.today())

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib_ing = c1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c2.checkbox("CURSO BÔNUS")
        confirma = c3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        # BOTÕES DE AÇÃO
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Salvar Aluno"):
            if aluno:
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.curso_atual else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.curso_atual else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": aluno.upper(), "Tel. Resp": t_resp,
                    "Tel. Aluno": t_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": st.session_state.curso_atual, "Pagamento": pagto.upper(),
                    "Vendedor": vend.upper(), "Data Matrícula": dt_mat.strftime("%d/%m/%Y"),
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.curso_atual = "" # Limpa para o próximo aluno
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_nuvem = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                linha_v = pd.DataFrame([{c: "" for c in df_novos.columns}])
                df_final = pd.concat([df_nuvem, df_novos, linha_v], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.success("Enviado para o Gerenciador!")
                st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    # TABELA DE PRÉ-VISUALIZAÇÃO (Fundo Branco embaixo)
    if st.session_state.lista_previa:
        st.markdown("<p style='text-align:center;'>Alunos na lista de espera:</p>", unsafe_allow_html=True)
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.markdown("### GERENCIADOR DE ALUNOS")
    df = conn.read(ttl="0s").fillna("")
    st.dataframe(df, use_container_width=True, hide_index=True)
