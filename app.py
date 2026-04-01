import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide")

# --- CSS PARA REPLICAR O DESIGN DO PRINT ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; }
    label { color: #2ecc71 !important; font-weight: bold !important; font-size: 16px !important; }
    .stButton>button { width: 100%; font-weight: bold; }
    .btn-salvar { background-color: #2ecc71 !important; color: black !important; }
    .btn-pdf { background-color: #76c7c0 !important; color: black !important; }
    .btn-mestre { background-color: #007bff !important; color: white !important; }
    div[data-testid="stForm"] { border: none !important; }
    h1, h2, h3 { color: white !important; text-align: center; }
    .stMetric { background-color: #16161a; border-radius: 10px; padding: 10px; }
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

if "lista_previa" not in st.session_state:
    st.session_state.lista_previa = []

def carregar_dados_nuvem():
    try:
        return conn.read(ttl="0s").fillna("")
    except:
        return pd.DataFrame()

# --- INTERFACE LATERAL ---
st.sidebar.title("MENU")
aba = st.sidebar.radio("Navegação", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    st.markdown("### PROFISSIONALIZA EAD - CADASTRO")
    
    # Centralizando os inputs (Criando colunas para dar margem)
    _, col_central, _ = st.columns([1, 2, 1])
    
    with col_central:
        id_aluno = st.text_input("ID")
        aluno = st.text_input("Aluno")
        tel_resp = st.text_input("Tel. Responsável")
        tel_alu = st.text_input("Tel. Aluno")
        cpf = st.text_input("CPF Responsável")
        cidade = st.text_input("Cidade")
        curso_cod = st.selectbox("Curso Contratado", options=[""] + list(CODIGOS_CURSOS.keys()), 
                                 format_func=lambda x: f"{x} - {CODIGOS_CURSOS[x]}" if x != "" else "Selecione...")
        pagamento = st.text_input("Forma de Pagamento")
        vendedor = st.selectbox("Vendedor", options=["", "GILSON", "OUTRO"]) # Adicione seus vendedores aqui
        data_mat = st.date_input("Data da Matrícula", value=date.today())

        st.write("") # Espaço
        c_check1, c_check2, c_check3 = st.columns(3)
        lib_ing = c_check1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c_check2.checkbox("CURSO BÔNUS")
        confirma = c_check3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        st.write("")
        b1, b2, b3 = st.columns(3)
        
        # BOTÃO SALVAR ALUNO (Manda para a lista provisória)
        if b1.button("Salvar Aluno"):
            if aluno:
                nome_curso = CODIGOS_CURSOS.get(curso_cod, "")
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if curso_cod == "2" else "NÃO",
                    "INGLÊS?": "SIM" if curso_cod == "4" else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": aluno.upper(), "Tel. Resp": tel_resp,
                    "Tel. Aluno": tel_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": nome_curso.upper(), "Pagamento": pagamento.upper(),
                    "Vendedor": vendedor.upper(), "Data Matrícula": data_mat.strftime("%d/%m/%Y"),
                    "OBS1": "teste", "OBS2": "teste"
                }
                st.session_state.lista_previa.append(novo)
                st.rerun()

        # BOTÃO FINALIZAR PDF (Manda a lista provisória para a Nuvem)
        if b2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_nuvem = carregar_dados_nuvem()
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                # Adiciona linha em branco ao final para separar o PDF na planilha
                linha_em_branco = pd.DataFrame([{c: "" for c in df_novos.columns}])
                
                df_final = pd.concat([df_nuvem, df_novos, linha_em_branco], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.success("PDF Finalizado! Dados enviados ao Gerenciador.")
                st.rerun()

        if b3.button("GERENCIAMENTO MESTRE"):
            st.info("Função a ser definida")

    st.markdown(f"<h4 style='text-align: center; color: white;'>Alunos na lista: {len(st.session_state.lista_previa)}</h4>", unsafe_allow_html=True)
    if st.session_state.lista_previa:
        st.table(pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Tel. Resp", "Tel. Aluno", "CPF", "Cidade", "Curso", "Pagamento", "Vendedor", "Data Matrícula"]])

elif aba == "GERENCIAMENTO":
    st.markdown("### GERENCIADOR DE ALUNOS")
    df = carregar_dados_nuvem()
    if not df.empty:
        busca = st.text_input("Buscar Aluno...").upper()
        if busca:
            df = df[df.apply(lambda row: row.astype(str).str.contains(busca).any(), axis=1)]
        st.dataframe(df, use_container_width=True, hide_index=True)

elif aba == "RELATÓRIOS":
    st.header("RELATÓRIOS")
    df_raw = carregar_dados_nuvem()
    if not df_raw.empty:
        df = df_raw[df_raw["Aluno"] != ""]
        st.metric("Total de Alunos", len(df))
        st.plotly_chart(px.bar(df["Vendedor"].value_counts().reset_index(), x="count", y="Vendedor", orientation='h'))
