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

# --- CSS AVANÇADO (ESTILO INFOGRÁFICO) ---
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    
    /* MENU SLIM */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a1a1a; border-bottom: 2px solid #333;
        position: fixed; top: 0; left: 0; width: 100vw; z-index: 999; height: 32px;
    }
    .stTabs [data-baseweb="tab"] { color: #888; font-size: 12px; height: 32px; }
    .stTabs [aria-selected="true"] { color: #FF00FF !important; border-bottom: 2px solid #FF00FF !important; }

    /* CARTÕES ESTILO INFOGRÁFICO */
    .info-card {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
    }
    .card-pink { background: linear-gradient(90deg, #FF00FF, #800080); }
    .card-green { background: linear-gradient(90deg, #00FF00, #008000); }
    .card-blue { background: linear-gradient(90deg, #00FFFF, #0000FF); }
    .card-orange { background: linear-gradient(90deg, #FFA500, #FF4500); }

    /* AJUSTES DE INPUTS 25PX */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 2px; }
    div[data-testid="stTextInput"] > div { height: 25px !important; min-height: 25px !important; }
    .stTextInput input { background-color: white !important; color: black !important; height: 25px !important; font-size: 11px !important; }
    label { color: #FF00FF !important; font-size: 13px !important; font-weight: bold !important; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA RELATÓRIOS (ESTILO INFOGRÁFICO) ---
with tab_rel:
    st.markdown("<h2 style='text-align: center; color: #FF00FF;'>INFOGRAPHIC DASHBOARD</h2>", unsafe_allow_html=True)
    
    try:
        df = conn.read(ttl="0s").dropna(how='all')
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
            col_data = "Data Matrícula"
            df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            
            # FILTRO
            periodo = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            df_f = df.loc[(df[col_data].dt.date >= periodo[0]) & (df[col_data].dt.date <= periodo[1])] if len(periodo) == 2 else df

            # --- TOP CARDS (Information Activities) ---
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="info-card card-pink"><small>MATRÍCULAS</small><br><span style="font-size:24px">{len(df_f)}</span></div>', unsafe_allow_html=True)
            with c2: 
                atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                st.markdown(f'<div class="info-card card-green"><small>ATIVOS</small><br><span style="font-size:24px">{atv}</span></div>', unsafe_allow_html=True)
            with c3:
                cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df_f.columns else 0
                st.markdown(f'<div class="info-card card-blue"><small>CANCELADOS</small><br><span style="font-size:24px">{cnc}</span></div>', unsafe_allow_html=True)
            with c4:
                vend = df_f['Vendedor'].nunique() if 'Vendedor' in df_f.columns else 0
                st.markdown(f'<div class="info-card card-orange"><small>VENDEDORES</small><br><span style="font-size:24px">{vend}</span></div>', unsafe_allow_html=True)

            st.write("---")
            
            # --- MIDDLE SECTION (Statistics and Charts) ---
            col_left, col_right = st.columns([1, 1.2])
            
            with col_left:
                st.markdown("<p style='color:#FF00FF; font-weight:bold;'>▸ Statistics and analysis</p>", unsafe_allow_html=True)
                if 'STATUS' in df_f.columns:
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=df_f['STATUS'].value_counts().index,
                        values=df_f['STATUS'].value_counts().values,
                        hole=.7,
                        marker=dict(colors=['#FF00FF', '#00FFFF', '#FFA500', '#00FF00'])
                    )])
                    fig_donut.update_layout(template="plotly_dark", showlegend=True, paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(t=0,b=0,l=0,r=0))
                    st.plotly_chart(fig_donut, use_container_width=True)

            with col_right:
                st.markdown("<p style='color:#FF00FF; font-weight:bold;'>▸ Charts and Graphs (Cidades)</p>", unsafe_allow_html=True)
                df_cid = df_f['Cidade'].value_counts().reset_index()
                fig_area = px.area(df_cid, x='Cidade', y='count', markers=True)
                fig_area.update_traces(line_color='#FF00FF', fillcolor='rgba(255, 0, 255, 0.2)')
                fig_area.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
                st.plotly_chart(fig_area, use_container_width=True)

            # --- BOTTOM SECTION (Analytics) ---
            st.markdown("<p style='color:#FF00FF; font-weight:bold;'>▸ Analytics (Vendas por Vendedor)</p>", unsafe_allow_html=True)
            df_vend = df_f['Vendedor'].value_counts().reset_index()
            fig_bar = px.bar(df_vend, x='count', y='Vendedor', orientation='h', color='count', color_continuous_scale='Magma')
            fig_bar.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# --- ABA CADASTRO ---
with tab_cad:
    # (Mantive a lógica de cadastro anterior mas com o novo visual CSS)
    st.markdown("<h3 style='text-align: center; color: #FF00FF;'>CADASTRO DE ALUNOS</h3>", unsafe_allow_html=True)
    # ... (Restante do seu código de cadastro aqui)
