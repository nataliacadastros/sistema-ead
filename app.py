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

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DEFINIÇÃO DA LOGO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

# --- INICIALIZAÇÃO DE ESTADOS (PREVINE ERROS DE NAVEGAÇÃO) ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None
if "df_auto_ready" not in st.session_state: st.session_state.df_auto_ready = None

# --- ARQUIVOS E PERSISTÊNCIA ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                return conteudo if isinstance(conteudo, dict) and "tags" in conteudo else padrao
        except: return padrao
    return padrao

if "dados_tags" not in st.session_state: st.session_state.dados_tags = carregar_tags()

DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; }
    .main .block-container { padding-top: 10px !important; max-width: 100% !important; margin: 0 auto !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 16px !important; display: flex; align-items: center; justify-content: flex-end; }
    div[data-testid="stTextInput"] { width: 100% !important; margin-bottom: 5px !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; height: 18px !important; border-radius: 5px !important; }
    .custom-table-wrapper { width: 100%; max-height: 500px; overflow: auto; background-color: #121629; border: 1px solid #1f295a; border-radius: 10px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2000px !important; font-size: 11px;}
    .custom-table th { background-color: #1f295a; color: #00f2ff; padding: 10px; position: sticky; top: 0; }
    .custom-table td { padding: 8px; border-bottom: 1px solid #1f295a; white-space: pre-wrap !important; }
    .status-badge { padding: 2px 8px; border-radius: 10px; font-weight: bold; font-size: 9px; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }
    
    /* HUD Relatórios */
    .card-hud-new { background: rgba(18, 22, 41, 0.5); border: 1px solid #1f295a; padding: 10px; border-radius: 8px; position: relative; height: 70px; }
    .hud-title { font-size: 9px; color: #64748b; text-transform: uppercase; }
    .hud-value { font-size: 20px; font-weight: bold; text-shadow: 0 0 5px currentColor; }
    .hud-cyan { color: #00f2ff; } .hud-green { color: #2ecc71; } .hud-pink { color: #ff007a; } .hud-purple { color: #bc13fe; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists(caminho_logo):
    c_img, _ = st.columns([0.1, 0.9])
    with c_img: st.image(caminho_logo, width=70)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try: return conn.read(ttl="5s").dropna(how='all')
    except: return pd.DataFrame()

def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    try: return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0
    except: return 0.0

def extrair_valor_geral(texto):
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

def limpar_vendedor(nome):
    return str(nome).split('-')[0].strip().upper() if nome else "N/A"

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO ---
with tab_cad:
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO:", f"input_curso_key_{s_al}"), ("PAGAMENTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in fields:
            cl, ci = st.columns([1.2, 3.8])
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            elif "f_cpf" in k: ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        
        if st.button("💾 SALVAR ALUNO", use_container_width=True):
            if st.session_state[f"f_nome_{s_al}"]:
                st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]), "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                st.session_state.reset_aluno += 1; st.rerun()
        
        if st.session_state.lista_previa:
            if st.button("📤 ENVIAR PARA PLANILHA GERAL", use_container_width=True):
                try:
                    creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                    ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                    for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                    ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2, value_input_option='RAW')
                    st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
            st.markdown(f"**Aguardando Envio:** {len(st.session_state.lista_previa)} alunos")
            st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], label_visibility="collapsed")
    with cf4: 
        if st.button("🔄"): st.cache_data.clear(); st.rerun()
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            stt = "status-ativo" if r['STATUS']=="ATIVO" else "status-cancelado"
            rows += f"<tr><td><span class='status-badge {stt}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in df_g.columns]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Filtro Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido)
            df_f['Vend_C'] = df_f['Vendedor'].apply(limpar_vendedor)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="card-hud-new hud-cyan"><div class="hud-title">Matrículas</div><div class="hud-value">{len(df_f)}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="card-hud-new hud-green"><div class="hud-title">Ativos</div><div class="hud-value">{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="card-hud-new hud-pink"><div class="hud-title">Cancelados</div><div class="hud-value">{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="card-hud-new hud-cyan"><div class="hud-title">Recebido</div><div class="hud-value">R${df_f["v_rec"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            
            g1, g2 = st.columns(2)
            with g1:
                fig1 = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.6, marker=dict(colors=['#2ecc71', '#ff007a']))])
                fig1.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=250)
                st.plotly_chart(fig1, use_container_width=True)
            with g2:
                dfv = df_f['Vend_C'].value_counts().reset_index()
                fig2 = go.Figure(data=[go.Pie(labels=dfv['Vend_C'], values=dfv['count'], hole=0.6, marker=dict(colors=['#00f2ff', '#bc13fe', '#ff007a', '#2ecc71']))])
                fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=True, height=250, legend=dict(font=dict(size=10)))
                st.plotly_chart(fig2, use_container_width=True)

# --- ABA 4: SUBIR ---
with tab_subir:
    st.info("Utilize as áreas de texto para importar dados em massa conforme o padrão do sistema.")
    st.text_area("IDs (Coluna G)", height=100)
    st.button("PROCESSAR IMPORTAÇÃO", use_container_width=True)
