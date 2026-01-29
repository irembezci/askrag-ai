from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)

def load_documents(path):
    if path.endswith(".pdf"):
        loader = PyPDFLoader(path)
    elif path.endswith(".docx"):
        loader = Docx2txtLoader(path)
    else:
        # TextLoader için encoding belirt
        try:
            loader = TextLoader(path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                loader = TextLoader(path, encoding='latin-1')
            except UnicodeDecodeError:
                loader = TextLoader(path, encoding='cp1254')  # Türkçe karakterler için
    
    return loader.load()