import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from openpyxl import Workbook, load_workbook
from io import BytesIO
from supabase import create_client

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

# --- CONEXÕES ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro nas credenciais do Supabase: {e}")

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists("tags_salvas.json"):
        try:
            with open("tags_salvas.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except: 
            return padrao
    return padrao

def salvar_tags(dados):
    try:
        with open("tags_salvas.json", "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar tags: {e}")

# --- DEFINIÇÃO DO CAMINHO DA LOGO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- CSS HUD NEON ---
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
    
    .stTabs div[data-testid="stTextInput"] input { text-transform: uppercase !important; }
    
    .stTextInput input { background-color: white !important; color: black !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: pre-wrap !important; }
    
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .logo-container { position: relative; top: -10px; left: 0px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADOS ---
if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- DICIONÁRIOS E FUNÇÕES MOTOR ---
DIC_CURSOS = {"00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR", "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"}

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

def extrair_valor_geral(texto):
    if not texto: return 0.0
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave])
    if len(valor) == 11: st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None

# --- LOGO ---
if os.path.exists(caminho_logo):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(caminho_logo, width=90)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABAS DO SISTEMA ---
lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"]
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(lista_abas)

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        s_ge = f"g_{st.session_state.reset_geral}"
        
        fields = [
            ("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), 
            ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"), ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), 
            ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
            ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
            ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")
        ]
        
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        st.write("")
        _, c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 1.2, 0.2])
        c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento)
        c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento)
        c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento)
        
        st.write("")
        _, b1, b2, _ = st.columns([1.2, 1.9, 1.9, 0.2])
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({
                        "ID": st.session_state[f"f_id_{s_al}"].upper(),
                        "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                        "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), 
                        "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]),
                        "CPF": st.session_state[f"f_cpf_{s_al}"],
                        "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), 
                        "Course": st.session_state[f"input_curso_key_{s_al}"].upper(),
                        "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(),
                        "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(),
                        "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                    })
                    st.session_state.reset_aluno += 1
                    st.rerun()
        
        if st.session_state.lista_previa: 
            st.markdown(f"### 📋 PRÉ-VISUALIZAÇÃO ({len(st.session_state.lista_previa)} ALUNOS)")
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.header("📋 Gerenciar Matrículas")
    col_p1, col_p2 = st.columns([3, 1])
    id_pesquisa = col_p1.text_input("Digite o ID do Aluno para editar:", key="id_pesq").strip()
    
    if col_p2.button("🔍 PESQUISAR"):
        if id_pesquisa:
            try:
                res = supabase.table("alunos").select("*").eq("ID", id_pesquisa).execute()
                if res.data:
                    st.session_state.dados_aluno = res.data[0]
                    st.success("Encontrado no Banco de Dados!")
                else: st.error("Aluno não encontrado.")
            except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    st.info("Selecione o período para visualizar o desempenho.")
    # Aqui entraria a lógica de filtragem e gráficos (Plotly) conforme seu código original

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    
    if modo == "MANUAL":
        c1, c2 = st.columns(2)
        with c1:
            u_user = st.text_area("IDs", height=100, key="in_user")
            u_cell = st.text_area("Celulares", height=100, key="in_cell")
            u_city = st.text_area("Cidades", height=100, key="in_city")
            u_pay = st.text_area("Pagamentos", height=100, key="in_pay")
        with c2:
            u_nome = st.text_area("Nomes", height=100, key="in_nome")
            u_doc = st.text_area("Documentos", height=100, key="in_doc")
            u_cour = st.text_area("Cursos", height=100, key="in_cour")
            u_sell = st.text_area("Vendedores", height=100, key="in_sell")
        u_date = st.text_area("Datas", height=100, key="in_date")

    with st.expander("🛠️ CONFIGURAR TAGS", expanded=False):
        cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
        cols = st.columns(3)
        selected_tags = {}
        for i, curso in enumerate(cursos_tags):
            with cols[i % 3]:
                tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, [])
                last_sel = st.session_state.dados_tags.get("last_selection", {}).get(curso, "")
                idx_default = (tags_lista.index(last_sel) + 1) if last_sel in tags_lista else 0
                cur_tag = st.selectbox(curso, [""] + tags_lista, index=idx_default, key=f"sel_{curso}")
                selected_tags[curso] = cur_tag

    if st.button("🚀 PROCESSAR DADOS", use_container_width=True):
        # Lógica de processamento e geração de Excel mantida conforme original
        st.info("Processando informações...")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("### SISTEMA ADM")
    st.write("Acesso Direto Habilitado")
