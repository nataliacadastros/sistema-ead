import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CSS ESTÉTICA HUD NEON & GERENCIAMENTO PROFISSIONAL ---
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
    
    /* ESTILOS DE CADASTRO ORIGINAIS */
    div[data-testid="stHorizontalBlock"] { margin-bottom: 5px !important; display: flex; align-items: center; }
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 14px !important; padding-right: 15px !important; display: flex; align-items: center; justify-content: flex-end; }
    .stTextInput input { background-color: white !important; color: black !important; text-transform: uppercase !important; font-size: 12px !important; height: 25px !important; border-radius: 5px !important; }
    
    /* BADGES DE STATUS GERENCIAMENTO */
    .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: bold; text-transform: uppercase; }
    .status-ativo { background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
    .status-cancelado { background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border: 1px solid #e74c3c; }
    .status-pendente { background-color: rgba(241, 196, 15, 0.2); color: #f1c40f; border: 1px solid #f1c40f; }

    /* TABELA CUSTOMIZADA */
    .custom-table { width: 100%; border-collapse: collapse; background-color: #121629; border-radius: 10px; overflow: hidden; margin-top: 20px; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 12px; font-size: 12px; border-bottom: 2px solid #0b0e1e; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; }
    .custom-table tr:hover { background-color: rgba(0, 242, 255, 0.05); }

    /* CARDS RELATÓRIO HUD */
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 100px; display: flex; flex-direction: column; justify-content: center; }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }

    .stButton > button { background-color: #00f2ff !important; color: #0b0e1e !important; font-weight: bold !important; border: none !important; border-radius: 5px !important; width: 100%; height: 35px !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0

# --- FUNÇÕES DE CONTROLE (CADASTRO) ---
def atualizar_pagamento():
    suffix_aluno = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    key_pagto = f"f_pagto_{suffix_aluno}"
    texto_atual = st.session_state.get(key_pagto, "")
    base = texto_atual.split('|')[0].strip()
    novo_texto = base
    if st.session_state.get(f"chk_1_{suffix_aluno}"): novo_texto += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix_aluno}"): novo_texto += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix_aluno}"): novo_texto += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[key_pagto] = novo_texto.upper()

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

# --- ABA 3: FUNÇÕES DE RELATÓRIO ---
def extrair_valor_recebido(texto):
    match = re.search(r'PAG[OA]S?\s*(?:R\$)?\s*([\d\.,]+)', str(texto).upper())
    if match:
        try: return float(match.group(1).replace('.', '').replace(',', '.'))
        except: return 0.0
    return 0.0

def extrair_valor_geral(texto):
    try:
        valores = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(valores[0]) if valores else 0.0
    except: return 0.0

# --- NAVEGAÇÃO ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

# --- ABA 1: CADASTRO (IMPECÁVEL - NÃO ALTERADA) ---
with tab_cad:
    _, centro, _ = st.columns([0.5, 5, 0.5])
    with centro:
        suffix_aluno = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
        suffix_geral = f"g_{st.session_state.reset_geral}"
        campos = [("ID:", f"f_id_{suffix_aluno}"), ("ALUNO:", f"f_nome_{suffix_aluno}"), ("TEL. RESPONSÁVEL:", f"f_tel_resp_{suffix_aluno}"),
                  ("TEL. ALUNO:", f"f_tel_aluno_{suffix_aluno}"), ("CPF RESPONSÁVEL:", f"f_cpf_{suffix_aluno}"), ("CIDADE:", f"f_cid_{suffix_geral}"),
                  ("CURSO CONTRATADO:", f"input_curso_key_{suffix_aluno}"), ("FORMA DE PAGAMENTO:", f"f_pagto_{suffix_aluno}"),
                  ("VENDEDOR:", f"f_vend_{suffix_geral}"), ("DATA DA MATRÍCULA:", f"f_data_{suffix_geral}")]
        
        for label, key in campos:
            c_lab, c_inp = st.columns([1.5, 3.5])
            c_lab.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            if "curso" in key: c_inp.text_input(label, key=key, on_change=transformar_curso, args=(key,), label_visibility="collapsed")
            else: c_inp.text_input(label, key=key, label_visibility="collapsed")

        st.write("")
        _, c_c1, c_c2, c_c3, _ = st.columns([1.5, 1.1, 1.2, 1.2, 0.1])
        c_c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{suffix_aluno}", on_change=atualizar_pagamento)
        c_c2.checkbox("CURSO BÔNUS", key=f"chk_2_{suffix_aluno}", on_change=atualizar_pagamento)
        c_c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{suffix_aluno}", on_change=atualizar_pagamento)

        st.write("")
        _, b_col1, b_col2, _ = st.columns([1.5, 1.75, 1.75, 0.1])
        with b_col1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state[f"f_nome_{suffix_aluno}"]:
                    aluno = {"ID": st.session_state[f"f_id_{suffix_aluno}"].upper(), "Aluno": st.session_state[f"f_nome_{suffix_aluno}"].upper(),
                             "Tel_Resp": st.session_state[f"f_tel_resp_{suffix_aluno}"], "Tel_Aluno": st.session_state[f"f_tel_aluno_{suffix_aluno}"],
                             "CPF": st.session_state[f"f_cpf_{suffix_aluno}"], "Cidade": st.session_state[f"f_cid_{suffix_geral}"].upper(),
                             "Curso": st.session_state[f"input_curso_key_{suffix_aluno}"].upper(), "Pagto": st.session_state[f"f_pagto_{suffix_aluno}"].upper(),
                             "Vendedor": st.session_state[f"f_vend_{suffix_geral}"].upper(), "Data_Mat": st.session_state[f"f_data_{suffix_geral}"]}
                    st.session_state.lista_previa.append(aluno)
                    st.session_state.reset_aluno += 1
                    st.rerun()
        with b_col2:
            if st.button("📤 ENVIAR PLANILHA"):
                if st.session_state.lista_previa:
                    try:
                        creds_info = st.secrets["connections"]["gsheets"]
                        credentials = Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
                        client = gspread.authorize(credentials)
                        sh = client.open_by_url(creds_info["spreadsheet"])
                        worksheet = sh.get_worksheet(0)
                        dados_finais = []
                        hoje = date.today().strftime("%d/%m/%Y")
                        for a in st.session_state.lista_previa:
                            col_d = "SIM" if "10 CURSOS" in a["Curso"] else "NÃO"
                            col_e = "A DEFINIR" if "INGLÊS" in a["Curso"] else "NÃO"
                            dados_finais.append(["ATIVO", "MGA", "A DEFINIR", col_d, col_e, hoje, a["ID"], a["Aluno"], a["Tel_Resp"], a["Tel_Aluno"], a["CPF"], a["Cidade"], a["Curso"], a["Pagto"], a["Vendedor"], a["Data_Mat"]])
                        worksheet.insert_rows(dados_finais, row=len(worksheet.col_values(1)) + 2 if worksheet.col_values(1) else 2)
                        st.session_state.lista_previa = []; st.session_state.reset_geral += 1
                        st.success("Enviado!"); st.cache_data.clear(); st.rerun()
                    except Exception as e: st.error(f"Erro: {e}")
        
        if st.session_state.lista_previa: st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO (NOVA INTERFACE PROFISSIONAL) ---
with tab_ger:
    # Barra de Filtros Estilo Painel
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 1.2, 1.2, 1.2, 0.8])
    with col_f1: busca = st.text_input("🔍 Buscar aluno...", placeholder="Nome ou ID", label_visibility="collapsed")
    with col_f2: filtro_curso = st.selectbox("Curso", ["Todos"] + list(DIC_CURSOS.values()), label_visibility="collapsed")
    with col_f3: filtro_status = st.selectbox("Status", ["Todos", "ATIVO", "CANCELADO", "PENDENTE"], label_visibility="collapsed")
    with col_f4: filtro_unidade = st.selectbox("Unidade", ["Todos", "MGA"], label_visibility="collapsed")
    with col_f5: 
        if st.button("🔄 REFRESH"): st.cache_data.clear(); st.rerun()

    try:
        # Leitura e Mapeamento
        df_ger = conn.read(ttl="0s").fillna("")
        col_names = ['STATUS', 'UNIDADE', 'TURMA', '10_CURSOS', 'INGLES', 'DATA_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALUNO', 'CPF', 'CIDADE', 'CURSO', 'PAGTO', 'VENDEDOR', 'DATA_MAT']
        df_ger.columns = col_names[:len(df_ger.columns)]

        # Aplicação de Filtros
        if busca: df_ger = df_ger[df_ger['ALUNO'].str.contains(busca, case=False) | df_ger['ID'].str.contains(busca, case=False)]
        if filtro_curso != "Todos": df_ger = df_ger[df_ger['CURSO'].str.contains(filtro_curso, case=False)]
        if filtro_status != "Todos": df_ger = df_ger[df_ger['STATUS'] == filtro_status]
        if filtro_unidade != "Todos": df_ger = df_ger[df_ger['UNIDADE'] == filtro_unidade]

        # Construção da Tabela Profissional em HTML
        html_tabela = """<table class="custom-table">
            <thead>
                <tr>
                    <th>NOME DO ALUNO</th>
                    <th>ID</th>
                    <th>TELEFONE</th>
                    <th>CURSO</th>
                    <th>STATUS</th>
                    <th>DATA CADASTRO</th>
                    <th>VENDEDOR</th>
                </tr>
            </thead>
            <tbody>"""
        
        for _, row in df_ger.iloc[::-1].head(30).iterrows():
            status_class = "status-ativo" if row['STATUS'] == "ATIVO" else "status-cancelado" if row['STATUS'] == "CANCELADO" else "status-pendente"
            html_tabela += f"""
                <tr>
                    <td style="font-weight: bold; color: #00f2ff;">{row['ALUNO']}</td>
                    <td>{row['ID']}</td>
                    <td>{row['TEL_ALUNO']}</td>
                    <td>{row['CURSO']}</td>
                    <td><span class="status-badge {status_class}">{row['STATUS']}</span></td>
                    <td>{row['DATA_CAD']}</td>
                    <td style="text-transform: uppercase;">{row['VENDEDOR']}</td>
                </tr>"""
        
        html_tabela += "</tbody></table>"
        st.markdown(html_tabela, unsafe_allow_html=True)
        st.caption(f"Exibindo {len(df_ger)} registros encontrados.")

    except Exception as e: st.error(f"Erro ao carregar painel: {e}")

# --- ABA 3: RELATÓRIOS (IMPECÁVEL - NÃO ALTERADA) ---
with tab_rel:
    try:
        df_rel = conn.read(ttl="0s").dropna(how='all')
        if not df_rel.empty:
            df_rel.columns = ['STATUS', 'UNIDADE', 'TURMA', '10_CURSOS', 'INGLES', 'DATA_CAD', 'ID', 'ALUNO', 'TEL_RESP', 'TEL_ALUNO', 'CPF', 'CIDADE', 'CURSO', 'PAGAMENTO', 'VENDEDOR', 'DATA_MAT'][:len(df_rel.columns)]
            df_rel['DATA_MAT'] = pd.to_datetime(df_rel['DATA_MAT'], dayfirst=True, errors='coerce')
            intervalo = st.date_input("Filtro", value=(date.today()-timedelta(days=7), date.today()), format="DD/MM/YYYY")
            if len(intervalo) == 2:
                df_f = df_rel.loc[(df_rel['DATA_MAT'].dt.date >= intervalo[0]) & (df_rel['DATA_MAT'].dt.date <= intervalo[1])].copy()
                df_f['Val_Rec'] = df_f['PAGAMENTO'].apply(extrair_valor_recebido)
                df_f['Val_Tick'] = df_f['PAGAMENTO'].apply(extrair_valor_geral)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                with c1: st.markdown(f'<div class="card-hud neon-pink"><small>Mats</small><h2>{len(df_f)}</h2></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="card-hud neon-green"><small>Ativos</small><h2>{len(df_f[df_f["STATUS"]=="ATIVO"])}</h2></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="card-hud neon-red"><small>Canc.</small><h2>{len(df_f[df_f["STATUS"]=="CANCELADO"])}</h2></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="card-hud neon-blue"><small>Recebido</small><h2 style="font-size:18px">R${df_f["Val_Rec"].sum():,.2f}</h2></div>', unsafe_allow_html=True)
                with c5:
                    tm_b = df_f[df_f['PAGAMENTO'].str.contains('BOLETO', na=False, case=False)]['Val_Tick'].mean() or 0.0
                    st.markdown(f'<div class="card-hud neon-purple"><small>T. Médio</small><div style="font-size:10px">Bol: R${tm_b:.0f}</div></div>', unsafe_allow_html=True)
                with c6: st.markdown(f'<div class="card-hud neon-blue"><small>Top</small><h2 style="font-size:14px">{df_f["VENDEDOR"].value_counts().idxmax() if not df_f.empty else "N/A"}</h2></div>', unsafe_allow_html=True)
                
                st.write("---")
                df_cid_v = df_f['CIDADE'].value_counts().head(4)
                if not df_cid_v.empty:
                    total_c = df_cid_v.sum(); cores = ["#ff007a", "#2ecc71", "#00f2ff", "#bc13fe"]
                    seg_html = "".join([f'<div class="hud-segment" style="width:{(q/total_c)*100}%; background:{cores[i%4]};"><div class="hud-label" style="color:{cores[i%4]};">{q}</div><div class="hud-city-name" style="color:{cores[i%4]};">{n}</div></div>' for i, (n, q) in enumerate(df_cid_v.items())])
                    st.markdown(f'<div class="hud-bar-container">{seg_html}</div>', unsafe_allow_html=True)

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    fig_p = go.Figure(data=[go.Pie(labels=df_f['STATUS'].value_counts().index, values=df_f['STATUS'].value_counts().values, hole=0.5, marker=dict(colors=['#2ecc71', '#ff4b4b']))])
                    fig_p.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=350); st.plotly_chart(fig_p, use_container_width=True)
                with col_g2:
                    df_v = df_f['VENDEDOR'].value_counts().reset_index().head(5)
                    fig_v = px.line(df_v, x='VENDEDOR', y='count', markers=True); fig_v.update_traces(line_color='#00f2ff')
                    fig_v.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350); st.plotly_chart(fig_v, use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")
