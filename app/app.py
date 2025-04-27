from flask import Flask, request, redirect, url_for, render_template, send_file
import os
from rdflib import Graph

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return '''
    <h1>Ontology Web App</h1>
    <ul>
        <li><a href="/upload">Upload OWL File</a></li>
        <li><a href="/view">View Last Uploaded OWL</a></li>
    </ul>
    '''

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            # Save the last uploaded filename
            with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "w") as f:
                f.write(file.filename)
            return redirect(url_for('view_ontology'))
    return '''
    <h1>Upload OWL File</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <a href="/">Back to Home</a>
    '''

from rdflib import RDF, RDFS, OWL

@app.route("/view")
def view_ontology():
    try:
        with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "r") as f:
            filename = f.read().strip()
    except FileNotFoundError:
        return "No file uploaded yet."

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    g = Graph()
    g.parse(filepath)

    # Now search correctly for RDF types
    classes = sorted(set(str(s) for s in g.subjects(RDF.type, OWL.Class)))
    object_properties = sorted(set(str(s) for s in g.subjects(RDF.type, OWL.ObjectProperty)))
    datatype_properties = sorted(set(str(s) for s in g.subjects(RDF.type, OWL.DatatypeProperty)))

    response = f"<h1>Ontology: {filename}</h1>"

    response += "<h2>Classes</h2><ul>"
    response += ''.join(f"<li>{c}</li>" for c in classes) or "<li><em>None found</em></li>"
    response += "</ul>"

    response += "<h2>Object Properties</h2><ul>"
    response += ''.join(f"<li>{p}</li>" for p in object_properties) or "<li><em>None found</em></li>"
    response += "</ul>"

    response += "<h2>Datatype Properties</h2><ul>"
    response += ''.join(f"<li>{p}</li>" for p in datatype_properties) or "<li><em>None found</em></li>"
    response += "</ul>"

    response += f'<br><a href="/download">Download OWL File</a><br>'
    response += f'<a href="/">Back to Home</a>'
    return response


@app.route("/download")
def download_file():
    try:
        with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "r") as f:
            filename = f.read().strip()
    except FileNotFoundError:
        return "No file uploaded yet."

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(filepath, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
