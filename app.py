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
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button { background-color: #90ee90 !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button { background-color: #a2d2ff !important; color: black !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) button { background-color: #007bff !important; color: white !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

CURSOS_DICT = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""
if "cidade_p" not in st.session_state: st.session_state.cidade_p = ""
if "vendedor_p" not in st.session_state: st.session_state.vendedor_p = ""
if "data_p" not in st.session_state: st.session_state.data_p = ""

# --- FUNÇÕES DE FORMATAÇÃO ---
def aplicar_mascara_cpf():
    v = "".join(filter(str.isdigit, st.session_state.cpf_input))
    if len(v) == 11:
        st.session_state.cpf_input = f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"

def aplicar_mascara_data():
    v = "".join(filter(str.isdigit, st.session_state.data_input))
    if len(v) == 8:
        st.session_state.data_input = f"{v[:2]}/{v[2:4]}/{v[4:]}"

def processar_curso_contratado():
    # Obtém o texto digitado e remove espaços extras nas pontas
    texto_bruto = st.session_state.curso_field.strip()
    
    # Divide o texto em partes para encontrar o último termo (possível código)
    partes = texto_bruto.split()
    
    if partes:
        ultimo_termo = partes[-1]
        
        # Se o último termo for um código válido no dicionário
        if ultimo_termo in CURSOS_DICT:
            nome_curso = CURSOS_DICT[ultimo_termo].upper()
            
            # Pega o texto que já existia antes desse último código
            texto_anterior = " ".join(partes[:-1])
            
            # Se já houver conteúdo anterior (outro curso), remove o "+" se ele estiver sobrando
            if texto_anterior:
                if texto_anterior.endswith("+"):
                    texto_anterior = texto_anterior[:-1].strip()
                st.session_state.curso_acumulado = f"{texto_anterior} + {nome_curso} "
            else:
                # Primeiro curso do campo
                st.session_state.curso_acumulado = f"{nome_curso} "
        else:
            # Se não for código, mantém o que o usuário escreveu em maiúsculo
            st.session_state.curso_acumulado = texto_bruto.upper() + " "
    
    # Atualiza o widget com o novo valor processado
    st.session_state.curso_field = st.session_state.curso_acumulado

# --- INTERFACE ---
with st.sidebar:
    st.title("SISTEMA EAD")
    aba = st.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        id_alu = st.text_input("ID", key="id_alu")
        nome_alu = st.text_input("Aluno", key="nome_alu")
        tel_r = st.text_input("Tel. Responsável", key="tel_r")
        tel_a = st.text_input("Tel. Aluno", key="tel_a")
        st.text_input("CPF Responsável", key="cpf_input", on_change=aplicar_mascara_cpf)
        cidade = st.text_input("Cidade", value=st.session_state.cidade_p, key="cid_f")
        
        # CAMPO CURSO CONTRATADO COM LÓGICA DE ENTER
        st.text_input("Curso Contratado", 
                      value=st.session_state.curso_acumulado, 
                      key="curso_field", 
                      on_change=processar_curso_contratado)
        
        pagto = st.text_input("Forma de Pagamento", key="pagto")
        vendedor = st.text_input("Vendedor", value=st.session_state.vendedor_p, key="vend_f")
        st.text_input("Data da Matrícula (DDMMYYYY + Enter)", value=st.session_state.data_p, key="data_input", on_change=aplicar_mascara_data)

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib_ing = c1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c2.checkbox("CURSO BÔNUS")
        confirma = c3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Salvar Aluno"):
            if nome_alu:
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.curso_acumulado else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.curso_acumulado else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_alu, "Aluno": nome_alu.upper(), "Tel. Resp": tel_r, "Tel. Aluno": tel_a,
                    "CPF": st.session_state.cpf_input, "Cidade": cidade.upper(), 
                    "Curso": st.session_state.curso_acumulado.strip(), "Pagamento": pagto.upper(), 
                    "Vendedor": vendedor.upper(), "Data Matrícula": st.session_state.data_input,
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.cidade_p = cidade
                st.session_state.vendedor_p = vendedor
                st.session_state.data_p = st.session_state.data_input
                st.session_state.curso_acumulado = ""
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_n = conn.read(ttl="0s").fillna("")
                df_new = pd.DataFrame(st.session_state.lista_previa)
                df_final = pd.concat([df_n, df_new, pd.DataFrame([{c: "" for c in df_new.columns}])], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.session_state.cidade_p = ""; st.session_state.vendedor_p = ""; st.session_state.data_p = ""
                st.session_state.cpf_input = ""; st.session_state.data_input = ""; st.session_state.curso_acumulado = ""
                st.success("PDF Enviado!")
                st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    if st.session_state.lista_previa:
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True, hide_index=True)
