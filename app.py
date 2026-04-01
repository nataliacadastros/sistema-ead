import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN COMPACTO E CORES DO PRINT ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #004a99 !important; }
    .stTextInput>div>div>input { background-color: white !important; color: black !important; height: 24px !important; font-size: 13px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 13px !important; margin-bottom: -5px !important; }
    .stButton>button { height: 30px; font-size: 12px !important; border-radius: 4px; margin-top: 10px; font-weight: bold; }
    /* Cores dos Botões conforme o Print */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #90ee90 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #a2d2ff !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    .block-container { padding-top: 1rem !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "texto_curso" not in st.session_state: st.session_state.texto_curso = ""

# --- FUNÇÃO DE TRADUÇÃO AUTOMÁTICA NO MESMO CAMPO ---
def processar_codigo_curso():
    entrada = st.session_state.campo_curso_unico.strip()
    
    # Se o que foi digitado for um código válido
    if entrada in CODIGOS_CURSOS:
        nome_curso = CODIGOS_CURSOS[entrada]
        if st.session_state.texto_curso:
            st.session_state.texto_curso += f" + {nome_curso}"
        else:
            st.session_state.texto_curso = nome_curso
    else:
        # Se digitaram texto normal (nome do curso manual), ele mantém
        st.session_state.texto_curso = entrada.upper()

# --- INTERFACE ---
with st.sidebar:
    st.title("SISTEMA EAD")
    aba = st.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        id_aluno = st.text_input("ID", key="id_aluno")
        aluno = st.text_input("Aluno", key="nome_aluno")
        t_resp = st.text_input("Tel. Responsável", key="tel_resp")
        t_alu = st.text_input("Tel. Aluno", key="tel_alu")
        cpf = st.text_input("CPF Responsável", key="cpf_resp")
        cidade = st.text_input("Cidade", key="cid_alu")
        
        # O CAMPO ÚNICO: Ele mostra o texto acumulado, mas processa o código ao dar Enter
        st.text_input("Curso Contratado (Digite o código e dê Enter)", 
                      value=st.session_state.texto_curso,
                      key="campo_curso_unico", 
                      on_change=processar_codigo_curso)
        
        pagto = st.text_input("Forma de Pagamento", key="form_pagto")
        vend = st.text_input("Vendedor", key="nome_vend")
        dt_mat = st.date_input("Data da Matrícula", value=date.today(), key="data_mat")

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib_ing = c1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c2.checkbox("CURSO BÔNUS")
        confirma = c3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Salvar Aluno"):
            if st.session_state.nome_aluno:
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.texto_curso else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.texto_curso else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": st.session_state.id_aluno, 
                    "Aluno": st.session_state.nome_aluno.upper(), 
                    "Tel. Resp": st.session_state.tel_resp,
                    "Tel. Aluno": st.session_state.tel_alu, 
                    "CPF": st.session_state.cpf_resp, 
                    "Cidade": st.session_state.cid_alu.upper(),
                    "Curso": st.session_state.texto_curso, 
                    "Pagamento": st.session_state.form_pagto.upper(),
                    "Vendedor": st.session_state.nome_vend.upper(), 
                    "Data Matrícula": st.session_state.data_mat.strftime("%d/%m/%Y"),
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.texto_curso = "" # Limpa o curso para o próximo aluno
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                with st.spinner("Enviando para a planilha..."):
                    df_nuvem = conn.read(ttl="0s").fillna("")
                    df_novos = pd.DataFrame(st.session_state.lista_previa)
                    linha_v = pd.DataFrame([{c: "" for c in df_novos.columns}])
                    df_final = pd.concat([df_nuvem, df_novos, linha_v], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.success("PDF Enviado com sucesso!")
                    st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    # TABELA DE PRÉ-VISUALIZAÇÃO (Fundo Branco)
    if st.session_state.lista_previa:
        st.markdown("<p style='text-align:center; color:white; font-weight:bold;'>Alunos na lista de espera:</p>", unsafe_allow_html=True)
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.markdown("### GERENCIADOR DE ALUNOS")
    df = conn.read(ttl="0s").fillna("")
    st.dataframe(df, use_container_width=True, hide_index=True)
