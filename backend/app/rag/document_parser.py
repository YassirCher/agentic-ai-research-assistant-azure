import fitz  # PyMuPDF
from typing import List, Dict, Any
from io import BytesIO

def parse_pdf_from_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Parse un document PDF depuis les bytes (upload) et extrait le texte par page
    avec les métadonnées de base.
    """
    documents = []
    
    # Ouvrir le PDF depuis le flux en mémoire
    pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
    
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")
        
        # Ignorer les pages complètement vides (moins de 10 caractères utiles)
        if len(text.strip()) > 10:
            doc_dict = {
                "page_content": text,
                "metadata": {
                    "source": filename,
                    "page": page_num + 1,  # 1-indexed for users
                }
            }
            documents.append(doc_dict)
            
    pdf_document.close()
    return documents
