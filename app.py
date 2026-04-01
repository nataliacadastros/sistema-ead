import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA (Menu sempre aberto e sem margens) ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="expanded")

# --- CSS PARA DESIGN IDENTICO AO PRINT E SEM SCROLL ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    [data-testid="stSidebar"] { background-color: #005bb7 !important; min-width: 200px !important; }
    .stTextInput>div>div>input { background-color: white !important; color: black !important; height: 22px !important; font-size: 13px !important; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 13px !important; margin-bottom: -5px !important; }
    .stButton>button { height: 28px; font-size: 11px !important; border-radius: 2px; margin-top: 10px; }
    /* Cores dos Botões */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #2ecc71 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #76c7c0 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    /* Ajuste para eliminar espaços em branco no topo */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""

# --- FUNÇÃO DE PROCESSAMENTO DO CURSO ---
def atualizar_curso():
    entrada = st.session_state.campo_digita_curso.strip()
    if entrada in CODIGOS_CURSOS:
        nome_novo = CODIGOS_CURSOS[entrada]
        if st.session_state.curso_acumulado:
            st.session_state.curso_acumulado += f" + {nome_novo}"
        else:
            st.session_state.curso_acumulado = nome_novo
    # Limpa o campo de digitação após o Enter para o próximo número
    st.session_state.campo_digita_curso = ""

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
        
        # LÓGICA DE CURSO: Um campo para digitar o número e outro que mostra o resultado
        st.text_input("Digitar Código do Curso (Dê Enter)", key="campo_digita_curso", on_change=atualizar_curso)
        curso_final = st.text_input("Curso Contratado (Resultado)", value=st.session_state.curso_acumulado.upper())
        
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
                    "10 CURSOS?": "SIM" if "10 CURSOS" in curso_final else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in curso_final else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": aluno.upper(), "Tel. Resp": t_resp,
                    "Tel. Aluno": t_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": curso_final, "Pagamento": pagto.upper(),
                    "Vendedor": vend.upper(), "Data Matrícula": dt_mat.strftime("%d/%m/%Y"),
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.curso_acumulado = "" # Reseta para o próximo aluno
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_nuvem = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                linha_v = pd.DataFrame([{c: "" for c in df_novos.columns}])
                df_final = pd.concat([df_nuvem, df_novos, linha_v], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.success("Enviado!")
                st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    # Lista de pré-visualização embaixo
    if st.session_state.lista_previa:
        st.markdown(f"<p style='text-align:center; color:white; margin:0;'>Alunos na lista: {len(st.session_state.lista_previa)}</p>", unsafe_allow_html=True)
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True, hide_index=True)

elif aba == "RELATÓRIOS":
    st.write("Em desenvolvimento...")
