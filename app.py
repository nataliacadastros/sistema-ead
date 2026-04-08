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

# --- ARQUIVOS E PERSISTÊNCIA ---
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

if "dados_tags" not in st.session_state: st.session_state.dados_tags = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS HUD NEON COMPLETO ---
st.markdown("""
    <style>
    /* Estilos Gerais */
    .stApp { background-color: #0b0e1e; color: #e0e0e0; font-family: 'Courier New', Courier, monospace; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 2px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; text-transform: uppercase;}
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; text-shadow: 0 0 5px #00f2ff;}
    
    .main .block-container { padding-top: 15px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; text-shadow: 0 0 5px #00f2ff;}
    
    /* Configuração dos Campos Fixos */
    div[data-testid="stTextInput"] { width: 100% !important; margin-bottom: 5px !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    /* Estilos da Tabela Gerenciamento */
    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 1px solid #1f295a; border-radius: 10px; margin-top: 5px; box-shadow: 0 0 15px rgba(31, 41, 90, 0.5);}
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; text-shadow: 0 0 5px #00f2ff;}
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: pre-wrap !important; }
    
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* Estilos Relatório HUD */
    .card-hud-new {
        background: rgba(18, 22, 41, 0.5);
        border: 1px solid #1f295a;
        padding: 10px;
        border-radius: 8px;
        text-align: left;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
        box-shadow: 0 0 10px rgba(31, 41, 90, 0.3);
        height: 80px;
    }
    
    /* Cantos decorativos HUD */
    .card-hud-new::before { content: ''; position: absolute; top: 0; left: 0; width: 10px; height: 10px; border-top: 2px solid currentColor; border-left: 2px solid currentColor; }
    .card-hud-new::after { content: ''; position: absolute; bottom: 0; right: 0; width: 10px; height: 10px; border-bottom: 2px solid currentColor; border-right: 2px solid currentColor; }

    .hud-title { font-size: 10px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;}
    .hud-value { font-size: 24px; font-weight: bold; margin-top: -5px; text-shadow: 0 0 8px currentColor;}
    .hud-sub { font-size: 9px; color: #64748b; margin-top: -5px;}

    /* Cores Neon HUD */
    .hud-cyan { color: #00f2ff; }
    .hud-purple { color: #bc13fe; }
    .hud-pink { color: #ff007a; }
    .hud-green { color: #2ecc71; }

    /* Container de Gráfico HUD */
    .chart-container-hud {
        background: rgba(18, 22, 41, 0.3);
        border: 1px solid #1f295a;
        border-radius: 8px;
        padding: 15px;
        position: relative;
        margin-top: 10px;
        box-shadow: 0 0 15px rgba(31, 41, 90, 0.2);
    }
    
    .chart-container-hud::before {
        content: '';
        position: absolute;
        top: 10px; left: 10px; right: 10px;
        height: 1px;
        background: linear-gradient(90deg, rgba(31, 41, 90, 0), rgba(31, 41, 90, 1), rgba(31, 41, 90, 0));
    }

    .stDateInput div[data-baseweb="input"] {
        background-color: #121629 !important;
        border: 1px solid #1f295a !important;
        color: #00f2ff !important;
        border-radius: 4px !important;
        font-size: 11px !important;
    }
    
    /* Barra de progresso Cidade */
    .hud-city-bar-container { background: rgba(31, 41, 90, 0.2); height: 10px; border-radius: 5px; width: 100%; position: relative; margin: 10px 0; border: 1px solid #1f295a; overflow: hidden;}
    .hud-city-segment { height: 100%; float: left; position: relative; border-right: 1px solid #0b0e1e;}
    .hud-city-legend { display: flex; justify-content: start; gap: 15px; font-size: 9px; margin-top: -5px;}
    .legend-item { display: flex; align-items: center; gap: 5px; text-transform: uppercase;}
    .legend-color { width: 8px; height: 8px; border-radius: 2px;}

    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stVerticalBlock"] > div:first-child { margin-top: -15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO COM LOGO ---
if os.path.exists(caminho_logo):
    c_logo, c_vazio = st.columns([0.1, 0.9])
    with c_logo: st.image(caminho_logo, width=75)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try: return conn.read(ttl="10s").dropna(how='all')
    except Exception as e: st.error(f"Erro de conexão: {e}"); return pd.DataFrame()

# --- ESTADOS DE SESSÃO GERAIS ---
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- FUNÇÕES AUXILIARES DE EXTRAÇÃO ---
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

# --- NAVEGAÇÃO ---
tab_rel, tab_ger = st.tabs(["📊 RELATÓRIOS (HUD)", "🖥️ GERENCIAMENTO"])

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        
        iv = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido)
            df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
            
            # --- SEÇÃO 1: MÉTRICAS HUD ---
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1: st.markdown(f'<div class="card-hud-new hud-cyan"><div class="hud-title">Matrículas</div><div class="hud-value">{len(df_f)}</div><div class="hud-sub">Período selecionado</div></div>', unsafe_allow_html=True)
            ativos = len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])
            with c2: st.markdown(f'<div class="card-hud-new hud-green"><div class="hud-title">Ativos</div><div class="hud-value">{ativos}</div><div class="hud-sub">{(ativos/len(df_f))*100 if len(df_f)>0 else 0:.0f}% do total</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="card-hud-new hud-pink"><div class="hud-title">Cancelados</div><div class="hud-value">{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</div><div class="hud-sub">Ações pendentes</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="card-hud-new hud-cyan"><div class="hud-title">Recebido</div><div class="hud-value" style="font-size:20px">R${df_f["v_rec"].sum():,.2f}</div><div class="hud-sub">Valor em caixa</div></div>', unsafe_allow_html=True)
            tm_b = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]['v_tic'].mean() or 0.0
            tm_c = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic'].mean() or 0.0
            with c5: st.markdown(f'<div class="card-hud-new hud-purple"><div class="hud-title">Ticket Médio</div><div class="hud-sub">Bol: R${tm_b:.0f}</div><div class="hud-sub">Car: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
            
            # --- SEÇÃO 2: GRÁFICOS HUD ---
            g1, g2 = st.columns([1, 1])
            
            # Gráfico Pizza: Status Geral
            with g1:
                st.markdown('<div class="chart-container-hud">', unsafe_allow_html=True)
                st.markdown('<p class="hud-title hud-cyan">Distribuição de Status</p>', unsafe_allow_html=True)
                figp = go.Figure(data=[go.Pie(
                    labels=df_f['STATUS'].value_counts().index, 
                    values=df_f['STATUS'].value_counts().values, 
                    hole=0.6,
                    marker=dict(colors=['#2ecc71', '#ff007a'], line=dict(color='#0b0e1e', width=2))
                )])
                figp.update_layout(
                    template="plotly_dark", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(font=dict(size=10, color="#e0e0e0")),
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=250
                )
                st.plotly_chart(figp, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # --- MELHORIA: RANKING VENDEDORES EM PIZZA HUD ---
            with g2:
                st.markdown('<div class="chart-container-hud">', unsafe_allow_html=True)
                st.markdown('<p class="hud-title hud-purple">Ranking por Vendedor</p>', unsafe_allow_html=True)
                dfv = df_f["Vendedor"].value_counts().reset_index()
                
                # Formata rótulo da legenda: Nome (Quantidade)
                dfv['Label'] = dfv.apply(lambda row: f"{row['Vendedor']} ({row['count']})", axis=1)

                # Gráfico de Pizza (Rosca) HUD Neon
                figv = go.Figure(data=[go.Pie(
                    labels=dfv['Label'], 
                    values=dfv['count'], 
                    hole=0.6,
                    # Degradês ciano/roxo baseados nas referências
                    marker=dict(colors=['#00f2ff', '#bc13fe', '#ff007a', '#2ecc71', '#ff9f43'], 
                                line=dict(color='#0b0e1e', width=2))
                )])
                
                figv.update_layout(
                    template="plotly_dark", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(font=dict(size=9, color="#e0e0e0"), textprefix='', orientation="v"),
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=250
                )
                st.plotly_chart(figv, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # --- SEÇÃO 3: CIDADES HUD ---
            st.markdown('<div class="chart-container-hud" style="margin-top:20px;">', unsafe_allow_html=True)
            st.markdown('<p class="hud-title hud-green">Volume por Cidade</p>', unsafe_allow_html=True)
            df_cv = df_f['Cidade'].value_counts().head(5)
            if not df_cv.empty:
                t_c = df_cv.sum()
                cores_cidades = ["#00f2ff", "#bc13fe", "#ff007a", "#2ecc71", "#ff9f43"]
                segmentos_html = "".join([f'<div class="hud-city-segment" style="width:{(q/t_c)*100}%; background:{cores_cidades[i%5]}; box-shadow: 0 0 10px {cores_cidades[i%5]}80;"></div>' for i, (n, q) in enumerate(df_cv.items())])
                st.markdown(f'<div class="hud-city-bar-container">{segmentos_html}</div>', unsafe_allow_html=True)
                legenda_html = "".join([f'<div class="legend-item"><div class="legend-color" style="background:{cores_cidades[i%5]};"></div><span style="color:{cores_cidades[i%5]}">{n} ({q})</span></div>' for i, (n, q) in enumerate(df_cv.items())])
                st.markdown(f'<div class="hud-city-legend">{legenda_html}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: GERENCIAMENTO (Mantida) ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar Aluno...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    with cf4: 
        if st.button("🔄", key="btn_ref"): st.cache_data.clear(); st.rerun()
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]
        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            rows += f"<tr><td><span class='status-badge {'status-ativo' if r['STATUS']=='ATIVO' else 'status-cancelado'}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold;text-shadow:0 0 5px #00f2ff;'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold;text-shadow:0 0 5px #00f2ff;'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in df_g.columns]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
