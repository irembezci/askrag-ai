import streamlit as st
import tempfile
import os
from utils.loader import load_documents
from utils.rag import build_rag_chain

st.set_page_config(page_title="AskRAG", layout="wide")

if "chain" not in st.session_state:
    st.session_state.chain = None
    st.session_state.chat_history = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "language" not in st.session_state:
    st.session_state.language = "Türkçe"

# Custom CSS
st.markdown("""
<style>
    /* Sohbet mesajları için özel stiller */
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* Kullanıcı mesajı */
    [data-testid="stChatMessageContent"] {
        background-color: transparent;
    }
    
    /* Container stil */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

left, right = st.columns([1, 2])

# ---------- LEFT PANEL ----------
with left:
    st.markdown("## 📄 AskRAG")
    
    language = st.radio(
        "Dil / Language",
        ["Türkçe", "English"],
        horizontal=True,
        index=0 if st.session_state.language == "Türkçe" else 1
    )
    
    # Dil değiştiğinde chain'i sıfırla
    if language != st.session_state.language:
        st.session_state.language = language
        if st.session_state.chain is not None:
            st.session_state.chain = None
            st.session_state.chat_history = []
            st.info("Dil değiştirildi. Lütfen dokümanları yeniden yükleyin." if language == "Türkçe" else "Language changed. Please upload documents again.")
    
    subtitle = "Dokümanlarınızla sohbet edin" if st.session_state.language == "Türkçe" else "Chat with your documents"
    st.markdown(subtitle)
    
    st.markdown("---")
    
    upload_label = "Dosya Yükle (PDF, DOCX, TXT)" if st.session_state.language == "Türkçe" else "Upload Files (PDF, DOCX, TXT)"
    uploaded_files = st.file_uploader(
        upload_label,
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )
    
    if uploaded_files and st.session_state.chain is None:
        spinner_text = "Dokümanlar işleniyor..." if st.session_state.language == "Türkçe" else "Processing documents..."
        with st.spinner(spinner_text):
            try:
                all_docs = []
                for f in uploaded_files:
                    suffix = os.path.splitext(f.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(f.read())
                        tmp_path = tmp.name
                    
                    try:
                        docs = load_documents(tmp_path)
                        all_docs.extend(docs)
                        success_msg = f"✅ {f.name} yüklendi" if st.session_state.language == "Türkçe" else f"✅ {f.name} uploaded"
                        st.info(success_msg)
                    except Exception as e:
                        error_msg = f"❌ {f.name} yüklenemedi: {str(e)}" if st.session_state.language == "Türkçe" else f"❌ {f.name} upload failed: {str(e)}"
                        st.error(error_msg)
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                
                if all_docs:
                    st.session_state.chain = build_rag_chain(all_docs, language=st.session_state.language)
                    success_msg = f"🎉 {len(all_docs)} doküman hazır!" if st.session_state.language == "Türkçe" else f"🎉 {len(all_docs)} documents ready!"
                    st.success(success_msg)
                else:
                    warning_msg = "Hiçbir doküman yüklenemedi." if st.session_state.language == "Türkçe" else "No documents could be uploaded."
                    st.warning(warning_msg)
                    
            except Exception as e:
                error_msg = f"Genel hata: {str(e)}" if st.session_state.language == "Türkçe" else f"General error: {str(e)}"
                st.error(error_msg)
                import traceback
                st.error(traceback.format_exc())

# ---------- RIGHT PANEL ----------
with right:
    chat_title = "## 💬 Sohbet Alanı" if st.session_state.language == "Türkçe" else "## 💬 Chat Area"
    st.markdown(chat_title)
    
    # Sohbet container'ı
    chat_container = st.container(height=500)
    
    with chat_container:
        if len(st.session_state.chat_history) == 0:
            empty_msg = "💬 Henüz mesaj yok. Aşağıdan soru sorun!" if st.session_state.language == "Türkçe" else "💬 No messages yet. Ask a question below!"
            st.info(empty_msg)
        else:
            for user, bot in st.session_state.chat_history:
                # Kullanıcı mesajı
                with st.chat_message("user", avatar="👤"):
                    st.write(user)
                
                # Asistan mesajı
                if bot in ["⏳ Asistan düşünüyor...", "⏳ Assistant thinking..."]:
                    with st.chat_message("assistant", avatar="⏳"):
                        st.write(bot)
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(bot)
    
    st.markdown("---")
    
    # Form ile mesaj gönderme
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        placeholder = "Sorunuzu yazın..." if st.session_state.language == "Türkçe" else "Type your question..."
        button_text = "Gönder" if st.session_state.language == "Türkçe" else "Send"
        
        with col1:
            user_input = st.text_input(
                "Sorunuzu yazın", 
                key="user_input", 
                label_visibility="collapsed", 
                placeholder=placeholder
            )
        with col2:
            send_btn = st.form_submit_button(button_text, use_container_width=True)
    
    # Temizle butonu
    clear_text = "🗑️ Sohbeti Temizle" if st.session_state.language == "Türkçe" else "🗑️ Clear Chat"
    clear_btn = st.button(clear_text, use_container_width=True)
    
    # Mesaj gönderme
    if send_btn and user_input and st.session_state.chain and not st.session_state.processing:
        st.session_state.processing = True
        thinking_msg = "⏳ Asistan düşünüyor..." if st.session_state.language == "Türkçe" else "⏳ Assistant thinking..."
        st.session_state.chat_history.append((user_input, thinking_msg))
        st.rerun()
    
    # Cevap alma
    if st.session_state.processing and len(st.session_state.chat_history) > 0:
        last_user, last_bot = st.session_state.chat_history[-1]
        if last_bot in ["⏳ Asistan düşünüyor...", "⏳ Assistant thinking..."]:
            try:
                response = st.session_state.chain.ask(last_user)
                st.session_state.chat_history[-1] = (last_user, response)
                st.session_state.processing = False
                st.rerun()
            except Exception as e:
                error_msg = f"❌ Hata: {str(e)}" if st.session_state.language == "Türkçe" else f"❌ Error: {str(e)}"
                st.session_state.chat_history[-1] = (last_user, error_msg)
                st.session_state.processing = False
                st.rerun()
    
    # Temizleme
    if clear_btn:
        st.session_state.chat_history = []
        st.session_state.processing = False
        st.rerun()