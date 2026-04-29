import streamlit as st
import pandas as pd
import re
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from openpyxl import Workbook, load_workbook
from io import BytesIO
from supabase import create_client

# --- 1. CONFIGURAÇÕES TÉCNICAS ---
ARQUIVO_TAGS = "tags_salvas.json"
ARQUIVO_CIDADES = "cidades.xlsx"

# --- CONEXÕES ---
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Erro nas credenciais do Supabase: {e}")

# ADICIONE ESTA FUNÇÃO ABAIXO PARA CORRIGIR O ERRO 2:
def safe_read():
    all_data = []
    step = 1000 
    offset = 0
    try:
        while True:
            # Busca em blocos para contornar o limite de 1000 da API
            res = supabase.table("alunos").select("*").range(offset, offset + step - 1).execute()
            if not res.data: 
                break
            all_data.extend(res.data)
            # Se vier menos que o step, chegamos ao fim dos dados
            if len(res.data) < step: 
                break
            offset += step
            
        if all_data:
            return pd.DataFrame(all_data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao sincronizar dados com o Supabase: {e}")
        return pd.DataFrame()
# --- MOTOR DE DADOS (SUPABASE + MEMÓRIA RAM) ---

def sincronizar_banco_completo():
    """Busca todos os registros do banco sem limite de 1000 linhas."""
    all_data = []
    step = 1000
    offset = 0
    try:
        while True:
            res = supabase.table("alunos").select("*").range(offset, offset + step - 1).execute()
            if not res.data: break
            all_data.extend(res.data)
            if len(res.data) < step: break
            offset += step
        return pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"Erro na sincronização: {e}")
        return pd.DataFrame()

def atualizar_sistema():
    """Recarrega a memória interna e limpa caches de relatórios."""
    with st.spinner("📥 Sincronizando sistema com o backup..."):
        st.session_state.banco_interno = sincronizar_banco_completo()
        st.cache_data.clear()

# Inicialização automática ao abrir o app
if "banco_interno" not in st.session_state:
    atualizar_sistema()

def salvar_mudancas_aluno(id_aluno, novos_dados):
    """Atualiza o aluno no Backup e reflete instantaneamente no Gerenciamento."""
    try:
        # 1. Atualiza no Supabase (Backup)
        supabase.table("alunos").update(novos_dados).eq("ID", id_aluno).execute()
        
        # 2. Localiza o aluno na memória interna (st.session_state) e atualiza
        df = st.session_state.banco_interno
        idx = df.index[df['ID'] == id_aluno]
        
        if not idx.empty:
            for coluna, valor in novos_dados.items():
                st.session_state.banco_interno.at[idx[0], coluna] = valor
            st.success(f"Alterações salvas para o ID {id_aluno}!")
            return True
    except Exception as e:
        st.error(f"Erro ao salvar alterações: {e}")
        return False

def carregar_tags():
    padrao = {"tags": {}, "last_selection": {}}
    if os.path.exists(ARQUIVO_TAGS):
        try:
            with open(ARQUIVO_TAGS, "r", encoding="utf-8") as f:
                return json.load(f)
        except: 
            return padrao
    return padrao

def salvar_tags(dados):
    try:
        with open(ARQUIVO_TAGS, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar tags: {e}")

# Inicializa as tags na sessão
if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()


# --- DEFINIÇÃO DO CAMINHO DA LOGO ---
diretorio_atual = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(diretorio_atual, "logo.png")

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="SISTEMA ADM | PROFISSIONALIZA", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    page_icon=caminho_logo if os.path.exists(caminho_logo) else None
)

# --- CSS HUD NEON ---
st.markdown("""
    <style>
    .stApp { background-color: #0b0e1e; color: #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { 
        background-color: #121629; border-bottom: 1px solid #1f295a;
        position: fixed; top: 0; left: 0 !important; width: 100vw !important;
        z-index: 999; justify-content: center; height: 35px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-size: 11px !important; padding: 0 30px !important; }
    .stTabs [aria-selected="true"] { color: #00f2ff !important; border-bottom: 2px solid #00f2ff !important; background-color: rgba(0, 242, 255, 0.05) !important; }
    
    .main .block-container { padding-top: 40px !important; max-width: 100% !important; margin: 0 auto !important; }
    
    label { color: #00f2ff !important; font-weight: bold !important; font-size: 17px !important; display: flex; align-items: center; justify-content: flex-end; }
    
    .stTabs div[data-testid="stTextInput"] input { text-transform: uppercase !important; }
    
    .stTextInput input { background-color: white !important; color: black !important; font-size: 12px !important; height: 18px !important; border-radius: 5px !important; }
    .stCheckbox label p { color: #2ecc71 !important; font-weight: bold !important; font-size: 11px !important; }

    .custom-table-wrapper { width: 100%; max-height: 600px; overflow: auto; background-color: #121629; border: 2px solid #1f295a; border-radius: 10px; margin-top: 15px; }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 2500px !important; }
    .custom-table th { background-color: #1f295a; color: #00f2ff; text-align: left; padding: 15px; font-size: 11px; text-transform: uppercase; position: sticky; top: 0; z-index: 99; }
    .custom-table td { padding: 12px; border-bottom: 1px solid #1f295a; font-size: 11px; color: #e0e0e0; white-space: pre-wrap !important; }
    
    .card-hud { background: rgba(18, 22, 41, 0.7); border: 1px solid #1f295a; padding: 12px; border-radius: 10px; text-align: center; height: 100%; min-height: 110px; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .neon-pink { color: #ff007a; border-top: 2px solid #ff007a; }
    .neon-green { color: #2ecc71; border-top: 2px solid #2ecc71; }
    .neon-blue { color: #00f2ff; border-top: 2px solid #00f2ff; }
    .neon-purple { color: #bc13fe; border-top: 2px solid #bc13fe; }
    .neon-red { color: #ff4b4b; border-top: 2px solid #ff4b4b; }
    
    div.stButton > button { background-color: #00f2ff !important; color: #000000 !important; font-weight: bold !important; border: none !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    .logo-container { position: relative; top: -10px; left: 0px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZAÇÃO DE ESTADOS ---
if "dados_tags" not in st.session_state:
    st.session_state.dados_tags = carregar_tags()
if "lista_previa" not in st.session_state: st.session_state.lista_previa = []
if "reset_aluno" not in st.session_state: st.session_state.reset_aluno = 0
if "reset_geral" not in st.session_state: st.session_state.reset_geral = 0
if "df_final_processado" not in st.session_state: st.session_state.df_final_processado = None

# --- DICIONÁRIOS E FUNÇÕES MOTOR ---
DIC_CURSOS = {"00": "COLÉGIO COMBO", "1": "PREPARATÓRIO JOVEM BANCÁRIO", "2": "10 CURSOS PROFISSIONALIZANTES", "3": "PREPARATÓRIO AGRO", "4": "INGLÊS", "5": "JOVEM NO DIREITO", "6": "PRÉ MILITAR", "7": "PREPARATÓRIO ENCCEJA", "8": "JOVEM NA AVIAÇÃO", "9": "INFORMÁTICA", "10": "ADMINISTRAÇÃO"}

def transformar_curso(chave):
    entrada = st.session_state[chave].strip()
    if not entrada: return
    match = re.search(r'(\d+)$', entrada)
    if match:
        codigo = match.group(1); nome = DIC_CURSOS.get(codigo)
        if nome:
            base = entrada[:match.start()].strip().rstrip('+').strip()
            st.session_state[chave] = (f"{base} + {nome}" if base and nome.upper() not in base.upper() else (base if base else nome)).upper()
    else: st.session_state[chave] = entrada.upper()

def extrair_valor_geral(texto):
    if not texto: return 0.0
    try:
        v = re.findall(r'\d+(?:\.\d+)?(?:,\d+)?', str(texto).replace('.', '').replace(',', '.'))
        return float(v[0]) if v else 0.0
    except: return 0.0

def atualizar_pagamento():
    suffix = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
    base = st.session_state.get(f"f_pagto_{suffix}", "").split('|')[0].strip()
    novo = base
    if st.session_state.get(f"chk_1_{suffix}"): novo += " | Após pagamento link cartão, avisar Natália para liberação In-glês"
    if st.session_state.get(f"chk_2_{suffix}"): novo += " | Caso pague via link cartão, avisar Natália para liberação curso bônus a escolha"
    if st.session_state.get(f"chk_3_{suffix}"): novo += " | AGUARDANDO CONFIRMAÇÃO DA MATRÍCULA"
    st.session_state[f"f_pagto_{suffix}"] = novo.upper()

def formatar_cpf(chave):
    valor = re.sub(r'\D', '', st.session_state[chave])
    if len(valor) == 11: st.session_state[chave] = f"{valor[:3]}.{valor[3:6]}.{valor[6:9]}-{valor[9:]}"

def reset_campos_subir():
    for c in ["in_user", "in_nome", "in_cell", "in_doc", "in_city", "in_cour", "in_pay", "in_sell", "in_date"]:
        if c in st.session_state: st.session_state[c] = ""
    st.session_state.df_final_processado = None

# --- LOGO ---
if os.path.exists(caminho_logo):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(caminho_logo, width=90)
    st.markdown('</div>', unsafe_allow_html=True)

# --- ABAS DO SISTEMA ---
lista_abas = ["📑 CADASTRO", "🖥️ GERENCIAMENTO", "📊 RELATÓRIOS", "📤 SUBIR ALUNOS"]
tab_cad, tab_ger, tab_rel, tab_subir = st.tabs(lista_abas)

# --- ABA 1: CADASTRO ---
if tab_cad: 
    with tab_cad:
        _, centro, _ = st.columns([0.2, 5.6, 0.2])
        
        with centro:
            # Suffixos para evitar conflito de IDs de widgets
            s_al = f"a_{st.session_state.reset_aluno}_{st.session_state.reset_geral}"
            s_ge = f"g_{st.session_state.reset_geral}"
            
            fields = [
                ("ID:", f"f_id_{s_al}"), 
                ("ALUNO:", f"f_nome_{s_al}"), 
                ("TEL. RESPONSÁVEL:", f"f_tel_resp_{s_al}"),
                ("TEL. ALUNO:", f"f_tel_aluno_{s_al}"), 
                ("CPF RESPONSÁVEL:", f"f_cpf_{s_al}"), 
                ("CIDADE:", f"f_cid_{s_ge}"),
                ("CURSO CONTRATADO:", f"input_curso_key_{s_al}"), 
                ("FORMA DE PAGAMENTO:", f"f_pagto_{s_al}"),
                ("VENDEDOR:", f"f_vend_{s_ge}"), 
                ("DATA DA MATRÍCULA:", f"f_data_{s_ge}")
            ]
            
            for l, k in fields:
                cl, ci = st.columns([1.2, 3.8])
                cl.markdown(f"<label>{l}</label>", unsafe_allow_html=True)
                if "curso" in k: 
                    ci.text_input(l, key=k, on_change=transformar_curso, args=(k,), label_visibility="collapsed")
                elif "f_cpf" in k: 
                    ci.text_input(l, key=k, on_change=formatar_cpf, args=(k,), label_visibility="collapsed")
                else: 
                    ci.text_input(l, key=k, label_visibility="collapsed")
            
            st.write("")
            _, c1, c2, c3, _ = st.columns([1.2, 1.2, 1.2, 1.2, 0.2])
            c1.checkbox("LIB. IN-GLÊS", key=f"chk_1_{s_al}", on_change=atualizar_pagamento)
            c2.checkbox("CURSO BÔNUS", key=f"chk_2_{s_al}", on_change=atualizar_pagamento)
            c3.checkbox("CONFIRMAÇÃO", key=f"chk_3_{s_al}", on_change=atualizar_pagamento)
            
            st.write("")
            _, b1, b2, _ = st.columns([1.2, 1.9, 1.9, 0.2])
            
            with b1:
                if st.button("💾 SALVAR NA LISTA"):
                    if st.session_state[f"f_nome_{s_al}"]:
                        st.session_state.lista_previa.append({
                            "ID": st.session_state[f"f_id_{s_al}"].upper(),
                            "Nome": st.session_state[f"f_nome_{s_al}"].upper(),
                            "Tel_Resp": str(st.session_state[f"f_tel_resp_{s_al}"]), 
                            "Tel_Aluno": str(st.session_state[f"f_tel_aluno_{s_al}"]),
                            "CPF": st.session_state[f"f_cpf_{s_al}"],
                            "Cidade": st.session_state[f"f_cid_{s_ge}"].upper(), 
                            "Curso": st.session_state[f"input_curso_key_{s_al}"].upper(),
                            "Pagamento": st.session_state[f"f_pagto_{s_al}"].upper(),
                            "Vendedor": st.session_state[f"f_vend_{s_ge}"].upper(),
                            "Data_Matricula": st.session_state[f"f_data_{s_ge}"]
                        })
                        st.session_state.reset_aluno += 1
                        st.rerun()
                    else:
                        st.warning("Preencha pelo menos o nome do aluno.")
                        
            with b2:
                if st.button("📤 ENVIAR PARA O BACKUP (Supabase)"):
                    if st.session_state.lista_previa:
                        try:
                            # 1. Envia os dados para a tabela 'alunos' do Supabase
                            # Nota: Certifique-se que os nomes das chaves batem com as colunas do banco
                            res = supabase.table("alunos").insert(st.session_state.lista_previa).execute()
                            
                            # 2. Limpa a lista de espera
                            st.session_state.lista_previa = []
                            st.session_state.reset_geral += 1
                            
                            # 3. ATUALIZAÇÃO CRÍTICA: Sincroniza a memória interna imediatamente
                            # Isso faz com que o novo aluno apareça no Gerenciamento na hora
                            st.session_state.banco_interno = sincronizar_banco_completo()
                            
                            st.success("Dados sincronizados com o backup com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao enviar para o Supabase: {e}")
                    else:
                        st.info("Nenhum aluno na lista de pré-visualização.")
            
            if st.session_state.lista_previa: 
                st.markdown(f"### 📋 PRÉ-VISUALIZAÇÃO ({len(st.session_state.lista_previa)} ALUNOS)")
                st.dataframe(pd.DataFrame(st.session_state.lista_previa), use_container_width=True, hide_index=True)

# --- ABA 2: GERENCIAMENTO ---
with tab_ger:
    st.header("📋 Gerenciador Interno de Alunos")
    
    # Botão de Sincronização Manual (Caso você queira atualizar o 'backup')
    if st.button("🔄 ATUALIZAR MEMÓRIA (Puxar do Supabase)"):
        st.session_state.banco_interno = sincronizar_banco_completo()
        st.success("Memória interna atualizada!")
        st.rerun()

    df_memoria = st.session_state.banco_interno

    if df_memoria.empty:
        st.info("Nenhum aluno carregado na memória.")
    else:
        st.write(f"Total de alunos no sistema: **{len(df_memoria)}**")
        
        # Busca Instantânea (Acontece na memória do seu PC, sem internet)
        busca = st.text_input("🔍 Pesquisar aluno (Nome, CPF ou ID):")
        
        if busca:
            df_exibir = df_memoria[df_memoria.astype(str).apply(lambda x: x.str.contains(busca, case=False, na=False)).any(axis=1)]
        else:
            df_exibir = df_memoria

        st.dataframe(df_exibir, use_container_width=True, hide_index=True, height=500)

        st.write("---")
        
        # Área de Edição
        st.subheader("📝 Editar Registro")
        id_pesquisa = st.text_input("ID para editar:", key="id_edit_ger")
        
        if st.button("🔍 CARREGAR DADOS"):
            aluno = df_memoria[df_memoria['ID'].astype(str) == id_pesquisa.strip()]
            if not aluno.empty:
                st.session_state.dados_aluno = aluno.iloc[0].to_dict()
                st.success(f"Aluno {st.session_state.dados_aluno.get('Nome', '')} carregado!")
            else:
                st.error("ID não encontrado na memória local.")


# --- ABA 4: SUBIR ALUNOS ---
if tab_subir:
    with tab_subir:
        st.markdown("### 📤 IMPORTAÇÃO EAD")
        
        modo = st.radio("Método:", ["MANUAL", "AUTOMÁTICO"], horizontal=True)
        st.write("---")
        
        if modo == "AUTOMÁTICO":
            df_m = safe_read()
            if not df_m.empty:
                try:
                    col_f = df_m.columns[5]
                    df_m[col_f] = pd.to_datetime(df_m[col_f], dayfirst=True, errors='coerce')
                    data_sel = st.date_input("Filtrar Cadastro (Coluna F):", value=date.today())
                    df_filtrado = df_m[df_m[col_f].dt.date == data_sel]
                    
                    if not df_filtrado.empty:
                        cids = sorted(df_filtrado[df_m.columns[11]].unique())
                        sel_cids = st.multiselect("Cidades:", cids)
                        st.session_state.df_auto_ready = df_filtrado[df_filtrado[df_m.columns[11]].isin(sel_cids)]
                        st.info(f"{len(st.session_state.df_auto_ready)} alunos encontrados.")
                except: 
                    st.error("Erro ao processar colunas da planilha automática.")
        else:
            c1, c2 = st.columns(2)
            with c1:
                u_user = st.text_area("IDs", height=100, key="in_user")
                u_cell = st.text_area("Celulares", height=100, key="in_cell")
                u_city = st.text_area("Cidades", height=100, key="in_city")
                u_pay = st.text_area("Pagamentos", height=100, key="in_pay")
            with c2:
                u_nome = st.text_area("Nomes", height=100, key="in_nome")
                u_doc = st.text_area("Documentos", height=100, key="in_doc")
                u_cour = st.text_area("Cursos", height=100, key="in_cour")
                u_sell = st.text_area("Vendedores", height=100, key="in_sell")
            u_date = st.text_area("Datas", height=100, key="in_date")

        with st.expander("🛠️ CONFIGURAR TAGS", expanded=False):
            cursos_tags = ['PREPARATÓRIO JOVEM BANCÁRIO', 'PREPARATÓRIO AGRO', 'JOVEM NO DIREITO', 'INGLÊS', 'PRÉ MILITAR', 'ADMINISTRATIVO', 'INFORMÁTICA', 'PREPARATÓRIO ENCCEJA', 'JOVEM NA AVIAÇÃO', 'TECNOLOGIA']
            cols = st.columns(3)
            selected_tags = {}
            for i, curso in enumerate(cursos_tags):
                with cols[i % 3]:
                    st.markdown(f"<p style='font-size:10px; margin-bottom:2px; color:#00f2ff; font-weight:bold;'>{curso}</p>", unsafe_allow_html=True)
                    tags_lista = st.session_state.dados_tags.get("tags", {}).get(curso, [])
                    last_sel = st.session_state.dados_tags.get("last_selection", {}).get(curso, "")
                    
                    # Define o index baseado na última escolha
                    idx_default = (tags_lista.index(last_sel) + 1) if last_sel in tags_lista else 0
                    
                    c_sel, c_del = st.columns([0.4, 0.6])
                    cur_tag = c_sel.selectbox("", [""] + tags_lista, index=idx_default, key=f"sel_{curso}", label_visibility="collapsed")
                    
                    if cur_tag != last_sel:
                        st.session_state.dados_tags["last_selection"][curso] = cur_tag
                        salvar_tags(st.session_state.dados_tags)
                    
                    if c_del.button("🗑️", key=f"del_{curso}"):
                        if cur_tag and cur_tag in st.session_state.dados_tags["tags"][curso]:
                            st.session_state.dados_tags["tags"][curso].remove(cur_tag)
                            st.session_state.dados_tags["last_selection"][curso] = ""
                            salvar_tags(st.session_state.dados_tags)
                            st.rerun()
                    
                    c_new, _ = st.columns([0.4, 0.6])
                    new_tag = c_new.text_input("", placeholder="Nova...", key=f"new_{i}", label_visibility="collapsed").upper()
                    if new_tag and new_tag not in tags_lista:
                        if curso not in st.session_state.dados_tags["tags"]: st.session_state.dados_tags["tags"][curso] = []
                        st.session_state.dados_tags["tags"][curso].append(new_tag)
                        st.session_state.dados_tags["last_selection"][curso] = new_tag
                        salvar_tags(st.session_state.dados_tags)
                        st.rerun()
                    selected_tags[curso] = (new_tag if new_tag else cur_tag).upper()

if st.button("🚀 PROCESSAR DADOS", use_container_width=True):
            raw_list = []
            if modo == "MANUAL":
                l_ids = u_user.strip().split('\n')
                l_nomes = u_nome.strip().split('\n')
                l_pays = u_pay.strip().split('\n')
                l_cours = u_cour.strip().split('\n')
                l_cells = u_cell.strip().split('\n')
                l_docs = u_doc.strip().split('\n')
                l_citys = u_city.strip().split('\n')
                l_sells = u_sell.strip().split('\n')
                l_dates = u_date.strip().split('\n')
                min_len = len(l_ids)
                if min_len > 0:
                    for i in range(min_len):
                        try:
                            raw_list.append({
                                "User": l_ids[i], "Nome": l_nomes[i], "Pay": l_pays[i], 
                                "Cour": l_cours[i], "Cell": l_cells[i], "Doc": l_docs[i], 
                                "City": l_citys[i], "Sell": l_sells[i], "Date": l_dates[i]
                            })
                        except: continue
            elif "df_auto_ready" in st.session_state and st.session_state.df_auto_ready is not None:
                for _, r in st.session_state.df_auto_ready.iterrows():
                    raw_list.append({"User": r.iloc[6], "Nome": r.iloc[7], "Cell": r.iloc[9], "Doc": r.iloc[10], "City": r.iloc[11], "Cour": r.iloc[12], "Pay": r.iloc[13], "Sell": r.iloc[14], "Date": r.iloc[15]})
            
            if raw_list:
                try:
                    wb_c = load_workbook(ARQUIVO_CIDADES)
                    ws_c = wb_c.active
                    c_map = {str(r[1]).strip().upper(): str(r[2]) for r in ws_c.iter_rows(min_row=2, values_only=True) if r[1]}
                except: c_map = {}
                
                processed = []
                for item in raw_list:
                    c_orig = str(item['Cour']).upper()
                    p_orig = str(item['Pay']).upper()

                    posicoes_tags = []
                    for curso_nome, tag_valor in selected_tags.items():
                        if tag_valor:
                            pos = c_orig.find(curso_nome.upper())
                            if pos != -1:
                                posicoes_tags.append((pos, tag_valor))

                    posicoes_tags.sort()
                    tags_f = [t[1] for t in posicoes_tags]
                    c_final = ",".join(tags_f).upper() if tags_f else c_orig

                    p_final = "PENDENTE"
                    has_bol = "BOLETO" in p_orig
                    has_car = "CARTÃO" in p_orig or "LINK" in p_orig
                    if (has_bol and not has_car): p_final = "BOLETO"
                    elif (has_car and not has_bol): p_final = "CARTÃO"
                    
                    obs_final = f"{c_final} | {c_orig} | {p_orig}".upper()
                    ouro_val = "1" if "10 CURSOS PROFISSIONALIZANTES" in obs_final else "0"
                    
                    processed.append({
                        "username": item['User'], "email2": f"{item['User']}@profissionalizaead.com.br", 
                        "name": str(item['Nome']).split(" ")[0].upper(), 
                        "lastname": " ".join(str(item['Nome']).split(" ")[1:]).upper(), 
                        "cellphone2": str(item['Cell']), "document": item['Doc'], 
                        "city2": c_map.get(str(item['City']).upper(), item['City']), 
                        "courses": c_final, "payment": p_final, "observation": obs_final, 
                        "ouro": ouro_val, "password": "futuro", "role": "1", 
                        "secretary": "MGA", "seller": item['Sell'], "contract_date": item['Date'], "active": "1"
                    })
                st.session_state.df_final_processado = pd.DataFrame(processed)

if st.session_state.df_final_processado is not None:
            df = st.session_state.df_final_processado
            mask = df['payment'] == "PENDENTE"
            if mask.any():
                st.warning("⚠️ Confirmação necessária:")
                df_conf = df.loc[mask, ["username", "name", "observation"]].copy()
                df_conf.columns = ["ID", "Nome", "Texto Original (Pagamento)"]
                df_conf["Forma Final"] = "BOLETO"
                edited = st.data_editor(df_conf, column_config={"Forma Final": st.column_config.SelectboxColumn("Forma", options=["BOLETO", "CARTÃO"], required=True)}, disabled=["ID", "Nome", "Texto Original (Pagamento)"], hide_index=True, use_container_width=True, key="pag_editor")
                if st.button("✅ CONFIRMAR E GERAR EXCEL"):
                    for _, row in edited.iterrows(): 
                        df.loc[df['username'] == row["ID"], "payment"] = row["Forma Final"]
                    st.session_state.df_final_processado = df
                    st.rerun()
            
            if not (st.session_state.df_final_processado['payment'] == "PENDENTE").any():
                output = BytesIO()
                wb = Workbook()
                ws = wb.active
                ws.append(list(st.session_state.df_final_processado.columns))
                for r in st.session_state.df_final_processado.values.tolist(): 
                    ws.append([str(val) for val in r])
                wb.save(output)
                st.download_button("📥 BAIXAR EXCEL FINAL", output.getvalue(), f"ead_{date.today()}.xlsx", on_click=reset_campos_subir, use_container_width=True)


# --- SIDEBAR (BARRA LATERAL) ---
# Certifique-se de que o "with" está colado na margem esquerda
with st.sidebar:
    st.markdown("### 🖥️ Painel de Controle")
    st.write("Bem-vindo ao Sistema")
    # Removi as linhas de 'Logado' e 'Nível' que causavam erro
