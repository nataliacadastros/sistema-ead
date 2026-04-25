import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials
from openpyxl import Workbook, load_workbook
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- CONEXÃO COM A PLANILHA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_usuarios():
    try:
        df = conn.read(worksheet="usuários", ttl="1s")
        return df.dropna(how='all')
    except Exception as e:
        return pd.DataFrame(columns=["usuario", "senha", "nivel"])

# --- CONTROLE DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_ativo = None
    st.session_state.nivel_ativo = None

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    
    .main .block-container { padding-top: 40px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    
    /* --- REGRA INDISPENSÁVEL DO CADASTRO (MANTIDA MAIÚSCULO NO CADASTRO) --- */
    .stTabs div[data-testid="stTextInput"] input { 
        text-transform: uppercase !important; 
    }

    /* --- ESTILO GERAL DOS INPUTS --- */
    div[data-testid="stTextInput"] input { 
        background-color: white !important; 
        color: black !important; 
        font-size: 12px !important; 
        height: 18px !important; 
        border-radius: 5px !important; 
    }
    
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: pre-wrap !important; }
    
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    .logo-container { position: relative; top: -10px; left: 0px; margin-bottom: 10px; }
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }

    /* --- ESTILO TELA DE LOGIN --- */
    .login-box { 
        background: rgba(18, 22, 41, 0.9); padding: 40px; border-radius: 15px; 
        border: 2px solid #1f295a; box-shadow: 0 0 30px rgba(0, 242, 255, 0.1);
        margin-top: 100px; text-align: center;
    }
    
    /* EXCEÇÃO EXCLUSIVA PARA A TELA DE LOGIN (Remove maiúsculo) */
    .login-box div[data-testid="stTextInput"] input {
        text-transform: none !important;
    }

    /* --- CORREÇÃO DO BOTÃO DE LOGIN (ROXO COM LETRA BRANCA) --- */
    /* Aplica a cor de fundo roxa (#bc13fe) e texto branco puro (#ffffff) */
    .login-box button {
        background-color: #bc13fe !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: none !important;
    }
    
    /* Efeito de hover para o botão de login */
    .login-box button:hover {
        background-color: #a30fdb !important; /* Roxo ligeiramente mais escuro no hover */
        box-shadow: 0 0 15px rgba(188, 19, 254, 0.6) !important; /* Brilho roxo */
    }

    /* --- ESTILO DOS DEMAIS BOTÕES DO SISTEMA (MANTIDO ORIGINAL) --- */
    div.stButton > button {
        background-color: #00f2ff !important;
        color: black !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background-color: #00d4df !important;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.6) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    _, centro_login, _ = st.columns([1, 1.2, 1])
    with centro_login:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        if os.path.exists(caminho_logo):
            st.image(caminho_logo, width=180)
        st.markdown("<h2 style='color: #00f2ff; margin-bottom:30px;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
        
        user_in = st.text_input("USUÁRIO", key="login_u_v3").strip()
        pass_in = st.text_input("SENHA", type="password", key="login_p_v3").strip()
        
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            df_users = carregar_usuarios()
            if not df_users.empty:
                # Compara ignorando maiúsculas/minúsculas na verificação interna
                valido = df_users[
                    (df_users['usuario'].astype(str).str.strip().str.upper() == user_in.upper()) & 
                    (df_users['senha'].astype(str).str.strip() == pass_in)
                ]
                if not valido.empty:
                    st.session_state.logado = True
                    st.session_state.usuario_ativo = user_in
                    st.session_state.nivel_ativo = str(valido.iloc[0]['nivel']).upper()
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
            else:
                st.error("Erro ao carregar banco de usuários.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ABAIXO TODO O RESTO DO SEU CÓDIGO ORIGINAL MANTIDO ---
# (Cadastro, Gerenciamento, Relatórios e Usuários)

ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                if isinstance(conteudo, dict) and "tags" in conteudo: return conteudo
                elif isinstance(conteudo, dict): return {"tags": conteudo, "last_selection": {}}
        except: return padrao
    return padrao

def salvar_tags(dados):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None
if "df_auto_ready" not in st.session_state: st.session_state.df_auto_ready = None

def safe_read():
    try: return conn.read(ttl="10s").dropna(how='all')
    except Exception as e: return pd.DataFrame()

def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None
    st.session_state.df_auto_ready = None

def extrair_valor_recebido(texto):
    if not texto: return 0.0
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    if match:
        try: return float(match.group(1).replace('.', '').replace(',', '.'))
        except: return 0.0
    return 0.0

def extrair_valor_geral(texto):
    if not texto: return 0.0
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def transformar_curso(chave):
    entrada = st.session_state[chave].strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper()
    else: st.session_state[chave] = entrada.upper()

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave])
    if len(valor) == 11: st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += "
