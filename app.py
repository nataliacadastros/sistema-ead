import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS CONSOLIDADO (EFEITOS TECH + MEDIDAS EXATAS) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    /* MENU SLIM NO TOPO */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a3a5a; border-bottom: 2px solid #2c5282;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 32px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; font-weight: 600; padding: 0px 30px !important; height: 32px !important; line-height: 32px !important; font-size: 13px !important; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #2ecc71 !important; }
    
    /* CONTEÚDO GERAL */
    .main .block-container { padding-top: 38px !important; max-width: 1100px !important; margin: 0 auto !important; }

    /* CAMPOS DE CADASTRO (25PX) */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 3px !important; display: flex; align-items: center; justify-content: center; }
    div[data-testid="stTextInput"] > div { min-height: 25px !important; height: 25px !important; width: 100% !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 15px !important; padding-right: 15px !important; height: 25px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }

    /* ESTILO DOS CARDS TECH (RELATÓRIO) */
    .card-tech {
        background-color: #1a3a5a; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border-bottom: 4px solid #2ecc71;
        box-shadow: 0px 4px 15px rgba(46, 204, 113, 0.2);
    }
    .card-tech small { color: #bdc3c7; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }
    .card-tech h2 { margin: 5px 0 0 0; color: white; font-size: 28px; }

    /* BOTÕES */
    .stButton > button { background-color: #2ecc71 !important; color: white !important; font-weight: bold !important; border-radius: 5px !important; }
    div[data-testid="column"] .stButton > button { height: 40px !important; width: 90% !important; }
    
    /* ESCONDER INTERFACE DO STREAMLIT */
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "val_curso" not in st.session_state: st.session_state.val_curso = ""
if "val_pagto" not in st.session_state: st.session_state.val_pagto = ""

# --- FUNÇÕES ---
def transformar_curso():
    entrada = st.session_state.input_curso_key.strip()
    if not entrada: st.session_state.val_curso = ""; st.session_state.input_curso_key = ""; return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state.val_curso = f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)
        else: st.session_state.val_curso = entrada.upper()
    else: st.session_state.val_curso = entrada.upper()
    st.session_state.val_curso = st.session_state.val_curso.upper().strip() + " "
    st.session_state.input_curso_key = st.session_state.val_curso

def processar_pagto():
    base = st.session_state.input_pagto_key.split(" | ")[0].strip().upper()
    obs = []
    if st.session_state.chk_1: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if st.session_state.chk_2: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if st.session_state.chk_3: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    st.session_state.val_pagto = f"{base} | {' | '.join(obs)}" if obs else base
    st.session_state.input_pagto_key = st.session_state.val_pagto

# --- UI ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        campos = [("ID:", "f_id", None), ("ALUNO:", "f_nome", None), ("CIDADE:", "f_cid", None), ("CURSO:", "input_curso_key", transformar_curso), ("PAGAMENTO:", "input_pagto_key", None), ("VENDEDOR:", "f_vend", None), ("DATA MATRÍCULA:", "f_data", None)]
        for label, key, func in campos:
            c_lab, c_inp = st.columns([1.5, 3.5]) 
            c_lab.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if key == "input_curso_key": c_inp.text_input(label, key=key, value=st.session_state.val_curso, on_change=func, label_visibility="collapsed")
            elif key == "input_pagto_key": c_inp.text_input(label, key=key, value=st.session_state.val_pagto, label_visibility="collapsed")
            elif key == "f_data": c_inp.text_input(label, key=key, value=date.today().strftime("%d/%m/%Y"), label_visibility="collapsed")
            else: c_inp.text_input(label, key=key, label_visibility="collapsed")
        
        _, c_c1, c_c2, c_c3, _ = st.columns([0.8, 1.2, 1.2, 1.2, 0.8])
        with c_c1: st.checkbox("LIB. IN-GLÊS", key="chk_1", on_change=processar_pagto)
        with c_c2: st.checkbox("CURSO BÔNUS", key="chk_2", on_change=processar_pagto)
        with c_c3: st.checkbox("CONFIRMAÇÃO", key="chk_3", on_change=processar_pagto)
        
        st.write("")
        _, b_l, b_r, _ = st.columns([0.5, 2, 2, 0.5])
        with b_l:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.f_nome:
                    aluno = {"ID": st.session_state.f_id.upper(), "Aluno": st.session_state.f_nome.upper(), "Cidade": st.session_state.f_cid.upper(), "Curso": st.session_state.input_curso_key.strip(), "Pagamento": st.session_state.input_pagto_key.upper(), "Vendedor": st.session_state.f_vend.upper(), "Data Matrícula": st.session_state.f_data}
                    st.session_state.lista_previa.append(aluno)
                    st.rerun()
        with b_r:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    df_old = conn.read(ttl="0s").fillna(""); df_new = pd.DataFrame(st.session_state.lista_previa)
                    conn.update(data=pd.concat([df_old, df_new], ignore_index=True))
                    st.session_state.lista_previa = []; st.success("Enviado!"); st.rerun()
        
        st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

with tab_ger:
    st.markdown("<h3 style='text-align: center; color: #2ecc71;'>🖥️ BASE DE DADOS</h3>", unsafe_allow_html=True)
    try:
        dados = conn.read(ttl="0s").fillna("")
        if not dados.empty:
            if "ID" in dados.columns: dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
            st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=500)
            if st.button("🔄 ATUALIZAR LISTA"): st.cache_data.clear(); st.rerun()
    except: st.error("Erro ao carregar dados.")

with tab_rel:
    st.markdown("<h3 style='text-align: center; color: #2ecc71;'>📊 DASHBOARD ANALÍTICO</h3>", unsafe_allow_html=True)
    
    try:
        df_rel = conn.read(ttl="0s").fillna("")
        if not df_rel.empty:
            col_data = "Data Matrícula"
            df_rel[col_data] = pd.to_datetime(df_rel[col_data], dayfirst=True, errors='coerce')
            df_rel = df_rel.dropna(subset=[col_data])
            
            # --- FILTRO PORTUGUÊS ---
            st.markdown("<p style='color: #2ecc71; font-weight: bold; margin-bottom: -10px;'>Selecione o período:</p>", unsafe_allow_html=True)
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY", label_visibility="collapsed")
            
            if isinstance(intervalo, (list, tuple)) and len(intervalo) == 2:
                d_ini, d_fim = intervalo
                df_f = df_rel.loc[(df_rel[col_data].dt.date >= d_ini) & (df_rel[col_data].dt.date <= d_fim)]
                
                if not df_f.empty:
                    st.write("---")
                    # --- CARDS TECH ---
                    c1, c2, c3 = st.columns(3)
                    with c1: st.markdown(f'<div class="card-tech"><small>Matrículas</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                    with c2: 
                        v_top = df_f['Vendedor'].value_counts().idxmax() if 'Vendedor' in df_f.columns else "N/A"
                        st.markdown(f'<div class="card-tech" style="border-color: #f1c40f;"><small>Top Vendedor</small><h2 style="font-size: 20px;">{v_top}</h2></div>', unsafe_allow_html=True)
                    with c3:
                        atv = len(df_f[df_f['Status'].str.upper() == 'ATIVO']) if 'Status' in df_f.columns else 0
                        st.markdown(f'<div class="card-tech" style="border-color: #3498db;"><small>Ativos</small><h2>{atv}</h2></div>', unsafe_allow_html=True)

                    st.write("")
                    # --- GRÁFICOS TECH (PLOTLY NEON) ---
                    g1, g2 = st.columns(2)
                    with g1:
                        st.markdown("<p style='text-align:center; color:#2ecc71; font-size:12px;'>RANKING POR CIDADE</p>", unsafe_allow_html=True)
                        fig_c = px.bar(df_f['Cidade'].value_counts().reset_index(), x='count', y='Cidade', orientation='h', color='count', color_continuous_scale='Viridis')
                        fig_c.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
                        st.plotly_chart(fig_c, use_container_width=True)
                    
                    with g2:
                        st.markdown("<p style='text-align:center; color:#2ecc71; font-size:12px;'>STATUS GERAL</p>", unsafe_allow_html=True)
                        fig_p = px.pie(df_f, names='Status', hole=0.7, color_discrete_sequence=['#2ecc71', '#e74c3c', '#f1c40f'])
                        fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=20, b=20, l=20, r=20))
                        fig_p.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#1a2436', width=2)))
                        st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.warning("Nenhum dado no período.")
    except Exception as e: st.error(f"Erro: {e}")
