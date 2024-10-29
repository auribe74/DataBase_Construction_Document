from flask import Flask, render_template, request, send_from_directory
import os
from PyPDF2 import PdfReader
import docx

app = Flask(__name__)

# Ruta a la carpeta de documentos
DOCUMENTS_FOLDER = r'C:\Users\aurib\OneDrive\Documentos\Proyectos Personales\BOT AI\Application_Documents_Folder'
RESULTS_PER_PAGE = 10  # Número de resultados por página
search_history = []  # Variable global para almacenar el historial

@app.route('/')
def home():
    return render_template('index.html', history=search_history)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    page = request.args.get('page', 1, type=int)  # Página actual, por defecto la 1
    if not query:
        return render_template('index.html', message="Please enter a search term", history=search_history)

    # Guardar búsqueda en el historial si no está repetida
    if query not in search_history:
        search_history.append(query)

    # Buscar dentro del contenido de los documentos
    all_results = search_documents(query)
    total_results = len(all_results)

    # Obtener los resultados para la página actual
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    paginated_results = all_results[start:end]

    return render_template('index.html', 
                           results=paginated_results, 
                           query=query, 
                           page=page, 
                           total_results=total_results,
                           results_per_page=RESULTS_PER_PAGE,
                           history=search_history)

def search_documents(query):
    results = []
    for root, dirs, files in os.walk(DOCUMENTS_FOLDER):
        for file in files:
            # Revisamos PDFs
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                if search_pdf(pdf_path, query):
                    relative_path = os.path.relpath(pdf_path, DOCUMENTS_FOLDER)
                    full_path = os.path.abspath(pdf_path)
                    results.append({'name': file, 'path': relative_path, 'full_path': full_path})
            # Revisamos documentos Word
            elif file.endswith('.docx'):
                docx_path = os.path.join(root, file)
                if search_docx(docx_path, query):
                    relative_path = os.path.relpath(docx_path, DOCUMENTS_FOLDER)
                    full_path = os.path.abspath(docx_path)
                    results.append({'name': file, 'path': relative_path, 'full_path': full_path})
    return results

def search_pdf(pdf_path, query):
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and query.lower() in text.lower():
                return True
    except Exception as e:
        print(f"Error leyendo PDF {pdf_path}: {e}")
    return False

def search_docx(docx_path, query):
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            if query.lower() in para.text.lower():
                return True
    except Exception as e:
        print(f"Error leyendo DOCX {docx_path}: {e}")
    return False

@app.route('/download/<path:filename>')
def download(filename):
    # Sirve el archivo desde la ruta completa
    return send_from_directory(DOCUMENTS_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
