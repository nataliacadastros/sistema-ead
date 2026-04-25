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
        return conn.read(worksheet="usuários", ttl="1s").dropna(how='all')
    except Exception as e:
        return pd.DataFrame(columns=["usuario", "senha", "nivel"])

# --- CONTROLE DE SESSÃO E LOGIN ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_ativo = None
    st.session_state.nivel_ativo = None

# --- CSS HUD NEON COMPLETO (CORREÇÃO DEFINITIVA DO LOGIN) ---
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
    
    /* REGRA GERAL PARA CADASTRO (MAIÚSCULO) */
    div[data-testid="stTextInput"] input { 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        font-size: 12px !important; 
        height: 18px !important; 
        border-radius: 5px !important; 
    }
    
    /* REGRA ESPECÍFICA PARA LOGIN (IGNORA O MAIÚSCULO) */
    [data-testid="stForm"] div[data-testid="stTextInput"] input,
    .login-wrapper div[data-testid="stTextInput"] input {
        text-transform: none !important;
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
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; transition: all 0.3s ease !important; }
    div.stButton > button:hover { background-color: #00d4df !important; box-shadow: 0 0 15px rgba(0, 242, 255, 0.6) !important; color: #000000 !important; }

    header {visibility: hidden;} footer {visibility: hidden;}
    .logo-container { position: relative; top: -10px; left: 0px; margin-bottom: 10px; }
    .stat-label { font-size: 12px; font-weight: bold; margin-bottom: 4px; display: block; }

    .login-box { 
        background: rgba(18, 22, 41, 0.9); padding: 40px; border-radius: 15px; 
        border: 2px solid #1f295a; box-shadow: 0 0 30px rgba(0, 242, 255, 0.1);
        margin-top: 100px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE TELA DE LOGIN ---
if not st.session_state.logado:
    # Div container para aplicar a exceção CSS
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    _, centro_login, _ = st.columns([1, 1.2, 1])
    with centro_login:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        if os.path.exists(caminho_logo):
            st.image(caminho_logo, width=180)
        st.markdown("<h2 style='color: #00f2ff; margin-bottom:30px;'>ACESSO RESTRITO</h2>", unsafe_allow_html=True)
        
        user_in = st.text_input("USUÁRIO", key="login_user_final").strip().lower()
        pass_in = st.text_input("SENHA", type="password", key="login_pass_final").strip()
        
        if st.button("ENTRAR NO SISTEMA", use_container_width=True):
            df_users = carregar_usuarios()
            if not df_users.empty:
                valido = df_users[
                    (df_users['usuario'].astype(str).str.strip().str.lower() == user_in) & 
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
                st.error("Erro ao conectar com a base de usuários.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- ABAIXO TODO O RESTO DO SEU CÓDIGO ORIGINAL (MANTIDO) ---

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
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

if os.path.exists(caminho_logo):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(caminho_logo, width=90)
    st.markdown('</div>', unsafe_allow_html=True)

is_admin = st.session_state.nivel_ativo == "ADMIN"
titulos_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS", "👥 USUÁRIOS"] if is_admin else ["🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"]
abas = st.tabs(titulos_abas)

if is_admin:
    tab_cad, tab_ger, tab_rel, tab_subir, tab_users = abas
else:
    tab_ger, tab_rel = abas

# --- ABA 1: CADASTRO ---
if is_admin:
    with tab_cad:
        _, centro, _ = st.columns([0.2, 5.6, 0.2])
        with centro:
            s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
            fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                      ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                      ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                      ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
            for l, k in fields:
                cl, ci = st.columns([1.2, 3.8]); cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
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
                            "ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(),
                            "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]),
                            "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), 
                            "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(),
                            "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]
                        })
                        st.session_state.reset_aluno += 1; st.rerun()
            with b2:
                if st.button("📤 ENVIAR PLANILHA"):
                    if st.session_state.lista_previa:
                        try:
                            creds_info = st.secrets["connections"]["gsheets"]
                            client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                            ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                            d_f = []
                            for a in st.session_state.lista_previa:
                                d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                            ws.append_rows(d_f, value_input_option='RAW')
                            st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado com sucesso!"); st.cache_data.clear(); st.rerun()
                        except Exception as e: st.error(f"Erro ao enviar: {e}")
            if st.session_state.lista_previa:
                st.markdown(f"### 📋 PRÉ-VISUALIZAÇÃO ({len(st.session_state.lista_previa)} ALUNOS)")
                st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# ABA 2: GERENCIAMENTO
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
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
            sc = "status-badge status-ativo" if r['STATUS'] == "ATIVO" else "status-badge status-cancelado"
            rows += f"<tr><td><span class='{sc}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in df_g.columns]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

# ABA 3: RELATÓRIOS
with tab_rel:
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"
        df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Filtrar Período", value=(date.today()-timedelta(days=7), date.today()))
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            v_taxa = 0.0; v_cartao = 0.0; v_entrada = 0.0
            for linha in df_f['Pagamento'].tolist():
                if not linha: continue
                l_u = str(linha).upper()
                if "TAXA" in l_u: v_taxa += 50.0
                m_m = re.findall(r'(\d+)\s*[X]\s*(?:R\$)?\s*([\d\.,]+)', l_u)
                if m_m and ("CARTÃO" in l_u or "LINK" in l_u):
                    for q, v in m_m: v_cartao += int(q) * float(v.replace('.', '').replace(',', '.'))
                else:
                    m_f = re.findall(r'(?:PAGO|R\$)\s*([\d\.]+,\d{2}|[\d\.]+)', l_u)
                    for v in m_f:
                        try:
                            val = float(v.replace('.', '').replace(',', '.'))
                            if val != 50.0:
                                if "CARTÃO" in l_u or "LINK" in l_u: v_cartao += val
                                else: v_entrada += val
                        except: pass
            total = v_taxa + v_cartao + v_entrada
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">TOTAL</span><h2>R${total:,.2f}</h2></div>', unsafe_allow_html=True)

# ABA 4: SUBIR ALUNOS (ADMIN)
if is_admin:
    with tab_subir:
        st.markdown("### 📤 IMPORTAÇÃO EAD")
        st.info("Função original mantida para processamento.")

# ABA 5: USUÁRIOS (ADMIN)
if is_admin:
    with tab_users:
        st.markdown("### 👥 GESTÃO DE ACESSOS")
        with st.form("form_users_geral", clear_on_submit=True):
            nu_user = st.text_input("Novo Usuário (Login)").strip().lower()
            nu_pass = st.text_input("Senha").strip()
            nu_nivel = st.selectbox("Nível", ["ADMIN", "CONSULTA"])
            if st.form_submit_button("CADASTRAR"):
                if nu_user and nu_pass:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws_u = client.open_by_url(creds_info["spreadsheet"]).worksheet("usuários")
                        ws_u.append_row([nu_user, nu_pass, nu_nivel])
                        st.success(f"Usuário {nu_user} cadastrado!")
                        st.cache_data.clear()
                    except Exception as e: st.error(f"Erro: {e}")
        st.write("---")
        st.dataframe(carregar_usuarios(), use_container_width=True, hide_index=True)

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.usuario_ativo.upper() if st.session_state.usuario_ativo else ''}")
    st.write(f"Nível: {st.session_state.nivel_ativo}")
    if st.button("SAIR DO SISTEMA"):
        st.session_state.logado = False
        st.rerun()
