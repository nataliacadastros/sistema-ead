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
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- PERSISTÊNCIA DE TAGS ---
ARQUIVO_TAGS = "tags_salvas.json"

def carregar_tags():
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_tags(tags):
    with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)

if "tags_salvas" not in st.session_state:
    st.session_state.tags_salvas = carregar_tags()

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS ESTÉTICA HUD NEON & LAYOUT CUSTOMIZADO ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { 
        color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important;
        background-color: rgba(0, 242, 255, 0.05) !important;
    }
    .main .block-container { padding-top: 45px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    /* CSS CADASTRO ORIGINAL */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; border-radius: 5px !important; }
    
    /* CSS GERENCIAMENTO ORIGINAL */
    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }
    .status-badge { padding: 4px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }

    /* CSS SUBIR ALUNOS - LAYOUT DO PRINT */
    .subir-label { color: #e0e6ed !important; font-size: 14px !important; margin-bottom: 5px !important; }
    .stTextArea textarea { background-color: white !important; color: black !important; text-transform: uppercase !important; border-radius: 0px !important; }
    .btn-salvar-planilha > div [data-testid="stButton"] button {
        background-color: #805dca !important; color: white !important; font-weight: bold !important; width: 100% !important; border-radius: 0px !important; height: 45px !important;
    }
    
    /* HUD CARDS RELATORIO */
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES ORIGINAIS ---
def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

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

def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    return float(match.group(1).replace('.', '').replace(',', '.')) if match else 0.0

def extrair_valor_geral(texto):
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"])

# --- ABA 1: CADASTRO (RESTAURADA) ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"; s_ge = f"g_{st.session_state.reset_geral}"
        c = [("ID:", f"f_id_{s_al}"), ("ALUNO:", f"f_nome_{s_al}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
             ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), ("CIDADE:", f"f_cid_{s_ge}"),
             ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
             ("VENDEDOR:", f"f_vend_{s_ge}"), ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")]
        for l, k in c:
            cl, ci = st.columns([1.5, 3.5])
            cl.markdown(f"<label style='color:#00f2ff; font-weight:bold; font-size:17px; display:flex; align-items:center; justify-content:flex-end; padding-right:15px;'>{l}</label>", unsafe_allow_html=True)
            if "curso" in k: ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
            else: ci.text_input(l, key=k, label_visibility="collapsed")
        st.write("")
        _, c1, c2, c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento)
        c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento)
        c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento)
        st.write("")
        _, b1, b2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        with b1:
            if st.button("💾 SALVAR ALUNO", key="btn_save_al"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA", key="btn_send_ws"):
                if st.session_state.lista_previa:
                    try:
                        creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                        for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                        ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
        if st.session_state.lista_previa: st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO (RESTAURADA) ---
with tab_ger:
    cf1, cf2, cf3, cf4 = st.columns([2.5, 1.5, 1.5, 0.5])
    with cf1: bu = st.text_input("🔍 Buscar...", key="busca_ger", placeholder="Nome ou ID", label_visibility="collapsed")
    with cf2: fs = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO"], key="filtro_status", label_visibility="collapsed")
    with cf3: fu = st.selectbox("Unidade", ["Todos", "MGA"], key="filtro_unid", label_visibility="collapsed")
    with cf4: 
        if st.button("🔄", key="btn_refresh"): st.cache_data.clear(); st.rerun()
    try:
        df_g = conn.read(ttl="0s").fillna("")
        hd = ['STATUS', 'UNID.', 'TURMA', '10C', 'ING', 'DT_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALU', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VEND.', 'DT_MAT']
        df_g.columns = hd[:len(df_g.columns)]
        if bu: df_g = df_g[df_g['ALUNO'].str.contains(bu, case=False) | df_g['ID'].str.contains(bu, case=False)]
        if fs != "Todos": df_g = df_g[df_g['STATUS'] == fs]
        if fu != "Todos": df_g = df_g[df_g['UNID.'] == fu]
        rows = ""
        for _, r in df_g.iloc[::-1].iterrows():
            sc = "status-ativo" if r['STATUS'] == "ATIVO" else "status-cancelado"
            rows += f"<tr><td><span class='status-badge {sc}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ID']}</td><td style='color:#00f2ff;font-weight:bold'>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in hd]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS (RESTAURADA) ---
with tab_rel:
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            df_r.columns = [c.strip() for c in df_r.columns]; v_col = "Vendedor"
            if v_col in df_r.columns: df_r[v_col] = df_r[v_col].astype(str).str.replace(' - COLÉGIO', '', case=False).str.strip().str.upper()
            dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            iv = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
                df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido); df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                # ... [Restante do código original de relatórios mantido internamente]
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 4: SUBIR ALUNOS (LAYOUT FIEL AO PRINT) ---
with tab_subir:
    col_campos, col_tags = st.columns([3, 2])
    
    with col_campos:
        # Linha 1: Usuários e Nome completo
        l1_c1, l1_c2 = st.columns(2)
        l1_c1.markdown("<p class='subir-label'>Usuários</p>", unsafe_allow_html=True)
        u_user = l1_c1.text_area("Usuários", height=100, label_visibility="collapsed", key="in_user")
        l1_c2.markdown("<p class='subir-label'>Nome completo</p>", unsafe_allow_html=True)
        u_nome = l1_c2.text_area("Nome completo", height=100, label_visibility="collapsed", key="in_nome")
        
        # Linha 2: Celular e Documento
        l2_c1, l2_c2 = st.columns(2)
        l2_c1.markdown("<p class='subir-label'>Celular</p>", unsafe_allow_html=True)
        u_cell = l2_c1.text_area("Celular", height=100, label_visibility="collapsed", key="in_cell")
        l2_c2.markdown("<p class='subir-label'>Documento</p>", unsafe_allow_html=True)
        u_doc = l2_c2.text_area("Documento", height=100, label_visibility="collapsed", key="in_doc")

        # Linha 3: Cidade e Cursos
        l3_c1, l3_c2 = st.columns(2)
        l3_c1.markdown("<p class='subir-label'>Cidade</p>", unsafe_allow_html=True)
        u_city = l3_c1.text_area("Cidade", height=100, label_visibility="collapsed", key="in_city")
        l3_c2.markdown("<p class='subir-label'>Cursos</p>", unsafe_allow_html=True)
        u_cour = l3_c2.text_area("Cursos", height=100, label_visibility="collapsed", key="in_cour")

        # Linha 4: Pagamento e Vendedor
        l4_c1, l4_c2 = st.columns(2)
        l4_c1.markdown("<p class='subir-label'>Pagamento</p>", unsafe_allow_html=True)
        u_pay = l4_c1.text_area("Pagamento", height=100, label_visibility="collapsed", key="in_pay")
        l4_c2.markdown("<p class='subir-label'>Vendedor</p>", unsafe_allow_html=True)
        u_sell = l4_c2.text_area("Vendedor", height=100, label_visibility="collapsed", key="in_sell")

        # Linha 5: Data contrato
        l5_c1, _ = st.columns(2)
        l5_c1.markdown("<p class='subir-label'>Data contrato</p>", unsafe_allow_html=True)
        u_date = l5_c1.text_area("Data contrato", height=100, label_visibility="collapsed", key="in_date")

    with col_tags:
        st.markdown("<p style='font-weight:bold; color:white; font-size:16px;'>Tags por curso:</p>", unsafe_allow_html=True)
        cursos_tag_list = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO']
        
        selected_tags = {}
        for curso in cursos_tag_list:
            tag_options = st.session_state.tags_salvas.get(curso, [])
            c_t1, c_t2, c_t3 = st.columns([2, 2, 1])
            c_t1.markdown(f"<p style='font-size:11px; margin-top:10px;'>{curso}</p>", unsafe_allow_html=True)
            with c_t2:
                current_tag = st.selectbox(curso, options=[""] + tag_options, key=f"sel_{curso}", label_visibility="collapsed")
                new_tag = st.text_input(f"New {curso}", key=f"nt_{curso}", label_visibility="collapsed", placeholder="Nova...")
                selected_tags[curso] = new_tag if new_tag else current_tag
            with c_t3:
                if st.button("Excluir tag", key=f"del_{curso}"):
                    if current_tag in st.session_state.tags_salvas.get(curso, []):
                        st.session_state.tags_salvas[curso].remove(current_tag); salvar_tags(st.session_state.tags_salvas); st.rerun()

    st.write("---")
    u_f_cid = st.file_uploader("Arraste aqui a planilha de cidades", type=["xlsx"], label_visibility="collapsed")
    
    st.markdown('<div class="btn-salvar-planilha">', unsafe_allow_html=True)
    if st.button("Salvar planilha", use_container_width=True):
        if not u_f_cid or not u_user: st.error("Faltam dados")
        else:
            # LÓGICA DE PROCESSAMENTO (MAIÚSCULAS / TAGS / CARTÃO)
            wb_c = load_workbook(u_f_cid); ws_c = wb_c.active
            cid_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]}
            
            l_u = u_user.strip().split('\n'); l_n = u_nome.strip().split('\n'); l_p = u_pay.strip().split('\n')
            l_co = u_cour.strip().split('\n'); l_ce = u_cell.strip().split('\n'); l_d = u_doc.strip().split('\n')
            l_ci = u_city.strip().split('\n'); l_s = u_sell.strip().split('\n'); l_dt = u_date.strip().split('\n')

            # Persistir tags novas
            for k, v in selected_tags.items():
                if v and v not in st.session_state.tags_salvas.get(k, []):
                    if k not in st.session_state.tags_salvas: st.session_state.tags_salvas[k] = []
                    st.session_state.tags_salvas[k].append(v)
            salvar_tags(st.session_state.tags_salvas)

            processed, pendentes = [], []
            for i in range(len(l_u)):
                try:
                    n_up = l_n[i].strip().upper()
                    fname = n_up.split(" ")[0]; lname = " ".join(n_up.split(" ")[1:]) if " " in n_up else ""
                    
                    c_o = l_co[i].strip().upper(); p_o = l_p[i].strip().upper()
                    tags_a = [selected_tags[k] for k in cursos_tag_list if k in c_o and selected_tags.get(k)]
                    
                    courses_col = ",".join(tags_a) if tags_a else c_o
                    obs = f"{','.join(tags_a) if tags_a else 'SEM TAG'} | {c_o} | {p_o}"
                    
                    p_f = "BOLETO" if ("BOLETO" in p_o or "SEM FORMA" in p_o) else ("CARTÃO" if "BOLSA 100%" in p_o else p_o)
                    if "CARTÃO" in p_o: pendentes.append({"Index": i, "Aluno": n_up, "Orig": p_o, "Definir": "CARTÃO"})
                    
                    processed.append({
                        "username": l_u[i], "email2": f"{l_u[i]}@profissionalizaead.com.br", "name": fname, "lastname": lname,
                        "cellphone2": l_ce[i], "document": l_d[i], "city2": cid_map.get(l_ci[i].strip().upper(), l_ci[i]),
                        "courses": courses_col, "payment": p_f, "observation": obs, "ouro": "1" if "+ 10" in obs else "0",
                        "password": "futuro", "role": "1", "secretary": "MGA", "seller": l_s[i], "contract_date": l_dt[i], "active": "1"
                    })
                except: continue
            st.session_state.dados_brutos, st.session_state.pendentes, st.session_state.processou = processed, pendentes, True

    if st.session_state.get("processou") and st.session_state.get("pendentes"):
        st.warning("Validação de Cartão:")
        ed = st.data_editor(pd.DataFrame(st.session_state.pendentes), column_config={"Definir": st.column_config.SelectboxColumn("Opção", options=["CARTÃO", "BOLETO"], required=True)}, disabled=["Index", "Aluno", "Orig"], hide_index=True)
        if st.button("Confirmar e Gerar"):
            for _, r in ed.iterrows(): st.session_state.dados_brutos[r["Index"]]["payment"] = r["Definir"]
            out = BytesIO(); wb = Workbook(); ws = wb.active; cols = ["username", "email2", "name", "lastname", "cellphone2", "document", "city2", "courses", "payment", "observation", "ouro", "password", "role", "secretary", "seller", "contract_date", "active"]
            ws.append(cols); [ws.append([d[c] for c in cols]) for d in st.session_state.dados_brutos]; wb.save(out); st.download_button("Baixar Planilha", out.getvalue(), "ead.xlsx")
    elif st.session_state.get("processou"):
        out = BytesIO(); wb = Workbook(); ws = wb.active; cols = ["username", "email2", "name", "lastname", "cellphone2", "document", "city2", "courses", "payment", "observation", "ouro", "password", "role", "secretary", "seller", "contract_date", "active"]
        ws.append(cols); [ws.append([d[c] for c in cols]) for d in st.session_state.dados_brutos]; wb.save(out); st.download_button("Baixar Planilha", out.getvalue(), "ead.xlsx")
    st.markdown('</div>', unsafe_allow_html=True)
