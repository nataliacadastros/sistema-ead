import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
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

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
                return conteudo if isinstance(conteudo, dict) and "tags" in conteudo else padrao
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

# --- CSS HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    [data-testid="stAppViewBlockContainer"] { padding-top: 40px !important; padding-left: 0px !important; padding-right: 0px !important; max-width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] { background-color: #121629; border-bottom: 1px solid #1f295a; position: fixed; top: 0; left: 0 !important; width: 100vw !important; z-index: 999; justify-content: center; height: 35px !important; }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; border-radius: 5px !important; }
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E FUNÇÕES DE DADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read():
    try:
        return conn.read(ttl="10s").dropna(how='all')
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

def atualizar_registro_gsheets(id_aluno, novos_dados_lista):
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
        ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
        celula = ws.find(str(id_aluno))
        if celula:
            # Atualiza a linha A-P correspondente
            ws.update(range_name=f"A{celula.row}:P{celula.row}", values=[novos_dados_lista])
            return True
        return False
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False

# --- ESTADOS DE SESSÃO ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES AUXILIARES (LÓGICA DE NEGÓCIO) ---
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

# --- ABA 1: CADASTRO ---
with tab_cad:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    if os.path.exists(caminho_logo):
        st.image(caminho_logo, width=90)
    
    _, centro, _ = st.columns([0.2, 5.6, 0.2])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        s_ge = f"g_{st.session_state.reset_geral}"
        
        fields = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
                  ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                  ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        
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
                    st.session_state.reset_aluno += 1
                    st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds_info["spreadsheet"]).get_worksheet(0)
                        d_f = [[ "ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", 
                                 date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], 
                                 a["Pagto"], a["Vendedor"], a["Data_Mat"] ] for a in st.session_state.lista_previa]
                        ws.append_rows(d_f, value_input_option='RAW')
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1
                        st.cache_data.clear(); st.success("Enviado!"); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 2: GERENCIAMENTO (ATUALIZADA) ---
with tab_ger:
    st.markdown('<div style="padding: 0 20px;">', unsafe_allow_html=True)
    st.markdown("### 🖥️ GERENCIADOR DE ALUNOS")
    
    df_g = safe_read()
    if not df_g.empty:
        df_g.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        
        # Busca para edição (Simulando clique/seleção)
        c_search, c_ref = st.columns([4, 1])
        busca_ed = c_search.text_input("🔍 Localizar para Edição", placeholder="Nome ou ID...")
        if c_ref.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()

        if busca_ed:
            res = df_g[df_g['ALUNO'].str.contains(busca_ed, case=False, na=False) | df_g['ID'].str.contains(busca_ed, case=False, na=False)]
            if not res.empty:
                aluno_edit = st.selectbox("Selecione o registro para abrir:", res['ALUNO'] + " | " + res['ID'])
                id_edit = aluno_edit.split(" | ")[-1]
                reg = df_g[df_g['ID'] == id_edit].iloc[0]

                # Formulário de Edição (Simulando Toplevel/Grab_set)
                with st.expander(f"📝 EDITAR: {reg['ALUNO']}", expanded=True):
                    with st.form("edit_form"):
                        col_a, col_b = st.columns(2)
                        new_status = col_a.selectbox("STATUS", ["ATIVO", "CANCELADO"], index=0 if reg['STATUS'] == "ATIVO" else 1)
                        new_nome = col_a.text_input("ALUNO", value=reg['ALUNO'])
                        new_tel = col_b.text_input("TEL. RESP", value=reg['TEL_RESP'])
                        new_pag = st.text_area("PAGAMENTO", value=reg['PAGTO'])
                        
                        if st.form_submit_button("💾 SALVAR ALTERAÇÕES"):
                            dados_atuais = reg.tolist()
                            dados_atuais[0] = new_status
                            dados_atuais[7] = new_nome.upper()
                            dados_atuais[8] = new_tel
                            dados_atuais[13] = new_pag.upper()
                            
                            if atualizar_registro_gsheets(id_edit, dados_atuais):
                                st.success("Atualizado!"); st.cache_data.clear(); st.rerun()
            else: st.warning("Não encontrado.")

        st.write("---")
        st.dataframe(df_g.iloc[::-1], use_container_width=True, height=500)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    st.markdown('<div style="padding: 0 20px;">', unsafe_allow_html=True)
    df_r = safe_read()
    if not df_r.empty:
        df_r.columns = [c.strip() for c in df_r.columns]
        dt_col = "Data Matrícula"
        df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
        iv = st.date_input("Período", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
        
        if len(iv) == 2:
            df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
            v_taxa = 0.0; v_cartao = 0.0; v_entrada = 0.0
            
            for linha in df_f['Pagamento'].tolist():
                if not linha: continue
                l_up = str(linha).upper()
                taxas = re.findall(r'TAXA.*?(\d+)', l_up)
                for t in taxas: v_taxa += float(t)
                if "TAXA" in l_up and "PAGA" in l_up and not taxas: v_taxa += 50.0
                
                m_mult = re.findall(r'(\d+)\s*[X]\s*(?:R\$)?\s*([\d\.,]+)', l_up)
                if m_mult and ("CARTÃO" in l_up or "LINK" in l_up):
                    for q, v in m_mult: v_cartao += int(q) * float(v.replace('.', '').replace(',', '.'))
                else:
                    m_fixo = re.findall(r'(?:PAGO|R\$)\s*([\d\.]+,\d{2}|[\d\.]+)', l_up)
                    for val in m_fixo:
                        vl = float(val.replace('.', '').replace(',', '.'))
                        if vl != 50.0:
                            if "CARTÃO" in l_up or "LINK" in l_up: v_cartao += vl
                            else: v_entrada += vl
            
            total = v_taxa + v_cartao + v_entrada
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="card-hud neon-pink"><span class="stat-label">MATRÍCULAS</span><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="card-hud neon-green"><span class="stat-label">ATIVOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="card-hud neon-red"><span class="stat-label">CANCELADOS</span><h2>{len(df_f[df_f["STATUS"].str.upper()=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="card-hud neon-blue"><span class="stat-label">RECEBIDO</span><h2>R${total:,.2f}</h2></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 4: SUBIR ALUNOS ---
with tab_subir:
    st.markdown('<div style="padding: 0 50px;">', unsafe_allow_html=True)
    st.markdown("### 📤 IMPORTAÇÃO EAD")
    modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
    
    if modo == "AUTOMÁTICO":
        df_m = safe_read()
        if not df_m.empty:
            df_m.columns = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
            df_m['DT_CAD'] = pd.to_datetime(df_m['DT_CAD'], dayfirst=True, errors='coerce')
            d_sel = st.date_input("Data Cadastro:", value=date.today())
            df_fil = df_m[df_m['DT_CAD'].dt.date == d_sel]
            if not df_fil.empty:
                sel_c = st.multiselect("Cidades:", sorted(df_fil['CIDADE'].unique()))
                st.write(f"{len(df_fil[df_fil['CIDADE'].isin(sel_c)])} alunos prontos.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("IDs", key="in_user"); st.text_area("Células", key="in_cell")
            st.text_area("Cidades", key="in_city"); st.text_area("Pagamentos", key="in_pay")
        with c2:
            st.text_area("Nomes", key="in_nome"); st.text_area("Documentos", key="in_doc")
            st.text_area("Cursos", key="in_cour"); st.text_area("Vendedores", key="in_sell")
    st.markdown('</div>', unsafe_allow_html=True)
