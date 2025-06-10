from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

def set_input_type(state):
    if state["input"].endswith((".pdf", ".docx", ".pptx")):
        state["input_type"] = "document"
    else:
        state["input_type"] = "text"
    return state

def route_input_type(state):
    return state["input_type"]

def parse_document(state):
    ext = Path(state['input']).suffix.lower()
    if ext == '.pdf':
        loader = PyPDFLoader(state['input'])
        docs = loader.load()
        state['parsed_text'] = "\n\n".join(doc.page_content for doc in docs)
    elif ext == '.docx':
        loader = Docx2txtLoader(state['input'])  # 추가
    else:
        raise ValueError(f"Error: unsupported file extension: {ext}")
    docs = loader.load()
    state['parsed_text'] = "\n\n".join(doc.page_content for doc in docs)
    return state