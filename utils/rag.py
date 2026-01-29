from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

class SimpleRAG:
    def __init__(self, vectorstore, llm, language="Türkçe"):
        self.vectorstore = vectorstore
        self.llm = llm
        self.language = language
    
    def ask(self, question: str) -> str:
        docs = self.vectorstore.similarity_search(question, k=3)
        context = "\n\n".join(d.page_content for d in docs)
        
        if self.language == "Türkçe":
            prompt = f"""
Sen yardımsever bir asistansın. Aşağıdaki bağlamı kullanarak soruyu Türkçe olarak yanıtla.

ÖNEMLİ KURALLAR:
- Sadece düz metin kullan
- HTML etiketleri, kod blokları veya özel formatlar KULLANMA
- <div>, </div>, <p> gibi etiketler YASAK
- Cevabını doğrudan ve açık bir şekilde yaz
- Eğer cevap bağlamda yoksa, "Bu bilgi dokümanlarda bulunmuyor" de

Bağlam:
{context}

Soru:
{question}

Cevap (sadece düz Türkçe metin, HTML yok):
"""
        else:
            prompt = f"""
You are a helpful assistant. Answer the question in English using the following context.

IMPORTANT RULES:
- Use only plain text
- Do NOT use HTML tags, code blocks or special formatting
- Tags like <div>, </div>, <p> are FORBIDDEN
- Write your answer directly and clearly
- If the answer is not in the context, say "This information is not found in the documents"

Context:
{context}

Question:
{question}

Answer (plain English text only, no HTML):
"""
        
        response = self.llm.invoke(prompt).content
        
        # Agresif HTML temizleme
        response = re.sub(r'<[^>]+>', '', response)
        response = re.sub(r'&[a-z]+;', '', response)
        
        # Gereksiz boşlukları temizle
        response = re.sub(r'\s+', ' ', response)
        response = response.strip()
        
        # Türkçe karakterleri koru
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,;:!?()'-\n\t")
        allowed_chars.update("ğĞüÜşŞıİöÖçÇ")
        
        cleaned_response = ''.join(char for char in response if char in allowed_chars)
        
        return cleaned_response.strip()

def build_rag_chain(documents, language="Türkçe"):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )
    docs = splitter.split_documents(documents)
    
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )
    
    vectorstore = Chroma.from_documents(
        docs,
        embedding=embeddings
    )
    
    llm = ChatOllama(
        model="llama3.2",
        temperature=0.2
    )
    
    return SimpleRAG(vectorstore, llm, language=language)