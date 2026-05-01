import streamlit as st
from datetime import date
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.auth import get_current_user, require_page_access
from db.crud import get_bancadas, get_culturas, get_filetes_by_bancada, inserir_bancada, inserir_filete

st.set_page_config(page_title="Hydroponic Monitor", layout="wide")

st.title("🌱 HydroTwin - Painel de Controle")

# Verificar autenticação e acesso
usuario = get_current_user()
if usuario is None:
    st.error("❌ Você precisa estar autenticado para acessar esta página.")
    st.stop()

require_page_access(usuario, "Painel de Controle - Bancadas")

# Separar em abas
tab1, tab2 = st.tabs(["📋 Bancadas Cadastradas", "➕ Nova Bancada"])

# =========================
# TAB 1: LISTAR BANCADAS
# =========================
with tab1:
    st.header("Bancadas Cadastradas", help="Visualize e gerencie suas bancadas e filetes")
    
    bancadas = get_bancadas()
    
    if not bancadas:
        st.info("Nenhuma bancada cadastrada ainda. Crie uma nova bancada para começar!")
    else:
        bancadas.sort(key=lambda x: x[0])  # Ordenar por ID da bancada
        for bancada_id, nome_bancada, cultura_nome, filete_id, data_plantio, data_colheita in bancadas:
            with st.expander(f"🌿 {nome_bancada}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**ID da Bancada:** {bancada_id}")
                    
                    # Mostrar filetes dessa bancada
                    filetes = get_filetes_by_bancada(bancada_id)
                    
                    st.markdown("**Filetes Ativas:**")
                    if filetes:
                        filetes.sort(key=lambda x: x[0])  # Ordenar por ID do filete
                        for f_id, f_bancada_id, cultura_id, cultura_nome_f, data_plant, data_colh in filetes:
                            col_f1, col_f2, col_f3 = st.columns(3)
                            with col_f1:
                                st.caption(f"**Filete #{f_id}**")
                            with col_f2:
                                st.caption(f"Cultura: {cultura_nome_f or 'N/A'}")
                            with col_f3:
                                st.caption(f"Plantio: {data_plant}")
                    else:
                        st.caption("Nenhum filete cadastrado")
                
                with col2:
                    if st.button("➕ Adicionar Filete", key=f"btn_add_filete_{bancada_id}"):
                        st.session_state[f"show_form_filete_{bancada_id}"] = True
                
                # Formulário para adicionar filete (se clicado)
                if st.session_state.get(f"show_form_filete_{bancada_id}"):
                    st.markdown("---")
                    st.markdown("**Adicionar Novo Filete a esta Bancada**")
                    
                    culturas = get_culturas()
                    cultura_dict = {c[1]: c[0] for c in culturas}
                    opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())
                    
                    col_f1, col_f2 = st.columns(2)
                    
                    with col_f1:
                        cultura_nome_novo = st.selectbox(
                            "Cultura",
                            opcoes_cultura,
                            index=0,
                            key=f"sel_cultura_filete_{bancada_id}"
                        )
                    
                    with col_f2:
                        data_plantio_novo = st.date_input(
                            "Data de Plantio",
                            value=date.today(),
                            format="DD/MM/YYYY",
                            key=f"inp_data_filete_{bancada_id}"
                        )
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("✅ Confirmar", key=f"btn_confirmar_filete_{bancada_id}"):
                            if cultura_nome_novo == "Selecione a cultura":
                                st.error("Selecione uma cultura antes de confirmar.")
                            else:
                                cultura_id = cultura_dict[cultura_nome_novo]
                                try:
                                    inserir_filete(
                                        bancada_id,
                                        cultura_id,
                                        data_plantio_novo.strftime("%Y-%m-%d")
                                    )
                                    st.success(f"✅ Filete criado com sucesso! Cultura: {cultura_nome_novo}")
                                    st.session_state[f"show_form_filete_{bancada_id}"] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao criar filete: {str(e)}")
                    
                    with col_btn2:
                        if st.button("❌ Cancelar", key=f"btn_cancelar_filete_{bancada_id}"):
                            st.session_state[f"show_form_filete_{bancada_id}"] = False
                            st.rerun()


# =========================
# TAB 2: CRIAR NOVA BANCADA
# =========================
with tab2:
    import time
    if "salvando_bancada" not in st.session_state:
        st.session_state.salvando_bancada = False
    if "nova_bancada_pendente" not in st.session_state:
        st.session_state.nova_bancada_pendente = None
    if "reset_form" not in st.session_state:
        st.session_state.reset_form = False
    if "nome_bancada_nova" not in st.session_state:
        st.session_state.nome_bancada_nova = ""
    if "cultura_primeira_bancada" not in st.session_state:
        st.session_state.cultura_primeira_bancada = 0
    if "data_primeira_bancada" not in st.session_state:
        st.session_state.data_primeira_bancada = date.today()
        
    if st.session_state.reset_form:
        st.session_state.nome_bancada_nova = ""
        st.session_state.cultura_primeira_bancada = 0
        st.session_state.data_primeira_bancada = date.today()
        st.session_state.reset_form = False

    def iniciar_salvamento_bancada():
        st.session_state.nova_bancada_pendente = {
            "nome_bancada": st.session_state.nome_bancada_nova,
            "cultura_nome": st.session_state.cultura_primeira_bancada,
            "data_inicio": st.session_state.data_primeira_bancada,
        }
        st.session_state.salvando_bancada = True
    
    st.header("Cadastrar Nova Bancada", help="Crie uma nova bancada com seu primeiro filete")
    
    st.markdown("""
    Para criar uma nova bancada, você precisa:
    1. **Nome da Bancada** - identificar sua bancada
    2. **Primeiro Filete** - cultura e data de plantio (obrigatório)
    3. **Filetes Adicionais** - podem ser adicionados depois
    """)
    
    st.markdown("---")

    bancada_em_salvamento = st.session_state.salvando_bancada
    
    with st.form("form_nova_bancada", ):
        
        # Seção 1: Dados da Bancada
        st.subheader("1️⃣ Informações da Bancada")
        nome_bancada = st.text_input(
            "Nome da Bancada",
            key="nome_bancada_nova",
            help="Ex: Bancada 1, Setor A, etc.",
            disabled=bancada_em_salvamento
        )
        
        # Seção 2: Primeiro Filete (obrigatório)
        st.subheader("2️⃣ Primeiro Filete (Obrigatório)")
        
        culturas = get_culturas()
        cultura_dict = {c[1]: c[0] for c in culturas}
        opcoes_cultura = ["Selecione a cultura"] + list(cultura_dict.keys())
        
        col1, col2 = st.columns(2)
        
        with col1:
            cultura_nome = st.selectbox(
                "Cultura",
                opcoes_cultura,
                index=0,
                key="cultura_primeira_bancada",
                help="Selecione a cultura para o primeiro filete",
                disabled=bancada_em_salvamento
            )
        
        with col2:
            data_inicio = st.date_input(
                "Data de Plantio",
                value=date.today(),
                format="DD/MM/YYYY",
                key="data_primeira_bancada",
                help="Data de início do cultivo",
                disabled=bancada_em_salvamento
            )
        
        col_submit, col_empty = st.columns([1, 4])
        
        with col_submit:
            submitted = st.form_submit_button(
                "💾 Cadastrar Bancada",
                use_container_width=True,
                disabled=bancada_em_salvamento,
                on_click=iniciar_salvamento_bancada
            )

    if st.session_state.salvando_bancada and st.session_state.nova_bancada_pendente:
        dados_bancada = st.session_state.nova_bancada_pendente
        nome_bancada = dados_bancada["nome_bancada"]
        cultura_nome = dados_bancada["cultura_nome"]
        data_inicio = dados_bancada["data_inicio"]
        
        if not nome_bancada:
            st.error("❌ Digite um nome para a bancada.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            time.sleep(5)
            

        if cultura_nome == "Selecione a cultura":
            st.error("❌ Selecione uma cultura para o primeiro filete.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            time.sleep(5)
            

        if not data_inicio:
            st.error("❌ Selecione uma data de plantio.")
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            time.sleep(5)
            

        try:
            cultura_id = cultura_dict[cultura_nome]
            bancada_id = inserir_bancada(nome_bancada)

            if bancada_id is None:
                st.error("❌ Erro ao criar a bancada. Tente novamente.")
                st.session_state.salvando_bancada = False
                st.session_state.nova_bancada_pendente = None
                time.sleep(5)

            inserir_filete(
                bancada_id,
                cultura_id,
                data_inicio.strftime("%Y-%m-%d")
            )

            st.success(f"✅ Bancada '{nome_bancada}' cadastrada com sucesso!")
            st.info(f"📌 Primeiro filete criado com cultura '{cultura_nome}' em {data_inicio.strftime('%d/%m/%Y')}")
            
            st.session_state.reset_form = True
            
            time.sleep(5)

        except Exception as e:
            st.error(f"❌ Erro ao cadastrar bancada: {str(e)}")

        finally:
            st.session_state.salvando_bancada = False
            st.session_state.nova_bancada_pendente = None
            st.rerun()
