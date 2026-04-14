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
                if isinstance(conteudo, dict) and "tags" in conteudo:
                    return conteudo
                elif isinstance(conteudo, dict):
                    return {"tags": conteudo, "last_selection": {}}
        except: 
            return padrao
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
    div[data-testid="stTextInput"] { width: 100% !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
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
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; transition: all 0.3s ease !important; }
    div.stButton > button:hover { background-color: #00d4df !important; box-shadow: 0 0 15px rgba(0, 242, 255, 0.6) !important; color: #000000 !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
    
    .logo-container {
        position: relative;
        top: -10px;
        left: 0px;
        margin-bottom: 10px;
    }

    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO NO CANTO ESQUERDO ---
if os.path.exists(caminho_logo):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(caminho_logo, width=90)
    st.markdown('</div>', unsafe_allow_html=True)

# --- CONEXÃO REFORÇADA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        return conn.read(ttl="10s").dropna(how='all')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None
if "df_auto_ready" not in st.session_state: st.session_state.df_auto_ready = None

# --- FUNÇÕES AUXILIARES ---
def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None
    st.session_state.df_auto_ready = None

def converter_para_float(valor_str):
    """Trata corretamente milhar com ponto e decimal com vírgula."""
    if not valor_str: return 0.0
    v = valor_str.strip().replace("R$", "").replace(" ", "")
    if "." in v and "," in v:
        v = v.replace(".", "").replace(",", ".")
    else:
        v = v.replace(",", ".")
    try:
        return float(v)
    except:
        return 0.0

def extrair_valor_recebido(texto):
    """
    Lógica Cumulativa e Rigorosa (v2026.FINAL):
    1. Prioridade para conteúdos em parênteses (Alterações).
    2. Fim do ponto de corte (lê a linha inteira).
    3. Multiplicação Global (Regex flexível para grudados).
    4. Captura cumulativa de múltiplos valores.
    5. Precisão de float brasileira.
    """
    if not texto: return 0.0, 0.0, 0.0, 0.0
    
    t_raw = str(texto).upper()
    
    # REGRA 5: Prioridade de Parênteses (Se houver alteração entre parênteses, processa só isso)
    match_paren = re.search(r'\(([^)]*ALTER[^)]*)\)', t_raw)
    t = match_paren.group(1) if match_paren else t_raw

    v_cartao = 0.0
    v_entrada = 0.0
    v_taxa = 0.0

    # REGRA 2: Regex de Multiplicação Global (Captura mesmo se grudado ex: R12X90)
    for m in re.finditer(r'(\d+)\s*[xX]\s*([\d\.,]+)', t):
        qtd = int(m.group(1))
        v_un = converter_para_float(m.group(2))
        # Verifica se o contexto é PAGO/LINK/CARTÃO
        contexto = t[max(0, m.start()-15):min(len(t), m.end()+15)]
        if any(x in contexto for x in ["PAGO", "PAGA", "LINK", "CARTÃO", "OK"]):
            v_cartao += (qtd * v_un)

    # REGRA 3: Captura Cumulativa (Soma todos os valores precedidos por termos de pagamento)
    # Busca por valores após termos-chave em toda a linha
    padrao_pago = r'(?:PAGO|PAGOU|PAGA|ENTRADA|DÉBITO|PIX|DINHEIRO|PRIMEIRA|1ª|ATO)\s*(?:PARCELA)?\s*(?:R\$)?\s*([\d\.,]+)'
    for m in re.finditer(padrao_pago, t):
        val = converter_para_float(m.group(1))
        
        # Filtro: Evita somar o valor unitário que já entrou na multiplicação do cartão
        ja_no_x = False
        for mx in re.finditer(r'(\d+)\s*[xX]\s*([\d\.,]+)', t):
            if m.group(1) == mx.group(2): ja_no_x = True; break
            
        if not ja_no_x and val > 0:
            # Verifica se o valor é referente a TAXA
            cont_taxa = t[max(0, m.start()-15):m.end()]
            if "TAXA" in cont_taxa:
                v_taxa += val
            elif any(x in cont_taxa for x in ["CARTÃO", "LINK"]):
                # Se for valor cheio do cartão (sem parcelas)
                if val > (v_cartao + 0.01) or v_cartao == 0: v_cartao += val
            else:
                v_entrada += val

    # Backup para Taxas de 50 explícitas sem valor grudado
    if "TAXA" in t and "50" in t and ("PAGA" in t or "PAGO" in t) and v_taxa == 0:
        v_taxa = 50.0

    total = v_cartao + v_entrada + v_taxa
    return total, v_cartao, v_entrada, v_taxa

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
    if len(valor) == 11:
        st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 3: RELATÓRIOS (ONDE O CÁLCULO É APLICADO) ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"
        df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Filtrar Período (Data de Matrícula)", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            
            # --- PROCESSAMENTO FINANCEIRO CORRIGIDO ---
            res_pag = df_f['Pagamento'].apply(extrair_valor_recebido)
            df_f['v_rec'] = res_pag.apply(lambda x: x[0])
            df_f['v_cartao'] = res_pag.apply(lambda x: x[1])
            df_f['v_entrada'] = res_pag.apply(lambda x: x[2])
            df_f['v_taxa'] = res_pag.apply(lambda x: x[3])
            
            t_geral = df_f["v_rec"].sum()
            t_cartao = df_f["v_cartao"].sum()
            t_entrada = df_f["v_entrada"].sum()
            t_taxa = df_f["v_taxa"].sum()
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: st.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
            
            with c4: 
                # CARD TOTAL RECEBIDO COM DETALHAMENTO CENTESIMAL
                st.markdown(f'''
                    <div class="card-hud neon-blue">
                        <span class="stat-label">TOTAL RECEBIDO</span>
                        <h2 style="font-size:22px; margin-bottom:2px;">R${t_geral:,.2f}</h2>
                        <div style="font-size:9px; color:#64748b; line-height:1.2;">
                            CARTÃO: R${t_cartao:,.2f} | ENTR: R${t_entrada:,.2f}<br>
                            TAXAS: R${t_taxa:,.2f}
                        </div>
                    </div>''', unsafe_allow_html=True)
            
            with c5:
                # Ticket Médio usando valor geral para referência
                df_f['v_tic_ref'] = df_f['Pagamento'].apply(extrair_valor_geral)
                tm_b = df_f[df_f['Pagamento'].str.contains('BOLETO', na=False, case=False)]['v_tic_ref'].mean() or 0.0
                tm_c = df_f[df_f['Pagamento'].str.contains('CARTÃO|LINK', na=False, case=False)]['v_tic_ref'].mean() or 0.0
                st.markdown(f'<div class="card-hud neon-purple"><span class="stat-label">TICKET MÉDIO</span><div style="font-size:18px; font-weight:bold; color:#e0e0e0;">BOL: R${tm_b:.0f}<br>CAR: R${tm_c:.0f}</div></div>', unsafe_allow_html=True)
            
            with c6:
                c_banc = len(df_f[df_f["Curso"].str.contains("BANCÁRIO", case=False, na=False)])
                c_agro = len(df_f[df_f["Curso"].str.contains("AGRO", case=False, na=False)])
                c_ing = len(df_f[df_f["Curso"].str.contains("INGLÊS", case=False, na=False)])
                c_tec = len(df_f[df_f["Curso"].str.contains("TECNOLOGIA|INFORMÁTICA", case=False, na=False)])
                st.markdown(f'''
                    <div class="card-hud neon-blue">
                        <span class="stat-label">POR ÁREA</span>
                        <div style="font-size:15px; text-align:left; color:#e0e0e0; line-height:1.4; padding-left:5px;">
                            BANC: <b style="color:#00f2ff;">{c_banc}</b> | AGRO: <b style="color:#00f2ff;">{c_agro}</b><br>
                            INGL: <b style="color:#00f2ff;">{c_ing}</b> | TECN: <b style="color:#00f2ff;">{c_tec}</b>
                        </div>
                    </div>''', unsafe_allow_html=True)

            # Gráfico de Status simplificado
            if len(df_f) > 0:
                at_c = len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])
                can_c = len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])
                fig_status = go.Figure()
                fig_status.add_trace(go.Bar(y=["STATUS"], x=[at_c], orientation='h', marker=dict(color='#2ecc71'), text=[f"<b>ATIVOS: {at_c}</b>"], textposition='inside', insidetextanchor='start'))
                fig_status.add_trace(go.Bar(y=["STATUS"], x=[can_c], orientation='h', marker=dict(color='#ff4b4b'), text=[f"<b>CANCELADOS: {can_c}</b>"], textposition='inside', insidetextanchor='end'))
                fig_status.update_layout(barmode='stack', showlegend=False, height=40, margin=dict(t=5, b=5, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                st.plotly_chart(fig_status, use_container_width=True, config={'displayModeBar': False})

# ... [RESTANTE DAS ABAS 1, 2 E 4 MANTIDAS INTEGRALMENTE CONFORME O ORIGINAL] ...
