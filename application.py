from flask import Flask, render_template, request, send_from_directory
import os
from PyPDF2 import PdfReader
import docx
import time

app = Flask(__name__)

# Ruta a la carpeta de documentos
DOCUMENTS_FOLDER = os.path.join(os.getcwd(), 'static', 'documents')
RESULTS_PER_PAGE = 10  # Número de resultados por página
search_history = []  # Variable global para almacenar el historial

@app.route('/')
def home():
    return render_template('index.html', history=search_history)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    file_type = request.args.get('file_type', 'all')  # PDF, Word, o All
    date_filter = request.args.get('date_filter', 'all')  # Últimos 7 días, 30 días, o todos
    page = request.args.get('page', 1, type=int)  # Página actual, por defecto la 1

    if not query:
        return render_template('index.html', message="Please enter a search term", history=search_history)

    # Guardar búsqueda en el historial si no está repetida
    if query not in search_history:
        search_history.append(query)

    # Buscar dentro del contenido de los documentos
    all_results = search_documents(query, file_type, date_filter)
    total_results = len(all_results)

    # Ordenar resultados alfabéticamente por el nombre del archivo
    all_results.sort(key=lambda x: x['name'])

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

def search_documents(query, file_type, date_filter):
    results = []
    current_time = time.time()

    # Filtrar por fecha (últimos 7 días o 30 días)
    def file_recent(file_path, days):
        file_mtime = os.path.getmtime(file_path)
        return (current_time - file_mtime) <= (days * 86400)  # Convertir días a segundos

    for root, dirs, files in os.walk(DOCUMENTS_FOLDER):
        for file in files:
            # Filtrar por tipo de archivo
            if file_type == 'pdf' and not file.endswith('.pdf'):
                continue
            if file_type == 'word' and not file.endswith('.docx'):
                continue

            file_path = os.path.join(root, file)

            # Filtrar por fecha de modificación
            if date_filter == '7days' and not file_recent(file_path, 7):
                continue
            if date_filter == '30days' and not file_recent(file_path, 30):
                continue

            # Revisamos PDFs
            if file.endswith('.pdf'):
                if search_pdf(file_path, query):
                    relative_path = os.path.relpath(file_path, DOCUMENTS_FOLDER)
                    full_path = os.path.abspath(file_path)
                    results.append({'name': file, 'path': relative_path, 'full_path': full_path})
            # Revisamos documentos Word
            elif file.endswith('.docx'):
                if search_docx(file_path, query):
                    relative_path = os.path.relpath(file_path, DOCUMENTS_FOLDER)
                    full_path = os.path.abspath(file_path)
                    results.append({'name': file, 'path': relative_path, 'full_path': full_path})
    return results

def search_pdf(pdf_path, query):
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text and match_query(text, query):
                return True
    except Exception as e:
        print(f"Error leyendo PDF {pdf_path}: {e}")
    return False

def search_docx(docx_path, query):
    try:
        doc = docx.Document(docx_path)
        for para in doc.paragraphs:
            if match_query(para.text, query):
                return True
    except Exception as e:
        print(f"Error leyendo DOCX {docx_path}: {e}")
    return False

def match_query(text, query):
    # Permite búsqueda de frases exactas
    if '"' in query:
        phrase = query.strip('"')
        return phrase.lower() in text.lower()
    # Revisar si el query incluye operadores AND o OR
    if 'AND' in query:
        terms = [term.strip() for term in query.split('AND')]
        return all(term.lower() in text.lower() for term in terms)
    elif 'OR' in query:
        terms = [term.strip() for term in query.split('OR')]
        return any(term.lower() in text.lower() for term in terms)
    else:
        # Búsqueda simple
        return query.lower() in text.lower()

@app.route('/download/<path:filename>')
def download(filename):
    # Sirve el archivo desde la ruta completa
    return send_from_directory(DOCUMENTS_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    # En Render, usamos la variable de entorno PORT para el puerto dinámico
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
