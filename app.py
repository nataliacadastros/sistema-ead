import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DA PÁGINA (Otimizado para não ter Scroll) ---
st.set_page_config(page_title="PROFISSIONALIZA EAD", layout="wide", initial_sidebar_state="collapsed")

# --- CSS PARA COMPACTAR TUDO NA TELA ---
st.markdown("""
    <style>
    .stApp { background-color: #1a2436; color: white; }
    /* Diminuir fontes e margens */
    html, body, [data-testid="stVerticalBlock"] { font-size: 12px; }
    .stTextInput>div>div>input, .stDateInput>div>div>input { 
        background-color: white !important; color: black !important; height: 25px !important; 
    }
    label { color: #2ecc71 !important; font-weight: bold !important; margin-bottom: 0px !important; padding-bottom: 0px !important; }
    .stButton>button { height: 30px; font-size: 12px !important; border-radius: 2px; }
    .btn-salvar { background-color: #2ecc71 !important; color: black !important; }
    .btn-pdf { background-color: #76c7c0 !important; color: black !important; }
    .btn-mestre { background-color: #007bff !important; color: white !important; }
    /* Ajuste da Tabela Inferior */
    .stTable { font-size: 11px !important; background-color: white; }
    header {display: none !important;}
    footer {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

CODIGOS_CURSOS = {
    "00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR",
    "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"
}

# --- ESTADO E CONEXÃO ---
conn = st.connection("gsheets", type=GSheetsConnection)

if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "curso_texto" not in st.session_state: st.session_state.curso_texto = ""

# --- FUNÇÃO DE TRADUÇÃO DE CÓDIGO (Lógica do seu programa original) ---
def processar_curso():
    texto = st.session_state.input_curso.strip()
    partes = texto.split()
    if not partes: return
    
    ultimo = partes[-1]
    if ultimo in CODIGOS_CURSOS:
        nome_novo = CODIGOS_CURSOS[ultimo]
        base = " ".join(partes[:-1])
        if base:
            novo_texto = f"{base} + {nome_novo} "
        else:
            novo_texto = f"{nome_novo} "
        st.session_state.curso_texto = novo_texto.upper()

# --- INTERFACE ---
aba = st.sidebar.radio("Navegação", ["CADASTRO", "GERENCIAMENTO", "RELATÓRIOS"])

if aba == "CADASTRO":
    # Layout em colunas estreitas para centralizar e diminuir a largura dos campos
    _, col_central, _ = st.columns([1.5, 2, 1.5])
    
    with col_central:
        id_aluno = st.text_input("ID", key="id")
        aluno = st.text_input("Aluno", key="aluno")
        t_resp = st.text_input("Tel. Responsável", key="t_resp")
        t_alu = st.text_input("Tel. Aluno", key="t_alu")
        cpf = st.text_input("CPF Responsável", key="cpf")
        cidade = st.text_input("Cidade", key="cidade")
        
        # Campo de Curso com Lógica de Código
        curso_input = st.text_input("Curso Contratado (Digite o código e espaço)", 
                                    value=st.session_state.curso_texto,
                                    key="input_curso", 
                                    on_change=processar_curso)
        
        pagto = st.text_input("Forma de Pagamento", key="pagto")
        vend = st.text_input("Vendedor", key="vend")
        dt_mat = st.date_input("Data da Matrícula", value=date.today(), key="dt_mat")

        st.write("")
        c_ch1, c_ch2, c_ch3 = st.columns(3)
        lib_ing = c_ch1.checkbox("LIBERAÇÃO IN-GLÊS")
        bonus = c_ch2.checkbox("CURSO BÔNUS")
        confirma = c_ch3.checkbox("AGUARDANDO CONFIRMAÇÃO")

        b1, b2, b3 = st.columns(3)
        if b1.button("Salvar Aluno", key="save_btn"):
            if aluno:
                novo = {
                    "STATUS": "ATIVO", "SEC": "MGA", "TURMA": "", 
                    "10 CURSOS?": "SIM" if "10 CURSOS" in st.session_state.curso_texto else "NÃO",
                    "INGLÊS?": "SIM" if "INGLÊS" in st.session_state.curso_texto else "NÃO", 
                    "Data Cadastro": date.today().strftime("%d/%m/%Y"),
                    "ID": id_aluno, "Aluno": aluno.upper(), "Tel. Resp": t_resp,
                    "Tel. Aluno": t_alu, "CPF": cpf, "Cidade": cidade.upper(),
                    "Curso": st.session_state.curso_texto.strip(), "Pagamento": pagto.upper(),
                    "Vendedor": vend.upper(), "Data Matrícula": dt_mat.strftime("%d/%m/%Y"),
                    "OBS1": "LIB INGLÊS" if lib_ing else "", "OBS2": "BONUS" if bonus else ""
                }
                st.session_state.lista_previa.append(novo)
                st.session_state.curso_texto = "" # Limpa para o próximo
                st.rerun()

        if b2.button("Finalizar PDF"):
            if st.session_state.lista_previa:
                df_atual = conn.read(ttl="0s").fillna("")
                df_novos = pd.DataFrame(st.session_state.lista_previa)
                linha_vazia = pd.DataFrame([{c: "" for c in df_novos.columns}])
                df_final = pd.concat([df_atual, df_novos, linha_vazia], ignore_index=True)
                conn.update(data=df_final)
                st.session_state.lista_previa = []
                st.success("PDF Enviado!")
                st.rerun()

        b3.button("GERENCIAMENTO MESTRE")

    # Tabela de Pré-visualização compacta
    st.markdown(f"<p style='text-align:center; margin:0;'>Alunos na lista: {len(st.session_state.lista_previa)}</p>", unsafe_allow_html=True)
    if st.session_state.lista_previa:
        df_previa = pd.DataFrame(st.session_state.lista_previa)[["ID", "Aluno", "Tel. Resp", "Tel. Aluno", "Curso", "Vendedor"]]
        st.table(df_previa)

# --- GERENCIAMENTO E RELATÓRIOS (Simplificados) ---
elif aba == "GERENCIAMENTO":
    st.dataframe(conn.read(ttl="0s").fillna(""), use_container_width=True)
