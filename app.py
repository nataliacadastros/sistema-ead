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
    header {visibility: hidden;} footer {visibility: hidden;}
    .stDataFrame { background-color: white !important; color: black !important; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- INICIALIZAÇÃO DE ESTADOS ---
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_display" not in st.session_state: st.session_state.curso_display = ""
if "pagto_input" not in st.session_state: st.session_state.pagto_input = ""

# --- LÓGICA DE CURSOS (SUBSTITUIÇÃO NO CAMPO) ---
def processar_curso():
    # O Streamlit guarda o que foi digitado na chave do widget antes de rodar a função
    texto_digitado = st.session_state.curso_widget.strip()
    
    if texto_digitado:
        # Isolar o último termo (caso o usuário digite "CURSO + 2")
        partes = [p.strip() for p in texto_digitado.split('+')]
        ultimo_termo = partes[-1]
        
        # Se for um código válido, substituímos o código pelo nome
        if ultimo_termo in DIC_CURSOS:
            nome_completo = DIC_CURSOS[ultimo_termo]
            # Removemos o código da lista de partes e adicionamos o nome
            partes[-1] = nome_completo
            
            # Reconstrói a string com " + "
            # Usamos set para evitar duplicados se você preferir, mas join mantém a ordem
            resultado = " + ".join(partes)
            st.session_state.curso_display = resultado.upper()
        else:
            # Se não for código, apenas padroniza para maiúsculo
            st.session_state.curso_display = texto_digitado.upper()
    
    # Regra: Sempre garantir um espaço no final para facilitar a próxima digitação
    st.session_state.curso_display = st.session_state.curso_display.strip() + " "

def atualizar_pagto():
    base = st.session_state.pagto_widget.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: base += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: base += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: base += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = base

# --- ABAS ---
tab1, tab2, tab3 = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab1:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    with col_central:
        st.write("")
        
        # Função auxiliar para campos simples
        def row(label, key, val=None):
            c1, c2 = st.columns([1.2, 4])
            with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
            with c2: return st.text_input(label, label_visibility="collapsed", key=key, value=val)

        row("ID:", "id_alu")
        row("ALUNO:", "nome_alu")
        row("TEL. RESP:", "t_resp")
        row("TEL. ALUNO:", "t_alu")
        row("CIDADE:", "cid_f")
        
        # --- CAMPO CURSO (SUBSTITUIÇÃO IMEDIATA) ---
        c1, c2 = st.columns([1.2, 4])
        with c1: st.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        with c2:
            st.text_input(
                "CURSO", 
                label_visibility="collapsed", 
                key="curso_widget", 
                value=st.session_state.curso_display, # Ele olha para o estado processado
                on_change=processar_curso             # Roda a conversão no Enter
            )

        # --- CAMPO PAGAMENTO ---
        c1, c2 = st.columns([1.2, 4])
        with c1: st.markdown("<label>PAGAMENTO:</label>", unsafe_allow_html=True)
        with c2: st.text_input("PAGAMENTO", label_visibility="collapsed", key="pagto_widget", value=st.session_state.pagto_input)

        row("VENDEDOR:", "vend_f")
        row("DATA:", "data_input", val=date.today().strftime("%d/%m/%Y"))

        st.write("")
        s1, s2, s3 = st.columns(3)
        with s1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with s2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with s3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(),
                        "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(),
                        "Curso": st.session_state.curso_display.strip(),
                        "Pagamento": st.session_state.pagto_widget.upper(),
                        "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    # Reset dos campos
                    st.session_state.curso_display = ""
                    st.session_state.nome_alu = ""
                    st.session_state.id_alu = ""
                    st.rerun()

        with btn2:
            if st.button("📤 FINALIZAR E ENVIAR"):
                if st.session_state.lista_previa:
                    df_base = conn.read(ttl="0s").fillna("")
                    df_novo = pd.DataFrame(st.session_state.lista_previa)
                    conn.update(data=pd.concat([df_base, df_novo], ignore_index=True))
                    st.session_state.lista_previa = []
                    st.success("Enviado!")
                    st.rerun()

    st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

with tab2:
    try:
        dados = conn.read(ttl="0s").fillna("")
        if "ID" in dados.columns:
            dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
        st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True, height=600)
    except:
        st.write("Aguardando dados...")
