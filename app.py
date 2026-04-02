import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS CONSOLIDADO (CADASTRO FIEL AO ORIGINAL + RELATÓRIO INFOGRÁFICO) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    
    /* MENU SLIM NO TOPO */
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #1a3a5a; border-bottom: 2px solid #2c5282;
        position: fixed;
        top: 0;
        left: 0 !important;
        width: 100vw !important;
        z-index: 999;
        justify-content: center;
        height: 32px !important;
    }
    .stTabs [data-baseweb="tab"] { 
        color: #ffffff !important; font-weight: 600; padding: 0px 30px !important;
        height: 32px !important; line-height: 32px !important; font-size: 13px !important;
    }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #2ecc71 !important; }
    
    .main .block-container { 
        padding-top: 38px !important; 
        max-width: 1100px !important;
        margin: 0 auto !important;
    }

    /* --- ESTILO ABA CADASTRO (RESTAURADO) --- */
    div[data-testid="stHorizontalBlock"] { 
        margin-bottom: 3px !important;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    div[data-testid="stTextInput"] > div { 
        min-height: 25px !important; 
        height: 25px !important;
        width: 100% !important;
    }

    label { 
        color: #2ecc71 !important; 
        font-weight: bold !important; 
        font-size: 15px !important; 
        padding-right: 15px !important; 
        height: 25px !important;
        display: flex; 
        align-items: center; 
        justify-content: flex-end;
    }

    .stTextInput input { 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        font-size: 12px !important;
        height: 25px !important;
        border-radius: 5px !important;
    }

    .stCheckbox { display: flex; justify-content: center; margin-top: 8px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }
    
    .stButton > button {
        background-color: #2ecc71 !important; color: white !important; font-weight: bold !important;
        border-radius: 5px !important;
    }

    /* --- ESTILO ABA RELATÓRIO (INFOGRÁFICO) --- */
    .info-card {
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
        border-bottom: 4px solid rgba(0,0,0,0.2);
    }
    .card-pink { background: linear-gradient(90deg, #FF00FF, #800080); }
    .card-green { background: linear-gradient(90deg, #00FF00, #008000); }
    .card-blue { background: linear-gradient(90deg, #00FFFF, #0000FF); }
    .card-orange { background: linear-gradient(90deg, #FFA500, #FF4500); }

    .titulo-rel {
        color: #FF00FF;
        font-weight: bold;
        font-size: 14px;
        margin-top: 20px;
    }
    
    /* Esconder o cabeçalho padrão e a aba cadastro/gerenciamento */
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ABA DE RELATÓRIOS (ÚNICA EXIBIDA) ---
try:
    df_rel = conn.read(ttl="0s").dropna(how='all')
    if not df_rel.empty:
        df_rel.columns = [c.strip() for c in df_rel.columns]
        
        # --- LÓGICA DE UNIFICAÇÃO DE VENDEDORES (GILSON - COLÉGIO -> GILSON) ---
        if 'Vendedor' in df_rel.columns:
            df_rel['Vendedor'] = df_rel['Vendedor'].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
        
        col_data = "Data Matrícula"
        df_rel[col_data] = pd.to_datetime(df_rel[col_data], dayfirst=True, errors='coerce')
        
        st.markdown("<p style='color: #2ecc71; font-weight: bold; margin-bottom: 5px;'>Filtro de Período:</p>", unsafe_allow_html=True)
        # O seletor já começa selecionado, mostrando o relatório dos últimos 7 dias.
        intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY", label_visibility="collapsed")
        
        # Só executa se tivermos data de início e fim.
        if isinstance(intervalo, (tuple, list)) and len(intervalo) == 2:
            d_ini, d_fim = intervalo
            df_f = df_rel.loc[(df_rel[col_data].dt.date >= d_ini) & (df_rel[col_data].dt.date <= d_fim)]
            
            if not df_f.empty:
                st.write("---")
                
                # --- TOP CARDS (KPIs) ---
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="info-card card-pink"><small>MATRÍCULAS</small><br><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: 
                    atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="info-card card-green"><small>ATIVOS</small><br><h2>{atv}</h2></div>', unsafe_allow_html=True)
                with c3:
                    cnc = len(df_f[df_f['STATUS'].str.upper() == 'CANCELADO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="info-card card-blue"><small>CANCELADOS</small><br><h2>{cnc}</h2></div>', unsafe_allow_html=True)
                with c4:
                    # Encontrar o vendedor com mais vendas no período
                    if 'Vendedor' in df_f.columns and not df_f.empty:
                        counts = df_f['Vendedor'].value_counts()
                        # idxmax() retorna o índice (nome do vendedor) com o maior valor
                        top_vendedor = counts.idxmax() if not counts.empty else "N/A"
                    else:
                        top_vendedor = "N/A"
                    st.markdown(f'<div class="info-card card-orange"><small>MAIOR DESEMPENHO EM CAPTAÇÃO DE ALUNOS</small><br><h2 style="font-size: 18px;">{top_vendedor}</h2></div>', unsafe_allow_html=True)

                st.write("---")
                
                # --- SEÇÃO CIDADES (INFOGRÁFICO BARRA SEGMENTADA) ---
                st.markdown('<p style="color:#FF00FF; font-weight:bold;">▸ Information activities (Cidades)</p>', unsafe_allow_html=True)
                df_cid = df_f['Cidade'].value_counts().head(4) # Pegar top 4 cidades
                if not df_cid.empty:
                    total_cid = df_cid.sum()
                    cores = ["#FF00FF", "#8AFF00", "#00C2FF", "#FFB800"] # Rosa, Verde, Azul, Laranja
                    grads = ["linear-gradient(90deg, #FF00FF, #800080)", "linear-gradient(90deg, #8AFF00, #4D8F00)", 
                             "linear-gradient(90deg, #00C2FF, #006080)", "linear-gradient(90deg, #FFB800, #996E00)"]
                    
                    seg_html = ""
                    leg_html = ""
                    for i, (nome, qtd) in enumerate(df_cid.items()):
                        percent = (qtd / total_cid) * 100
                        cor = cores[i % 4]; grad = grads[i % 4]
                        
                        # Arredondar bordas apenas nas pontas da barra total
                        border_rad = "20px 0 0 20px" if i==0 else ("0 20px 20px 0" if i==len(df_cid)-1 else "0")
                        
                        seg_html += f'<div class="segmento" style="width: {percent}%; background: {grad}; border-radius: {border_rad};"><div class="etiqueta" style="background: {cor};">{qtd}</div></div>'
                        leg_html += f'<div class="legenda-item"><div class="ponto" style="background: {cor};"></div><span>{nome}</span></div>'
                    
                    # Usar f-string para encapsular todo o HTML e garantir a renderização
                    html_final = f"""
                    <div class="container-cidades">
                        <div class="barra-segmentada">
                            {seg_html}
                        </div>
                        <div class="legenda-container">
                            {leg_html}
                        </div>
                    </div>
                    """
                    st.markdown(html_final, unsafe_allow_html=True)

                st.write("---")
                
                # --- GRÁFICOS INFERIORES (STATUS E VENDEDORES) ---
                col_g1, col_g2 = st.columns([1, 1])
                
                with col_g1:
                    st.markdown('<p style="color:#FF00FF; font-weight:bold;">▸ Statistics and analysis (Status)</p>', unsafe_allow_html=True)
                    if 'STATUS' in df_f.columns:
                        fig_p = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, 
                                                       values=df_f['STATUS'].value_counts().values, 
                                                       hole=.7, # Gráfico de Rosca
                                                       marker=dict(colors=['#FF00FF', '#00FFFF', '#FFA500']))])
                        # Configuração do visual: fundo transparente, sem legenda externa, textos internos
                        fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, 
                                            height=350, margin=dict(t=30,b=30,l=30,r=30))
                        fig_p.update_traces(textinfo='label+percent', textposition='inside')
                        st.plotly_chart(fig_p, use_container_width=True)
                
                with col_g2:
                    st.markdown('<p style="color:#FF00FF; font-weight:bold;">▸ Analytics (Top Divulgadores)</p>', unsafe_allow_html=True)
                    # Preparar dados para o gráfico de barras
                    df_vend_chart = df_f['Vendedor'].value_counts().reset_index()
                    df_vend_chart.columns = ['Vendedor', 'Vendas']
                    # Gráfico de barras horizontal, top 10 vendedores
                    fig_v = px.bar(df_vend_chart.head(10), x='Vendas', y='Vendedor', 
                                   orientation='h', color='Vendas', color_continuous_scale='Magma')
                    fig_v.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', 
                                        plot_bgcolor='rgba(0,0,0,0)', height=350, showlegend=False)
                    st.plotly_chart(fig_v, use_container_width=True)
            else:
                st.warning(f"Nenhum registro encontrado para o período: {d_ini.strftime('%d/%m/%Y')} até {d_fim.strftime('%d/%m/%Y')}.")
        else:
            st.info("Selecione a data final no calendário para carregar o relatório.")
    else:
        st.info("Aguardando registros ou planilha vazia para gerar relatórios.")
            
except Exception as e:
    st.error(f"Erro ao processar o Dashboard: {e}")
