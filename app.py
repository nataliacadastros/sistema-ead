import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="SISTEMA ADM | PROFISSIONALIZA", layout="wide", initial_sidebar_state="collapsed")

# --- DICIONÁRIO DE CURSOS ---
DIC_CURSOS = {
    "00": "COLÉGIO COMBO",
    "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS",
    "5": "JOVEM NO DIREITO",
    "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA",
    "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA",
    "10": "ADMINISTRAÇÃO"
}

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    .block-container { padding-top: 0.5rem !important; max-width: 99% !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0px; background-color: #1a3a5a; padding: 0px; border-bottom: 2px solid #2c5282; }
    .stTabs [data-baseweb="tab"] { height: 48px; color: #ffffff !important; font-weight: 600; border: none; background-color: transparent; padding: 0px 30px; }
    .stTabs [aria-selected="true"] { background-color: #2c5282 !important; border-bottom: 4px solid #2ecc71 !important; }
    div[data-testid="stTextInput"] > div { min-height: 22px !important; height: 22px !important; }
    .stTextInput>div>div>input { background-color: white !important; color: black !important; height: 22px !important; text-transform: uppercase !important; border-radius: 2px !important; font-size: 11px !important; padding: 0px 8px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; display: flex; align-items: center; height: 22px; justify-content: flex-end; padding-right: 15px; }
    [data-testid="stHorizontalBlock"] { margin-bottom: 8px !important; }
    div.stButton > button { background-color: #2ecc71 !important; color: white !important; font-weight: bold !important; height: 38px !important; border-radius: 4px !important; width: 100% !important; border: none !important; }
    .stCheckbox label p { font-size: 11px !important; color: #2ecc71 !important; font-weight: bold; }
    header {visibility: hidden;} footer {visibility: hidden;}
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { font-size: 10px !important; }
    .stDataFrame { background-color: white !important; color: black !important; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZAÇÃO DE ESTADOS ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_display" not in st.session_state: st.session_state.curso_display = ""

# --- FUNÇÕES DE LÓGICA ---

def processar_curso():
    """Captura o código digitado, converte via dicionário e concatena."""
    entrada = st.session_state.curso_field.strip()
    
    if entrada:
        # Pega a última parte digitada (caso o usuário tenha digitado algo após o último +)
        partes = entrada.split('+')
        ultimo_termo = partes[-1].strip()
        
        # Se o último termo for um código no dicionário, converte
        if ultimo_termo in DIC_CURSOS:
            nome_curso = DIC_CURSOS[ultimo_termo]
            
            # Reconstrói a string
            if st.session_state.curso_display:
                # Se o curso já não estiver na lista, adiciona
                if nome_curso not in st.session_state.curso_display:
                    st.session_state.curso_display += f" + {nome_curso}"
            else:
                st.session_state.curso_display = nome_curso
        else:
            # Se não for código, mantém o que foi digitado em maiúsculo
            st.session_state.curso_display = entrada.upper()
    
    # Regra: Sempre manter um espaço no final e converter para UPPER
    st.session_state.curso_display = st.session_state.curso_display.upper().strip() + " "
    # Limpa o campo de input temporário (o Streamlit atualizará o valor pelo session_state)

def atualizar_pagto():
    base = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

def campo_horizontal(label, key, value="", on_change=None):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)

# --- ABAS ---
abas = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with abas[0]:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    with col_central:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        
        # CAMPO CURSO COM LÓGICA DE CONVERSÃO
        campo_horizontal("CURSO:", "curso_field", value=st.session_state.curso_display, on_change=processar_curso)
        
        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input", value=date.today().strftime("%d/%m/%Y"))

        st.write("")
        sel1, sel2, sel3 = st.columns(3)
        with sel1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with sel2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with sel3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(),
                        "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(),
                        "Curso": st.session_state.curso_display.strip().upper(),
                        "Pagamento": st.session_state.pagto_input.upper(),
                        "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    # Reset dos campos para novo cadastro
                    st.session_state.curso_display = ""
                    st.session_state.nome_alu = ""
                    st.session_state.id_alu = ""
                    st.rerun()

        with btn2:
            if st.button("📤 FINALIZAR E ENVIAR"):
                if st.session_state.lista_previa:
                    df_sheets = conn.read(ttl="0s").fillna("")
                    df_novos = pd.DataFrame(st.session_state.lista_previa)
                    df_final = pd.concat([df_sheets, df_novos], ignore_index=True)
                    conn.update(data=df_final)
                    st.session_state.lista_previa = []
                    st.success("Enviado com sucesso!")
                    st.rerun()

    st.write("")
    df_vis = pd.DataFrame(st.session_state.lista_previa) if st.session_state.lista_previa else pd.DataFrame(columns=["ID", "Aluno", "Cidade", "Curso", "Pagamento", "Vendedor", "Data"])
    st.dataframe(df_vis, use_container_width=True, hide_index=True, height=180)

with abas[1]:
    st.write("")
    t1, t2 = st.columns([3, 1])
    with t1:
        busca = st.text_input("Filtro CRM", placeholder="🔍 Pesquise...", label_visibility="collapsed").upper()
    with t2: 
        if st.button("🔄 Sincronizar Base"):
            st.cache_data.clear()
            st.rerun()
    
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns:
            dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)

        dados_exibicao = dados.iloc[::-1]

        if busca:
            mask = dados_exibicao.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            dados_exibicao = dados_exibicao[mask]
        
        st.dataframe(
            dados_exibicao, 
            use_container_width=True, 
            hide_index=True, 
            height=600,
            column_config={
                "ID": st.column_config.TextColumn("ID", width=60),
                "Data": st.column_config.TextColumn("Data", width=80),
                "Vendedor": st.column_config.TextColumn("Vendedor", width=100),
                "Cidade": st.column_config.TextColumn("Cidade", width=120),
                "Aluno": st.column_config.TextColumn("Aluno", width=250),
                "Curso": st.column_config.TextColumn("Curso", width=200),
                "Pagamento": st.column_config.TextColumn("Pagamento", width=400),
            }
        )
    except Exception as e:
        st.error(f"Erro: {e}")
