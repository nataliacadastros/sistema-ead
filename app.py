import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página
st.set_page_config(page_title="Gerenciamento de Alunos", layout="centered")

# Inicialização do estado da sessão
if 'pre_visualizacao' not in st.session_state:
    st.session_state.pre_visualizacao = []
if 'banco_dados' not in st.session_state:
    st.session_state.banco_dados = []

# Tabela de Conversão de Cursos
CURSOS_MAP = {
    "1": "PREPARATÓRIO JOVEM BANCÁRIO",
    "2": "10 CURSOS PROFISSIONALIZANTES",
    "3": "PREPARATÓRIO AGRO",
    "4": "INGLÊS",
    "5": "JOVEM NO DIREITO",
    "6": "PRÉ MILITAR",
    "7": "ENCCEJA",
    "8": "JOVEM NA AVIAÇÃO",
    "9": "INFORMÁTICA",
    "10": "ADMINISTRAÇÃO"
}

st.title("🚀 Gestão de Alunos")

tab1, tab2 = st.tabs(["📝 Cadastro", "📊 Gerenciamento"])

with tab1:
    st.header("Cadastro de Aluno")
    
    # Campos um embaixo do outro
    id_aluno = st.text_input("ID")
    nome = st.text_input("ALUNO")
    tel_resp = st.text_input("TEL. RESPONSÁVEL")
    tel_aluno = st.text_input("TEL. ALUNO")
    
    # CPF com sugestão de formato
    cpf = st.text_input("CPF RESPONSÁVEL", placeholder="000.000.000-00")
    
    cidade = st.text_input("CIDADE")
    
    # Campo CURSO Inteligente
    curso_raw = st.text_input("CURSO CONTRATADO (Código ou Nome)")
    curso_nome = CURSOS_MAP.get(curso_raw, curso_raw).upper()
    if curso_raw in CURSOS_MAP:
        st.caption(f"✅ Identificado: {curso_nome}")

    vendedor = st.text_input("VENDEDOR")
    data_mat = st.date_input("DATA DA MATRÍCULA", value=date.today())
    
    forma_pagto_base = st.text_input("FORMA DE PAGAMENTO", placeholder="Digite o valor/condição aqui")

    # Checkboxes de automação (Abaixo da forma de pagamento)
    st.write("---")
    c_lib = st.checkbox("☑ LIB. IN-GLÊS")
    c_bonus = st.checkbox("☑ CURSO BÔNUS")
    c_conf = st.checkbox("☑ CONFIRMAÇÃO")

    # Lógica de concatenação
    obs = []
    if c_lib: obs.append("APÓS PAGAMENTO LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO IN-GLÊS")
    if c_bonus: obs.append("CASO PAGUE VIA LINK CARTÃO, AVISAR NATÁLIA PARA LIBERAÇÃO CURSO BÔNUS A ESCOLHA")
    if c_conf: obs.append("AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA")
    
    texto_pagamento_final = forma_pagto_base.upper()
    if obs:
        texto_pagamento_final += " | " + " | ".join(obs)

    st.write("---")
    if st.button("💾 SALVAR ALUNO"):
        novo_aluno = {
            "ID": id_aluno,
            "ALUNO": nome.upper(),
            "TEL. RESPONSÁVEL": tel_resp,
            "TEL. ALUNO": tel_aluno,
            "CPF": cpf,
            "CIDADE": cidade.upper(),
            "CURSO": curso_nome,
            "PAGAMENTO": texto_pagamento_final,
            "VENDEDOR": vendedor.upper(),
            "DATA": data_mat.strftime("%d/%m/%Y")
        }
        st.session_state.pre_visualizacao.append(novo_aluno)
        st.toast(f"Aluno {nome.split()[0]} enviado para pré-visualização!")

    # Seção de Pré-visualização
    if st.session_state.pre_visualizacao:
        st.subheader("📋 PRÉ-VISUALIZAÇÃO")
        df_pre = pd.DataFrame(st.session_state.pre_visualizacao)
        st.dataframe(df_pre)
        
        if st.button("📤 Enviar todos para Gerenciamento"):
            st.session_state.banco_dados.extend(st.session_state.pre_visualizacao)
            st.session_state.pre_visualizacao = [] 
            st.success("Dados enviados com sucesso!")
            st.rerun()

with tab2:
    st.header("Base de Dados")
    if st.session_state.banco_dados:
        df_final = pd.DataFrame(st.session_state.banco_dados)
        st.dataframe(df_final, use_container_width=True)
    else:
        st.info("Nenhum registro finalizado.")
