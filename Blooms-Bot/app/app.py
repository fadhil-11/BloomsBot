from flask import Blueprint, request, render_template
import fitz  # PyMuPDF

app = Blueprint('app', __name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_text = ""
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return "No file part", 400
        file = request.files['pdf_file']
        if file.filename == '':
            return "No selected file", 400
        if file:
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            extracted_text = ""
            for page in pdf_document:
                extracted_text += page.get_text()
            pdf_document.close()
    return render_template('index.html', extracted_text=extracted_text)