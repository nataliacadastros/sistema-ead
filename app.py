import streamlit as st
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ESTÉTICA HUD NEON ---
st.markdown("""
    <style>
    /* Fundo Azul Profundo */
    .stApp { 
        background-color: #0b0e1e; 
        color: #e0e0e0; 
    }
    
    /* Menu Slim HUD */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; 
        border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0; width: 100vw; z-index: 999; height: 35px;
    }
    .stTabs [data-baseweb="tab"] { 
        color: #64748b !important; 
        font-size: 11px !important;
    }
    .stTabs [aria-selected="true"] { 
        color: #00f2ff !important; 
        border-bottom: 2px solid #00f2ff !important;
        background-color: rgba(0, 242, 255, 0.05) !important;
    }

    /* Cards com Efeito de Brilho (Glow) */
    .card-hud {
        background: rgba(18, 22, 41, 0.7);
        border: 1px solid #1f295a;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
    }
    .card-hud small { 
        color: #64748b; 
        text-transform: uppercase; 
        letter-spacing: 2px; 
        font-size: 10px;
    }
    .card-hud h2 { 
        margin: 5px 0; 
        font-family: 'Courier New', monospace;
        font-weight: bold;
    }

    /* Cores Neon específicas para os Cards */
    .neon-pink { color: #ff007a; text-shadow: 0 0 10px rgba(255, 0, 122, 0.5); border-top: 2px solid #ff007a; }
    .neon-green { color: #39ff14; text-shadow: 0 0 10px rgba(57, 255, 20, 0.5); border-top: 2px solid #39ff14; }
    .neon-blue { color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5); border-top: 2px solid #bc13fe; }

    /* Barra de Cidades Estilo HUD */
    .hud-bar-container {
        background: rgba(31, 41, 90, 0.3);
        height: 12px;
        border-radius: 20px;
        width: 100%;
        position: relative;
        margin: 45px 0 20px 0;
        border: 1px solid #1f295a;
    }
    .hud-segment {
        height: 100%;
        float: left;
        position: relative;
        box-shadow: 0 0 10px rgba(0,0,0,0.5);
    }
    .hud-label {
        position: absolute;
        top: -35px;
        left: 50%;
        transform: translateX(-50%);
        background: #121629;
        border: 1px solid currentColor;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: bold;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def exibir_relatorios():
    try:
        df = conn.read(ttl="0s").dropna(how='all')
        if not df.empty:
            df.columns = [c.strip() for c in df.columns]
            col_data = "Data Matrícula"
            df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            
            # Filtro HUD
            st.markdown("<small style='color:#64748b'>FILTRAR FREQUÊNCIA DE DADOS</small>", unsafe_allow_html=True)
            periodo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), label_visibility="collapsed")
            
            if len(periodo) == 2:
                df_f = df.loc[(df[col_data].dt.date >= periodo[0]) & (df[col_data].dt.date <= periodo[1])]
                
                # CARDS ESTILO HUD
                st.write("")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Matrículas</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: 
                    atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df.columns else 0
                    st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{atv}</h2></div>', unsafe_allow_html=True)
                with c3:
                    cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df.columns else 0
                    st.markdown(f'<div class="card-hud neon-blue"><small>Cancelados</small><h2>{cnc}</h2></div>', unsafe_allow_html=True)
                with c4:
                    # Unificação de vendedores Gilson
                    df_f['Vendedor'] = df_f['Vendedor'].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
                    top_v = df_f['Vendedor'].value_counts().idxmax() if not df_f.empty else "N/A"
                    st.markdown(f'<div class="card-hud neon-purple"><small>Top Performer</small><h2 style="font-size:18px">{top_v}</h2></div>', unsafe_allow_html=True)

                st.write("---")
                
                # CIDADES ESTILO INFOGRÁFICO HUD
                st.markdown("<small style='color:#00f2ff'>▸ ANALYTICS: GEOLOCALIZAÇÃO</small>", unsafe_allow_html=True)
                df_cid = df_f['Cidade'].value_counts().head(4)
                if not df_cid.empty:
                    total = df_cid.sum()
                    cores = ["#ff007a", "#39ff14", "#00f2ff", "#bc13fe"]
                    
                    seg_html = ""
                    for i, (nome, qtd) in enumerate(df_cid.items()):
                        percent = (qtd / total) * 100
                        cor = cores[i % 4]
                        seg_html += f'''
                        <div class="hud-segment" style="width: {percent}%; background: {cor}; box-shadow: 0 0 10px {cor}80;">
                            <div class="hud-label" style="color: {cor};">{qtd}</div>
                        </div>'''
                    
                    st.markdown(f'<div class="hud-bar-container">{seg_html}</div>', unsafe_allow_html=True)

                # GRÁFICOS HUD (PLOTLY)
                st.write("")
                g1, g2 = st.columns([1, 1.2])
                
                with g1:
                    st.markdown("<small style='color:#64748b'>STATUS DISTRIBUTION</small>", unsafe_allow_html=True)
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=df_f['STATUS'].unique(), 
                        values=df_f['STATUS'].value_counts(),
                        hole=0.8,
                        marker=dict(colors=['#ff007a', '#00f2ff', '#39ff14'])
                    )])
                    fig_pie.update_layout(
                        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=300,
                        margin=dict(t=0, b=0, l=0, r=0)
                    )
                    fig_pie.update_traces(textinfo='label+percent', textfont_size=10)
                    st.plotly_chart(fig_pie, use_container_width=True)

                with g2:
                    st.markdown("<small style='color:#64748b'>PERFORMANCE POR VENDEDOR</small>", unsafe_allow_html=True)
                    df_v = df_f['Vendedor'].value_counts().reset_index()
                    fig_v = px.line(df_v, x='Vendedor', y='count', markers=True)
                    fig_v.update_traces(line_color='#00f2ff', marker=dict(size=10, color='#bc13fe', line=dict(width=2, color='#fff')))
                    fig_v.update_layout(
                        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)', height=300,
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#1f295a')
                    )
                    st.plotly_chart(fig_v, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao carregar HUD: {e}")

# Executa
exibir_relatorios()
