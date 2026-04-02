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
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 20px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
    .main .block-container { padding-top: 45px !important; max-width: 1200px !important; margin: 0 auto !important; }

    /* CARDS RELATÓRIO HUD */
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; }
    .neon-pink { color: #ff007a; text-shadow: 0 0 10px rgba(255, 0, 122, 0.5); border-top: 2px solid #ff007a; }
    .neon-green { color: #39ff14; text-shadow: 0 0 10px rgba(57, 255, 20, 0.5); border-top: 2px solid #39ff14; }
    .neon-blue { color: #00f2ff; text-shadow: 0 0 10px rgba(0, 242, 255, 0.5); border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; text-shadow: 0 0 10px rgba(188, 19, 254, 0.5); border-top: 2px solid #bc13fe; }
    
    .tm-container { display: flex; flex-direction: column; justify-content: center; height: 100%; }
    .tm-item { font-size: 14px; margin: 2px 0; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE CÁLCULO FINANCEIRO ---
def extrair_valor_recebido(texto):
    """
    Regra: Busca o valor numérico que aparece IMEDIATAMENTE após a palavra 'PAGO' ou 'PAGA'.
    Ex: 'TAXA R$50 PAGA VIA PIX' -> extrai 50
    """
    texto = str(texto).upper()
    # Busca 'PAGO', 'PAGA' ou 'PAGOS' seguido opcionalmente de 'R$', espaços e o número
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', texto)
    if match:
        valor_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return float(valor_str)
        except:
            return 0.0
    return 0.0

def extrair_valor_geral(texto):
    """Extrai o primeiro valor numérico que encontrar (para ticket médio)"""
    try:
        valores = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(valores[0]) if valores else 0.0
    except: return 0.0

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LÓGICA DE ABAS (CADASTRO E GERENCIAMENTO OMITIDOS NO EXEMPLO MAS MANTIDOS NO SISTEMA) ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_rel:
    try:
        df_rel = conn.read(ttl="0s").dropna(how='all')
        if not df_rel.empty:
            df_rel.columns = [c.strip() for c in df_rel.columns]
            col_data = "Data Matrícula"
            df_rel[col_data] = pd.to_datetime(df_rel[col_data], dayfirst=True, errors='coerce')
            
            intervalo = st.date_input("Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            
            if len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel[col_data].dt.date >= intervalo[0]) & (df_rel[col_data].dt.date <= intervalo[1])].copy()
                
                # --- PROCESSAMENTO FINANCEIRO ---
                df_f['Valor_Recebido'] = df_f['Pagamento'].apply(extrair_valor_recebido)
                total_recebido = df_f['Valor_Recebido'].sum()
                
                # Ticket Médio Geral (Considera o primeiro valor da célula)
                df_f['Valor_Ticket'] = df_f['Pagamento'].apply(extrair_valor_geral)
                df_boleto = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]
                df_cartao = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK|CREDITO|DEBITO', na=False, case=False)]
                
                tm_boleto = df_boleto['Valor_Ticket'].mean() if not df_boleto.empty else 0.0
                tm_cartao = df_cartao['Valor_Ticket'].mean() if not df_cartao.empty else 0.0

                # --- EXIBIÇÃO DOS CARDS ---
                st.write("")
                c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.5, 1.5])
                
                with c1: 
                    st.markdown(f'<div class="card-hud neon-pink"><small>Matrículas</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2:
                    atv = len(df_f[df_f['STATUS'].str.upper() == 'ATIVO']) if 'STATUS' in df_f.columns else 0
                    st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{atv}</h2></div>', unsafe_allow_html=True)
                with c3:
                    st.markdown(f'<div class="card-hud neon-blue"><small>Valor Recebido</small><h2 style="font-size:20px; color:#00f2ff">R$ {total_recebido:,.2f}</h2></div>', unsafe_allow_html=True)
                with c4:
                    # TICKET MÉDIO UNIFICADO
                    st.markdown(f'''
                        <div class="card-hud neon-purple">
                            <small>Ticket Médio</small>
                            <div class="tm-container">
                                <div class="tm-item">🎫 Boleto: <b>R$ {tm_boleto:.2f}</b></div>
                                <div class="tm-item">💳 Cartão: <b>R$ {tm_cartao:.2f}</b></div>
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)
                with c5:
                    df_f['Vendedor'] = df_f['Vendedor'].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
                    top_v = df_f['Vendedor'].value_counts().idxmax() if not df_f.empty else "N/A"
                    st.markdown(f'<div class="card-hud neon-blue"><small>Top Performer</small><h3 style="font-size:15px">{top_v}</h3></div>', unsafe_allow_html=True)

                st.write("---")
                # Gráficos e barra de cidades seguem a mesma lógica estética HUD anterior...
                st.info("💡 Dica: O 'Valor Recebido' soma apenas números que aparecem após a palavra 'PAGO' na coluna de Pagamento.")

    except Exception as e:
        st.error(f"Erro no processamento: {e}")
