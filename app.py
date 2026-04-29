import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página
st.set_page_config(page_title="Gerenciamento de Alunos", layout="wide")

# Inicialização do estado da sessão (Banco de dados temporário)
if 'pre_visualizacao' not in st.session_state:
    st.session_state.pre_visualizacao = []
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = []

# Dicionário de Cursos
CURSOS_MAP = {
    "1": "Preparatório Jovem Bancário",
    "2": "10 Cursos Profissionalizantes",
    "3": "Preparatório Agro",
    "4": "Inglês",
    "5": "Jovem no Direito",
    "6": "Pré Militar",
    "7": "Encceja",
    "8": "Jovem na Aviação",
    "9": "Informática",
    "10": "Administração"
}

st.title("🚀 Sistema de Gestão de Alunos")

tab1, tab2 = st.tabs(["📝 Cadastro", "📊 Gerenciamento"])

with tab1:
    st.header("Novo Cadastro")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        id_aluno = st.text_input("ID")
        nome = st.text_input("ALUNO (Nome Completo)")
        tel_resp = st.text_input("TEL. RESPONSÁVEL")
        tel_aluno = st.text_input("TEL. ALUNO")
        
    with col2:
        # Formatação simples de CPF (exemplo didático)
        cpf = st.text_input("CPF RESPONSÁVEL", placeholder="123.456.789-00")
        cidade = st.text_input("CIDADE")
        
        # Automação do Campo CURSO
        curso_input = st.text_input("CURSO (Digite o código ou nome)")
        curso_final = CURSOS_MAP.get(curso_input, curso_input)
        if curso_input in CURSOS_MAP:
            st.info(f"Curso selecionado: **{curso_final}**")

    with col3:
        vendedor = st.text_input("VENDEDOR")
        data_mat = st.date_input("DATA DA MATRÍCULA", value=date.today())
        forma_pagto_base = st.text_area("FORMA DE PAGAMENTO", placeholder="Ex: 12x 49,90 no cartão")

    # Checkboxes de automação
    st.subheader("Observações Adicionais")
    c_lib = st.checkbox("LIB. IN-GLÊS")
    c_bonus = st.checkbox("CURSO BÔNUS")
    c_conf = st.checkbox("CONFIRMAÇÃO")

    # Lógica de concatenação da Forma de Pagamento
    obs = []
    if c_lib: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if c_bonus: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if c_conf: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    
    texto_pagamento_final = forma_pagto_base.upper()
    if obs:
        texto_pagamento_final += " | " + " | ".join(obs)

    if st.button("💾 SALVAR ALUNO (Pré-visualização)"):
        novo_aluno = {
            "ID": id_aluno,
            "ALUNO": nome.upper(),
            "TEL. RESPONSÁVEL": tel_resp,
            "TEL. ALUNO": tel_aluno,
            "CPF": cpf,
            "CIDADE": cidade.upper(),
            "CURSO": curso_final.upper(),
            "PAGAMENTO": texto_pagamento_final.upper(),
            "VENDEDOR": vendedor.upper(),
            "DATA": data_mat.strftime("%d/%m/%Y")
        }
        st.session_state.pre_visualizacao.append(novo_aluno)
        st.success(f"Aluno {nome} adicionado à lista temporária!")

    # Seção de Pré-visualização
    if st.session_state.pre_visualizacao:
        st.divider()
        st.subheader("📋 PRÉ-VISUALIZAÇÃO (Lista Temporária)")
        df_pre = pd.DataFrame(st.session_state.pre_visualizacao)
        st.table(df_pre)
        
        if st.button("✅ FINALIZAR E ENVIAR PARA GERENCIAMENTO"):
            st.session_state.banco_dados.extend(st.session_state.pre_visualizacao)
            st.session_state.pre_visualizacao = [] # Limpa a pré-visualização
            st.rerun()

with tab2:
    st.header("Alunos Cadastrados")
    if st.session_state.banco_dados:
        df_final = pd.DataFrame(st.session_state.banco_dados)
        st.dataframe(df_final, use_container_width=True)
        
        # Opção para exportar
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Planilha (CSV)", csv, "alunos.csv", "text/csv")
    else:
        st.info("Nenhum aluno cadastrado no banco de dados ainda.")
