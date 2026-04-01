import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN COMPACTO ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #004a99 !important; }
    .stTextInput>div>div>input { background-color: white !important; color: black !important; height: 26px !important; font-size: 13px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 13px !important; margin-bottom: -5px !important; }
    .stButton>button { height: 32px; font-size: 12px !important; border-radius: 4px; font-weight: bold; width: 100%; }
    /* Cores dos Botões */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #90ee90 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #a2d2ff !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_display" not in st.session_state: st.session_state.curso_display = ""

# --- INTERFACE ---
with st.sidebar:
    st.title("SISTEMA EAD")
    aba = st.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        id_aluno = st.text_input("ID")
        aluno = st.text_input("Aluno")
        t_resp = st.text_input("Tel. Responsável")
        t_alu = st.text_input("Tel. Aluno")
        cpf = st.text_input("CPF Responsável")
        cidade = st.text_input("Cidade")
        
        # CAMPO DE CURSO COM TRADUÇÃO INSTANTÂNEA
        val_input = st.text_input("Curso Contratado (Digite o número e dê Enter)", key="input_raw")
        
        # Lógica de tradução: Se o que foi digitado está nos códigos, traduzimos e limpamos o input
        if val_input in CODIGOS_CURSOS:
            nome_traduzido = CODIGOS_CURSOS[val_input]
            if st.session_state.curso_display:
                st.session_state.curso_display += f" + {nome_traduzido}"
            else:
                st.session_state.curso_display = nome_traduzido
            # Limpa o campo de entrada para o próximo número e recarrega
            st.rerun()
        elif val_input != "" and val_input not in CODIGOS_CURSOS:
            # Se digitaram um texto que não é número, assume como nome manual
            st.session_state.curso_display = val_input.upper()

        # Exibe o curso atual (acumulado) em um campo desativado ou apenas texto verde
        st.markdown(f"<p style='color:#2ecc71; font-weight:bold; margin-bottom:0;'>CURSO ATUAL: <span style='color:white;'>{st.session_state.curso_display}</span></p>", unsafe_allow_html=True)
        
        if st.button("Limpar Cursos"):
            st.session_state.curso_display = ""
            st.rerun()

        pagto = st.text_input("Forma de Pagamento")
        vend = st.text_input("Vendedor")
        dt_mat = st.date_input("Data da Matrícula", value=date.today())

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib_ing = c1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c2.checkbox("CURSO BÔNUS")
        confirma = c3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Salvar Aluno"):
            if aluno:
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.curso_display else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.curso_display else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": aluno.upper(), "Tel. Resp": t_resp,
                    "Tel. Aluno": t_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": st.session_state.curso_display, "Pagamento": pagto.upper(),
                    "Vendedor": vend.upper(), "Data Matrícula": dt_mat.strftime("%d/%m/%Y"),
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.curso_display = "" # Limpa para o próximo
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_nuvem = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                linha_v = pd.DataFrame([{c: "" for c in df_novos.columns}])
                df_final = pd.concat([df_nuvem, df_novos, linha_v], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.success("PDF Enviado!")
                st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    if st.session_state.lista_previa:
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True, hide_index=True)
