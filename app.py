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

# --- ARQUIVO DE TAGS E PERSISTÊNCIA ---
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

# --- CSS ESTÉTICA HUD NEON & SUBIR ALUNOS ---
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
    
    /* ESTILO CADASTRO */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 0px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; padding-right: 15px !important; }
    
    /* CAMPOS DE TEXTO */
    .stTextInput input, .stTextArea textarea { 
        background-color: white !important; 
        color: black !important; 
        text-transform: uppercase !important; 
        border-radius: 5px !important; 
    }

    /* ESTILO ABA SUBIR ALUNOS (Cores Tkinter solicitadas) */
    .subir-container { background-color: #1C2526; padding: 20px; border-radius: 10px; }
    .stButton > button { background-color: #805dca !important; color: white !important; font-weight: bold !important; border: none !important; }
    
    /* GERENCIAMENTO */
    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; position: sticky; top: 0; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: nowrap; }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES AUXILIARES ---
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

# --- ABA 1: CADASTRO ---
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
            cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
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
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{s_al}"]:
                    st.session_state.lista_previa.append({"ID": st.session_state[f"f_id_{s_al}"].upper(), "Aluno": st.session_state[f"f_nome_{s_al}"].upper(), "Tel_Resp": st.session_state[f"f_tel_resp_{s_al}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{s_al}"], "CPF": st.session_state[f"f_cpf_{s_al}"], "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), "Course": st.session_state[f"input_curso_key_{s_al}"].upper(), "Pagto": st.session_state[f"f_pagto_{s_al}"].upper(), "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(), "Data_Mat": st.session_state[f"f_data_{s_ge}"]})
                    st.session_state.reset_aluno += 1; st.rerun()
        with b2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds = st.secrets["connections"]["gsheets"]; client = gspread.authorize(Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
                        ws = client.open_by_url(creds["spreadsheet"]).get_worksheet(0); d_f = []
                        for a in st.session_state.lista_previa: d_f.append(["ATIVO", "MGA", "A DEFINIR", "SIM" if "10 CURSOS" in a["Course"] else "NÃO", "A DEFINIR" if "INGLÊS" in a["Course"] else "NÃO", date.today().strftime("%d/%m/%Y"), a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Course"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                        ws.insert_rows(d_f, row=len(ws.col_values(1)) + 2 if ws.col_values(1) else 2)
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1; st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
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
            rows += f"<tr><td><span class='status-badge {sc}'>{r['STATUS']}</span></td><td>{r['UNID.']}</td><td>{r['TURMA']}</td><td>{r['10C']}</td><td>{r['ING']}</td><td>{r['DT_CAD']}</td><td>{r['ID']}</td><td>{r['ALUNO']}</td><td>{r['TEL_RESP']}</td><td>{r['TEL_ALU']}</td><td>{r['CPF']}</td><td>{r['CIDADE']}</td><td>{r['CURSO']}</td><td>{r['PAGTO']}</td><td>{r['VEND.']}</td><td>{r['DT_MAT']}</td></tr>"
        st.markdown(f'<div class="custom-table-wrapper"><table class="custom-table"><thead><tr>' + ''.join([f'<th>{h}</th>' for h in hd]) + f'</tr></thead><tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 3: RELATÓRIOS ---
with tab_rel:
    try:
        df_r = conn.read(ttl="0s").dropna(how='all')
        if not df_r.empty:
            df_r.columns = [c.strip() for c in df_r.columns]; v_col = "Vendedor"
            dt_col = "Data Matrícula"; df_r[dt_col] = pd.to_datetime(df_r[dt_col], dayfirst=True, errors='coerce')
            iv = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            if len(iv) == 2:
                df_f = df_r.loc[(df_r[dt_col].dt.date >= iv[0]) & (df_r[dt_col].dt.date <= iv[1])].copy()
                df_f['v_rec'] = df_f['Pagamento'].apply(extrair_valor_recebido); df_f['v_tic'] = df_f['Pagamento'].apply(extrair_valor_geral)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["v_rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
    except Exception as e: st.error(f"Erro: {e}")

# --- ABA 4: SUBIR ALUNOS (ADICIONADA) ---
with tab_subir:
    st.markdown('<div class="subir-container">', unsafe_allow_html=True)
    
    col_input, col_tags = st.columns([3, 2])
    
    with col_input:
        st.markdown("<h4 style='color:#e0e6ed'>CAMPOS DE IMPORTAÇÃO</h4>", unsafe_allow_html=True)
        # 9 campos de texto conforme solicitado
        sub_c1, sub_c2 = st.columns(2)
        u_user = sub_c1.text_area("Usuários", height=100)
        u_nome = sub_c2.text_area("Nome Completo", height=100)
        u_cell = sub_c1.text_area("Celular", height=100)
        u_doc = sub_c2.text_area("Documento", height=100)
        u_city = sub_c1.text_area("Cidade", height=100)
        u_course = sub_c2.text_area("Cursos", height=100)
        u_pay = sub_c1.text_area("Pagamento", height=100)
        u_sell = sub_c2.text_area("Vendedor", height=100)
        u_date = sub_c1.text_area("Data Contrato", height=100)

    with col_tags:
        st.markdown("<h4 style='color:#e0e6ed'>TAGS POR CURSO</h4>", unsafe_allow_html=True)
        cursos_tag_list = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO']
        
        selected_tags = {}
        for curso in cursos_tag_list:
            tag_options = st.session_state.tags_salvas.get(curso, [])
            c_t1, c_t2 = st.columns([3, 1])
            with c_t1:
                # Permite digitar nova tag ou selecionar existente
                current_tag = st.selectbox(f"{curso}", options=[""] + tag_options, key=f"sel_{curso}")
                new_tag = st.text_input(f"Nova tag para {curso}", key=f"new_{curso}", label_visibility="collapsed", placeholder="Add nova tag...")
                
                final_tag = new_tag if new_tag else current_tag
                selected_tags[curso] = final_tag
                
            with c_t2:
                st.write("") # Alinhamento
                if st.button("🗑️", key=f"del_{curso}"):
                    if current_tag in st.session_state.tags_salvas.get(curso, []):
                        st.session_state.tags_salvas[curso].remove(current_tag)
                        salvar_tags(st.session_state.tags_salvas)
                        st.rerun()

    st.write("---")
    u_file_cidades = st.file_uploader("Selecione a planilha de códigos de cidades", type=["xlsx"])
    
    if st.button("🚀 SALVAR PLANILHA", use_container_width=True):
        if not u_file_cidades:
            st.error("Por favor, selecione a planilha de cidades primeiro.")
        else:
            # LÓGICA DE PROCESSAMENTO (IGUAL AO TKINTER)
            wb_cid = load_workbook(u_file_cidades)
            ws_cid = wb_cid.active
            codigos_cidades = {}
            for row in ws_cid.iter_rows(min_row=2, values_only=True):
                if row[1] and row[2]:
                    c_key = str(row[1]).strip().upper()
                    if c_key not in codigos_cidades: codigos_cidades[c_key] = []
                    codigos_cidades[c_key].append(f"{row[2]} - {c_key} ({row[0]})")

            # Preparar dados
            l_user = u_user.strip().split('\n'); l_nome = u_nome.strip().split('\n')
            l_cell = u_cell.strip().split('\n'); l_doc = u_doc.strip().split('\n')
            l_city = u_city.strip().split('\n'); l_cour = u_course.strip().split('\n')
            l_pay = u_pay.strip().split('\n'); l_sell = u_sell.strip().split('\n')
            l_date = u_date.strip().split('\n')

            # Salvar tags novas no JSON
            for c_name, val in selected_tags.items():
                if val:
                    if c_name not in st.session_state.tags_salvas: st.session_state.tags_salvas[c_name] = []
                    if val not in st.session_state.tags_salvas[c_name]:
                        st.session_state.tags_salvas[c_name].append(val)
            salvar_tags(st.session_state.tags_salvas)

            linhas_final = []
            for i in range(len(l_user)):
                try:
                    nome_full = l_nome[i].strip()
                    partes = nome_full.split(" ")
                    fname = partes[0]; lname = " ".join(partes[1:]) if len(partes) > 1 else ""
                    email = f"{l_user[i].strip()}@profissionalizaead.com.br"
                    
                    # Pagamento
                    p_raw = l_pay[i].strip().upper()
                    if "BOLETO" in p_raw or "SEM FORMA" in p_raw: p_proc = "BOLETO"
                    elif "CARTÃO PAGO" in p_raw or "BOLSA 100%" in p_raw: p_proc = "CARTÃO"
                    else: p_proc = p_raw # Em Streamlit, o tratamento manual pode ser feito via st.data_editor se necessário

                    # Cidade
                    c_raw = l_city[i].strip().upper()
                    opcoes = codigos_cidades.get(c_raw, [])
                    c_proc = opcoes[0].split(" - ")[0] if len(opcoes) == 1 else c_raw

                    # Obs e Ouro
                    curso_tag = selected_tags.get(l_cour[i].strip(), "")
                    obs = f"{curso_tag} | {l_cour[i]} | {l_pay[i]}"
                    ouro = "1" if "+ 10" in obs else "0"

                    linhas_final.append([l_user[i], email, fname, lname, l_cell[i], l_doc[i], c_proc, curso_tag, p_proc, obs, ouro, "futuro", "1", "MGA", l_sell[i], l_date[i], "1"])
                except: continue

            # Gerar Excel para Download
            output = BytesIO()
            wb_out = Workbook(); ws_out = wb_out.active
            ws_out.append(["username", "email2", "name", "lastname", "cellphone2", "document", "city2", "courses", "payment", "observation", "ouro", "password", "role", "secretary", "seller", "contract_date", "active"])
            for r in linhas_final: ws_out.append(r)
            wb_out.save(output)
            
            st.download_button(label="📥 CLIQUE PARA BAIXAR PLANILHA", data=output.getvalue(), file_name=f"alunos_processados_{date.today()}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    st.markdown('</div>', unsafe_allow_html=True)
