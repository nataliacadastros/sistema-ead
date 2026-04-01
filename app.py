import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA TÍTULOS LATERAIS E ALTURA MÍNIMA ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; overflow: hidden; }
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        max-width: 98% !important;
    }

    /* Força o container do input a ter 20px */
    div[data-testid="stTextInput"] > div {
        min-height: 22px !important;
        height: 22px !important;
    }

    /* Estilo do Input */
    .stTextInput>div>div>input { 
        background-color: white !important; 
        color: black !important; 
        height: 22px !important; 
        min-height: 22px !important;
        line-height: 22px !important;
        text-transform: uppercase !important; 
        border-radius: 2px !important; 
        font-size: 11px !important;
        padding: 0px 5px !important;
    }
    
    /* Ajuste dos Títulos (Labels) para ficarem alinhados lateralmente */
    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 11px !important; 
        margin-bottom: 0px !important;
        display: flex;
        align-items: center;
        height: 22px; /* Mesma altura do input para alinhar meio a meio */
    }
    
    /* Botões Verdes */
    div.stButton > button {
        background-color: #2ecc71 !important;
        color: white !important;
        font-weight: bold !important;
        height: 30px !important;
        font-size: 12px !important;
        border-radius: 3px !important;
    }

    /* Tabs e Tabela */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #004a99; padding: 2px 10px; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; }
    
    /* Remove gaps entre linhas */
    [data-testid="stVerticalBlock"] { gap: 0.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURAÇÕES ---
CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}
COLUNAS = ["ID", "Aluno", "Tel. Responsável", "Tel. Aluno", "CPF Responsável", "Cidade", "Curso Contratado", "Forma de Pagamento", "Vendedor", "Data da Matrícula"]

conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO PARA CRIAR LINHA COM TÍTULO LATERAL ---
def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1, 4]) # 1 parte título, 4 partes campo
    with c1:
        st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2:
        # Deixamos o label do widget vazio porque já criamos o nosso na c1
        return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- LOGICA DE TRATAMENTO ---
def processar_curso():
    texto = st.session_state.curso_field.strip()
    partes = texto.split()
    if partes:
        ultimo = partes[-1]
        if ultimo in CURSOS_DICT:
            nome = CURSOS_DICT[ultimo].upper()
            anterior = " ".join(partes[:-1])
            st.session_state.curso_acumulado = f"{anterior} + {nome} " if anterior else f"{nome} "
        else: st.session_state.curso_acumulado = texto.upper() + " "
    st.session_state.curso_field = st.session_state.curso_acumulado

# --- INTERFACE ---
abas = st.tabs(["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

with abas[0]:
    _, col_form, _ = st.columns([0.5, 3, 0.5])
    
    with col_form:
        # Renderização dos campos com título à esquerda
        id_alu = campo_horizontal("ID:", "id_alu")
        nome_alu = campo_horizontal("ALUNO:", "nome_alu")
        t_resp = campo_horizontal("TEL. RESP:", "t_resp")
        t_alu = campo_horizontal("TEL. ALUNO:", "t_alu")
        cidade = campo_horizontal("CIDADE:", "cid_f", value=st.session_state.get("cidade_p", ""))
        curso = campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_acumulado, on_change=processar_curso)
        pagto = campo_horizontal("PAGAMENTO:", "pagto_input")
        vend = campo_horizontal("VENDEDOR:", "vend_f", value=st.session_state.get("vendedor_p", ""))
        data_m = campo_horizontal("DATA:", "data_input", value=st.session_state.get("data_p", ""))

        st.write("")
        # Botões e Checkboxes
        c1, c2, c3, b1, b2 = st.columns([1, 1, 1, 1.5, 1.5])
        with c1: st.checkbox("IN-GLÊS", key="check_lib")
        with c2: st.checkbox("BÔNUS", key="check_bonus")
        with c3: st.checkbox("CONFIRMA", key="check_conf")

        if b1.button("SALVAR ALUNO"):
            if st.session_state.nome_alu:
                aluno = {
                    "ID": st.session_state.id_alu.upper(), "Aluno": st.session_state.nome_alu.upper(),
                    "Cidade": st.session_state.cid_f.upper(), "Curso Contratado": st.session_state.curso_acumulado,
                    "Forma de Pagamento": st.session_state.pagto_input.upper(), "Vendedor": st.session_state.vend_f.upper(),
                    "Data da Matrícula": st.session_state.data_input
                }
                st.session_state.lista_previa.append(aluno)
                st.session_state.curso_acumulado = ""
                st.rerun()

        if b2.button("FINALIZAR PDF"):
            st.session_state.lista_previa = []
            st.rerun()

    # Tabela de Pré-visualização
    st.markdown(f"<p style='text-align: center; font-size: 11px; margin:0;'>Lista: {len(st.session_state.lista_previa)}</p>", unsafe_allow_html=True)
    if st.session_state.lista_previa:
        df_vis = pd.DataFrame(st.session_state.lista_previa)
    else:
        df_vis = pd.DataFrame(columns=COLUNAS)
    
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=150)
