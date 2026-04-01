import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA MENU SUPERIOR E TELA CHEIA ---
st.markdown("""
    <style>
    /* Fundo e preenchimento total da tela */
    .stApp { background-color: #1a2436; color: white; }
    
    /* Remove as margens das laterais para ocupar a tela toda */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Inputs Brancos com Texto Preto e Maiúsculo */
    .stTextInput>div>div>input { 
        background-color: white !important; color: black !important; 
        height: 32px !important; text-transform: uppercase !important; 
        border-radius: 4px !important;
    }
    
    /* Labels Verdes */
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 14px !important; margin-bottom: -2px !important; }
    
    /* Botões Verdes com Letra Branca */
    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        height: 45px !important;
        width: 100% !important;
        border-radius: 5px !important;
    }

    /* Estilização das Abas (Menu Horizontal Superior) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: #004a99;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre;
        color: white !important;
        background-color: transparent;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2ecc71 !important;
        border-radius: 5px;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Tabela Branca Total */
    .stDataFrame { background-color: white !important; border-radius: 0px !important; padding: 0px; }
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

# --- MENU SUPERIOR HORIZONTAL ---
aba_selecionada = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

# --- CONTEÚDO CADASTRO ---
with aba_selecionada[0]:
    # Formulário centralizado mas com campos ocupando boa largura
    _, col_form, _ = st.columns([1, 2, 1])
    
    with col_form:
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
        c1.checkbox("LIBERAÇÃO IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        c2.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        c3.checkbox("AGUARDANDO CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        st.write("")
        b1_col, b2_col = st.columns(2)
        
        if b1_col.button("SALVAR ALUNO"):
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

        if b2_col.button("FINALIZAR PDF"):
            if st.session_state.lista_previa:
                df_planilha = conn.read(ttl="0s").fillna("")
                df_to_save = pd.DataFrame(st.session_state.lista_previa)
                # Adiciona colunas técnicas da planilha
                cols_planilha = ["STATUS", "SEC", "TURMA", "10 CURSOS?", "INGLÊS?", "Data Cadastro", "ID", "Aluno", "Tel. Resp", "Tel. Aluno", "CPF", "Cidade", "Curso", "Pagamento", "Vendedor", "Data Matrícula", "OBS1", "OBS2"]
                
                # Mapeia os dados para as colunas reais da planilha
                df_to_save_final = pd.DataFrame(columns=cols_planilha)
                for aluno in st.session_state.lista_previa:
                    nova_l = {
                        "STATUS": "ATIVO", "SEC": "MGA", "ID": aluno["ID"], "Aluno": aluno["ID"],
                        "Tel. Resp": aluno["Tel. Responsável"], "Tel. Aluno": aluno["Tel. Aluno"],
                        "CPF": aluno["CPF Responsável"], "Cidade": aluno["Cidade"],
                        "Curso": aluno["Curso Contratado"], "Pagamento": aluno["Forma de Pagamento"],
                        "Vendedor": aluno["Vendedor"], "Data Matrícula": aluno["Data da Matrícula"],
                        "Data Cadastro": date.today().strftime("%d/%m/%Y"), 
                        "10 CURSOS?": "SIM" if "10 CURSOS" in aluno["Curso Contratado"] else "NÃO",
                        "INGLÊS?": "SIM" if "INGLÊS" in aluno["Curso Contratado"] else "NÃO"
                    }
                    df_to_save_final = pd.concat([df_to_save_final, pd.DataFrame([nova_l])], ignore_index=True)

                df_final = pd.concat([df_planilha, df_to_save_final, pd.DataFrame([{c: "" for c in cols_planilha}])], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.session_state.cidade_p = ""; st.session_state.vendedor_p = ""; st.session_state.data_p = ""
                st.rerun()

    # --- TABELA DE PRÉ-VISUALIZAÇÃO TELA CHEIA ---
    st.markdown(f"<p style='text-align: center; margin-top: 30px; font-weight: bold;'>Alunos na lista: {len(st.session_state.lista_previa)}</p>", unsafe_allow_html=True)
    
    if st.session_state.lista_previa:
        df_visual = pd.DataFrame(st.session_state.lista_previa)[COLUNAS_TABELA]
    else:
        vazio = {col: " " for col in COLUNAS_TABELA}
        df_visual = pd.DataFrame([vazio], columns=COLUNAS_TABELA)
    
    st.dataframe(df_visual, use_container_width=True, hide_index=True)

# --- CONTEÚDO GERENCIAMENTO ---
with aba_selecionada[1]:
    st.markdown("### GERENCIAMENTO DE MATRÍCULAS")
    df_geral = conn.read(ttl="0s").fillna("")
    st.dataframe(df_geral, use_container_width=True, hide_index=True)

# --- CONTEÚDO RELATÓRIOS ---
with aba_selecionada[2]:
    st.markdown("### RELATÓRIOS E ESTATÍSTICAS")
    st.info("Módulo de relatórios em desenvolvimento.")
