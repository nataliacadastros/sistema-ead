import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN IDENTICO AO PRINT ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #004a99 !important; }
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 28px !important; text-transform: uppercase !important; 
    }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 14px !important; margin-bottom: -5px !important; }
    .stButton>button { height: 35px; font-size: 13px !important; border-radius: 4px; font-weight: bold; width: 100%; }
    /* Cores dos botões */
    div[data-testid="column"]:nth-child(1) button { background-color: #90ee90 !important; color: black !important; }
    div[data-testid="column"]:nth-child(2) button { background-color: #a2d2ff !important; color: black !important; }
    div[data-testid="column"]:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Tabela de pré-visualização branca como no print */
    .stDataFrame { background-color: white !important; border-radius: 5px !important; }
    </style>
    """, unsafe_allow_html=True)

CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""
if "cidade_p" not in st.session_state: st.session_state.cidade_p = ""
if "vendedor_p" not in st.session_state: st.session_state.vendedor_p = ""
if "data_p" not in st.session_state: st.session_state.data_p = ""

# --- FUNÇÕES DE LÓGICA ---
def aplicar_mascara_cpf():
    v = "".join(filter(str.isdigit, st.session_state.cpf_input))
    if len(v) == 11:
        st.session_state.cpf_input = f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"

def aplicar_mascara_data():
    v = "".join(filter(str.isdigit, st.session_state.data_input))
    if len(v) == 8:
        st.session_state.data_input = f"{v[:2]}/{v[2:4]}/{v[4:]}"

def processar_curso():
    texto = st.session_state.curso_field.strip()
    partes = texto.split()
    if partes:
        ultimo = partes[-1]
        if ultimo in CURSOS_DICT:
            nome = CURSOS_DICT[ultimo].upper()
            anterior = " ".join(partes[:-1])
            if anterior:
                if anterior.endswith("+"): anterior = anterior[:-1].strip()
                st.session_state.curso_acumulado = f"{anterior} + {nome} "
            else:
                st.session_state.curso_acumulado = f"{nome} "
        else:
            st.session_state.curso_acumulado = texto.upper() + " "
    st.session_state.curso_field = st.session_state.curso_acumulado

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- INTERFACE ---
aba = st.sidebar.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    
    with col_central:
        # Usamos chaves dinâmicas para resetar o formulário sem erro de API
        id_alu = st.text_input("ID", key="id_alu")
        nome_alu = st.text_input("Aluno", key="nome_alu")
        t_resp = st.text_input("Tel. Responsável", key="t_resp")
        t_alu = st.text_input("Tel. Aluno", key="t_alu")
        st.text_input("CPF Responsável", key="cpf_input", on_change=aplicar_mascara_cpf)
        cidade = st.text_input("Cidade", value=st.session_state.cidade_p, key="cid_f")
        st.text_input("Curso Contratado", value=st.session_state.curso_acumulado, key="curso_field", on_change=processar_curso)
        st.text_input("Forma de Pagamento", key="pagto_input")
        vendedor = st.text_input("Vendedor", value=st.session_state.vendedor_p, key="vend_f")
        st.text_input("Data da Matrícula", value=st.session_state.data_p, key="data_input", on_change=aplicar_mascara_data)

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib = c1.checkbox("LIBERAÇÃO IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        bon = c2.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        con = c3.checkbox("AGUARDANDO CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        b1, b2, b3 = st.columns(3)
        
        if b1.button("Salvar Aluno"):
            if nome_alu:
                aluno_novo = {
                    "ID": id_alu.upper(), "Aluno": nome_alu.upper(), "Tel. Responsável": t_resp,
                    "Tel. Aluno": t_alu, "CPF Responsável": st.session_state.cpf_input,
                    "Cidade": cidade.upper(), "Curso Contratado": st.session_state.curso_acumulado.strip(),
                    "Forma de Pagamento": st.session_state.pagto_input.upper(),
                    "Vendedor": vendedor.upper(), "Data da Matrícula": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno_novo)
                # Mantém os persistentes
                st.session_state.cidade_p = cidade.upper()
                st.session_state.vendedor_p = vendedor.upper()
                st.session_state.data_p = st.session_state.data_input
                # Limpa curso e pagto para o próximo
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_planilha = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                # Adiciona colunas faltantes para bater com a planilha
                for col in ["STATUS", "SEC", "TURMA", "10 CURSOS?", "INGLÊS?", "Data Cadastro"]:
                    if col not in df_novos: df_novos[col] = ""
                
                df_final = pd.concat([df_planilha, df_novos, pd.DataFrame([{c: "" for c in df_planilha.columns}])], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.session_state.cidade_p = ""; st.session_state.vendedor_p = ""; st.session_state.data_p = ""
                st.success("Enviado!")
                st.rerun()

        b3.button("GERENCIAMENTO MESTRE")

    # --- LISTA DE PRÉ-VISUALIZAÇÃO (IDÊNTICA AO PRINT) ---
    st.markdown(f"<h4 style='text-align: center;'>Alunos na lista: {len(st.session_state.lista_previa)}</h4>", unsafe_allow_html=True)
    if st.session_state.lista_previa:
        df_visualizacao = pd.DataFrame(st.session_state.lista_previa)
        st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)
