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

# --- CSS ---
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
if "curso_final" not in st.session_state: st.session_state.curso_final = ""

# --- LÓGICA DE CONVERSÃO DE CURSOS ---
def processar_curso():
    # Pega o que foi digitado no campo temporário
    codigo = st.session_state.campo_temp.strip()
    
    if codigo in DIC_CURSOS:
        nome_curso = DIC_CURSOS[codigo]
        
        # Se já houver cursos, concatena com " + "
        if st.session_state.curso_final:
            # Evita adicionar o mesmo curso duas vezes
            if nome_curso not in st.session_state.curso_final:
                st.session_state.curso_final += f" + {nome_curso}"
        else:
            st.session_state.curso_final = nome_curso
            
        # Força maiúsculo e garante o espaço no final para a próxima digitação
        st.session_state.curso_final = st.session_state.curso_final.upper() + " "
    
    # Limpa o campo de digitação após o ENTER para o próximo código
    st.session_state.campo_temp = ""

def atualizar_pagto():
    texto = st.session_state.pagto_input.split(" | ")[0].strip().upper()
    if st.session_state.check_lib: texto += " | APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS"
    if st.session_state.check_bonus: texto += " | CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA"
    if st.session_state.check_conf: texto += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state.pagto_input = texto

def campo_horizontal(label, key, value=None, on_change=None):
    c1, c2 = st.columns([1.2, 4]) 
    with c1: st.markdown(f"<label>{label}</label>", unsafe_allow_html=True)
    with c2: 
        if value is not None:
            return st.text_input(label, label_visibility="collapsed", key=key, value=value, on_change=on_change)
        return st.text_input(label, label_visibility="collapsed", key=key, on_change=on_change)

# --- ABAS ---
tab_cad, tab_ger, tab_rel = st.tabs(["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS"])

with tab_cad:
    _, col_central, _ = st.columns([0.5, 3, 0.5])
    with col_central:
        st.write("")
        campo_horizontal("ID:", "id_alu")
        campo_horizontal("ALUNO:", "nome_alu")
        campo_horizontal("TEL. RESP:", "t_resp")
        campo_horizontal("TEL. ALUNO:", "t_alu")
        campo_horizontal("CIDADE:", "cid_f")
        
        # --- CAMPO DE CURSO (A MÁGICA ACONTECE AQUI) ---
        # Mostramos o resultado final (curso_final) em uma linha informativa logo acima ou usamos o value
        # Para seguir sua regra de digitar no campo e ele converter:
        c1, c2 = st.columns([1.2, 4])
        with c1: st.markdown("<label>CURSO:</label>", unsafe_allow_html=True)
        with c2: 
            # O usuário digita no 'campo_temp', que aciona o 'processar_curso'
            # O valor exibido é o 'curso_final' + o que ele está digitando agora
            st.text_input("CURSO", label_visibility="collapsed", key="campo_temp", 
                          placeholder=st.session_state.curso_final if st.session_state.curso_final else "Digite o código e ENTER",
                          on_change=processar_curso)
            
            # Exibição do que já foi acumulado para o usuário não se perder
            if st.session_state.curso_final:
                st.markdown(f"<p style='color:#2ecc71; font-size:10px; margin-top:-5px;'>Cursos: {st.session_state.curso_final}</p>", unsafe_allow_html=True)

        campo_horizontal("PAGAMENTO:", "pagto_input")
        campo_horizontal("VENDEDOR:", "vend_f")
        campo_horizontal("DATA:", "data_input", value=date.today().strftime("%d/%m/%Y"))

        st.write("")
        s1, s2, s3 = st.columns(3)
        with s1: st.checkbox("LIB. IN-GLÊS", key="check_lib", on_change=atualizar_pagto)
        with s2: st.checkbox("CURSO BÔNUS", key="check_bonus", on_change=atualizar_pagto)
        with s3: st.checkbox("CONFIRMAÇÃO", key="check_conf", on_change=atualizar_pagto)

        b1, b2 = st.columns(2)
        with b1:
            if st.button("💾 SALVAR ALUNO"):
                if st.session_state.nome_alu:
                    aluno = {
                        "ID": st.session_state.id_alu.upper(),
                        "Aluno": st.session_state.nome_alu.upper(),
                        "Cidade": st.session_state.cid_f.upper(),
                        "Curso": st.session_state.curso_final.strip(),
                        "Pagamento": st.session_state.pagto_input.upper(),
                        "Vendedor": st.session_state.vend_f.upper(),
                        "Data": st.session_state.data_input
                    }
                    st.session_state.lista_previa.append(aluno)
                    # Limpa tudo para o próximo
                    st.session_state.curso_final = ""
                    st.session_state.nome_alu = ""
                    st.session_state.id_alu = ""
                    st.rerun()

        with b2:
            if st.button("📤 FINALIZAR E ENVIAR"):
                if st.session_state.lista_previa:
                    df_base = conn.read(ttl="0s").fillna("")
                    df_novo = pd.DataFrame(st.session_state.lista_previa)
                    conn.update(data=pd.concat([df_base, df_novo], ignore_index=True))
                    st.session_state.lista_previa = []
                    st.success("Enviado com sucesso!")
                    st.rerun()

    st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

with tab_ger:
    # ... (O restante do código do gerenciamento permanece igual)
    dados = conn.read(ttl="0s").fillna("")
    if "ID" in dados.columns:
        dados["ID"] = dados["ID"].astype(str).str.replace(r'\.0$', '', regex=True)
    st.dataframe(dados.iloc[::-1], use_container_width=True, hide_index=True)
