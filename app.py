import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN IDENTICO AO SOLICITADO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #004a99 !important; }
    
    /* Inputs Brancos com Texto Preto e Maiúsculo */
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 30px !important; text-transform: uppercase !important; 
    }
    
    /* Labels Verdes */
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 14px !important; margin-bottom: -5px !important; }
    
    /* Botões Verdes com Letra Branca */
    .stButton>button { 
        height: 40px; 
        background-color: #2ecc71 !important; 
        color: white !important; 
        font-weight: bold !important; 
        border-radius: 4px; 
        width: 100%;
        border: none;
    }
    
    /* Remover elementos padrão do Streamlit */
    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Estilo da Tabela de Pré-visualização */
    .stDataFrame { background-color: white !important; border-radius: 2px !important; }
    
    /* Forçar alinhamento vertical dos blocos */
    [data-testid="stVerticalBlock"] { gap: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

COLUNAS_TABELA = ["ID", "Aluno", "Tel. Responsável", "Tel. Aluno", "CPF Responsável", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data da Matrícula"]

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
    # Centralização forçada dos campos (Largura igual para todos)
    _, col_central, _ = st.columns([1, 4, 1])
    
    with col_central:
        st.text_input("ID", key="id_alu")
        st.text_input("Aluno", key="nome_alu")
        st.text_input("Tel. Responsável", key="t_resp")
        st.text_input("Tel. Aluno", key="t_alu")
        st.text_input("CPF Responsável", key="cpf_input", on_change=aplicar_mascara_cpf)
        st.text_input("Cidade", value=st.session_state.cidade_p, key="cid_f")
        st.text_input("Curso Contratado", value=st.session_state.curso_acumulado, key="curso_field", on_change=processar_curso)
        st.text_input("Forma de Pagamento", key="pagto_input")
        st.text_input("Vendedor", value=st.session_state.vendedor_p, key="vend_f")
        st.text_input("Data da Matrícula", value=st.session_state.data_p, key="data_input", on_change=aplicar_mascara_data)

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib = c1.checkbox("LIBERAÇÃO IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        bon = c2.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        con = c3.checkbox("AGUARDANDO CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        # Botões centralizados e com a nova cor
        b1_col, b2_col = st.columns(2)
        
        if b1_col.button("Salvar Aluno"):
            if st.session_state.nome_alu:
                aluno_novo = {
                    "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(), 
                    "Tel. Responsável": st.session_state.t_resp, "Tel. Aluno": st.session_state.t_alu, 
                    "CPF Responsável": st.session_state.cpf_input, "Cidade": st.session_state.cid_f.upper(), 
                    "Curso Contratado": st.session_state.curso_acumulado.strip(),
                    "Forma de Pagamento": st.session_state.pagto_input.upper(),
                    "Vendedor": st.session_state.vend_f.upper(), "Data da Matrícula": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno_novo)
                st.session_state.cidade_p = st.session_state.cid_f.upper()
                st.session_state.vendedor_p = st.session_state.vend_f.upper()
                st.session_state.data_p = st.session_state.data_input
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2_col.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_planilha = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                # Adiciona colunas técnicas da planilha
                cols_planilha = ["STATUS", "SEC", "TURMA", "10 CURSOS?", "INGLÊS?", "Data Cadastro", "ID", "Aluno", "Tel. Resp", "Tel. Aluno", "CPF", "Cidade", "Curso", "Pagamento", "Vendedor", "Data Matrícula", "OBS1", "OBS2"]
                
                # Mapeia os dados para as colunas reais da planilha
                df_to_save = pd.DataFrame(columns=cols_planilha)
                for aluno in st.session_state.lista_previa:
                    nova_l = {
                        "STATUS": "ATIVO", "SEC": "MGA", "ID": aluno["ID"], "Aluno": aluno["Aluno"],
                        "Tel. Resp": aluno["Tel. Responsável"], "Tel. Aluno": aluno["Tel. Aluno"],
                        "CPF": aluno["CPF Responsável"], "Cidade": aluno["Cidade"],
                        "Curso": aluno["Curso Contratado"], "Pagamento": aluno["Forma de Pagamento"],
                        "Vendedor": aluno["Vendedor"], "Data Matrícula": aluno["Data da Matrícula"],
                        "Data Cadastro": date.today().strftime("%d/%m/%Y"), "10 CURSOS?": "SIM" if "10 CURSOS" in aluno["Curso Contratado"] else "NÃO",
                        "INGLÊS?": "SIM" if "INGLÊS" in aluno["Curso Contratado"] else "NÃO"
                    }
                    df_to_save = pd.concat([df_to_save, pd.DataFrame([nova_l])], ignore_index=True)

                df_final = pd.concat([df_planilha, df_to_save, pd.DataFrame([{c: "" for c in cols_planilha}])], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.session_state.cidade_p = ""; st.session_state.vendedor_p = ""; st.session_state.data_p = ""
                st.rerun()

    # --- TABELA DE PRÉ-VISUALIZAÇÃO FIXA (SEM 'EMPTY') ---
    st.markdown(f"<p style='text-align: center; margin-top: 20px;'>Alunos na lista: <b>{len(st.session_state.lista_previa)}</b></p>", unsafe_allow_html=True)
    
    # Criamos a tabela. Se estiver vazia, passamos um DataFrame apenas com colunas
    if st.session_state.lista_previa:
        df_visual = pd.DataFrame(st.session_state.lista_previa)[COLUNAS_TABELA]
    else:
        df_visual = pd.DataFrame(columns=COLUNAS_TABELA)
    
    # use_container_width garante que ela ocupe a largura total
    st.dataframe(df_visual, use_container_width=True, hide_index=True)

elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True, hide_index=True)
