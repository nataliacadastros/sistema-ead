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

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", 
    "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- CONEXÃO E ESTADOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Inicialização de variáveis persistentes
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_acumulado" not in st.session_state: st.session_state.curso_acumulado = ""
if "cidade_fixa" not in st.session_state: st.session_state.cidade_fixa = ""
if "vendedor_fixo" not in st.session_state: st.session_state.vendedor_fixo = ""
if "data_fixa" not in st.session_state: st.session_state.data_fixa = ""

# --- FUNÇÕES DE MÁSCARA E LÓGICA ---
def formatar_cpf(valor):
    v = "".join(filter(str.isdigit, valor))
    if len(v) <= 3: return v
    if len(v) <= 6: return f"{v[:3]}.{v[3:]}"
    if len(v) <= 9: return f"{v[:3]}.{v[3:6]}.{v[6:]}"
    return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"

def formatar_data(valor):
    v = "".join(filter(str.isdigit, valor))
    if len(v) <= 2: return v
    if len(v) <= 4: return f"{v[:2]}/{v[2:]}"
    return f"{v[:2]}/{v[2:4]}/{v[4:8]}"

def processar_curso():
    val = st.session_state.input_curso_raw.strip()
    if val in CODIGOS_CURSOS:
        nome = CODIGOS_CURSOS[val]
        if st.session_state.curso_acumulado:
            st.session_state.curso_acumulado += f" + {nome}"
        else:
            st.session_state.curso_acumulado = nome
        st.session_state.input_curso_raw = "" # Limpa o gatilho
    elif val != "":
        st.session_state.curso_acumulado = val.upper()

# --- INTERFACE ---
with st.sidebar:
    st.title("SISTEMA EAD")
    aba = st.radio("NAVEGAÇÃO", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        id_alu = st.text_input("ID", key="id_field")
        nome_alu = st.text_input("Aluno", key="nome_field")
        tel_r = st.text_input("Tel. Responsável", key="telr_field")
        tel_a = st.text_input("Tel. Aluno", key="tela_field")
        
        # Campo CPF com Máscara
        raw_cpf = st.text_input("CPF Responsável (000.000.000-00)", key="cpf_raw")
        cpf_formatado = formatar_cpf(raw_cpf)
        
        # Persistência de Cidade, Vendedor e Data
        cidade = st.text_input("Cidade", value=st.session_state.cidade_fixa, key="cid_input")
        
        # Campo Curso (Mesmo Campo)
        st.text_input("Curso Contratado (Digite o código e Enter)", 
                      value=st.session_state.curso_acumulado, 
                      key="input_curso_raw", on_change=processar_curso)
        
        pagto = st.text_input("Forma de Pagamento", key="pagto_field")
        vendedor = st.text_input("Vendedor", value=st.session_state.vendedor_fixo, key="vend_input")
        
        # Campo Data com Máscara (Sem Calendário)
        raw_dt = st.text_input("Data da Matrícula (DD/MM/AAAA)", value=st.session_state.data_fixa, key="dt_raw")
        dt_formatada = formatar_data(raw_dt)

        st.write("")
        c1, c2, c3 = st.columns(3)
        lib_ing = c1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c2.checkbox("CURSO BÔNUS")
        confirma = c3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        if btn_col1.button("Salvar Aluno"):
            if nome_alu:
                # Salva na lista prévia
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.curso_acumulado else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.curso_acumulado else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_alu, "Aluno": nome_alu.upper(), "Tel. Resp": tel_r, "Tel. Aluno": tel_a,
                    "CPF": cpf_formatado, "Cidade": cidade.upper(), "Curso": st.session_state.curso_acumulado,
                    "Pagamento": pagto.upper(), "Vendedor": vendedor.upper(), "Data Matrícula": dt_formatada,
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                
                # Mantém Cidade, Vendedor e Data salvos no Estado
                st.session_state.cidade_fixa = cidade
                st.session_state.vendedor_fixo = vendedor
                st.session_state.data_fixa = dt_formatada
                
                # Limpa os campos voláteis e curso
                st.session_state.curso_acumulado = ""
                st.rerun()

        if btn_col2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_nuvem = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                linha_v = pd.DataFrame([{c: "" for c in df_novos.columns}])
                df_final = pd.concat([df_nuvem, df_novos, linha_v], ignore_index=True)
                conn.update(data=df_final)
                
                # ZERA TUDO após enviar para a nuvem
                st.session_state.lista_previa = []
                st.session_state.cidade_fixa = ""
                st.session_state.vendedor_fixo = ""
                st.session_state.data_fixa = ""
                st.success("Enviado e campos resetados!")
                st.rerun()

        btn_col3.button("GERENCIAMENTO MESTRE")

    if st.session_state.lista_previa:
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Curso", "Vendedor"]])

elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True, hide_index=True)
