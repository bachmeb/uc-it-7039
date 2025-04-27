from flask import Flask, request, redirect, url_for, render_template, send_file
import os
from rdflib import Graph, URIRef, RDF, OWL
from urllib.parse import urljoin

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
        <li><a href="/edit">Edit Class Name</a></li>
    </ul>
    '''

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
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

@app.route("/edit", methods=["GET", "POST"])
def edit_class():
    try:
        with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "r") as f:
            filename = f.read().strip()
    except FileNotFoundError:
        return "No file uploaded yet."

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    g = Graph()
    g.parse(filepath)

    classes = sorted(set(str(s) for s in g.subjects(RDF.type, OWL.Class)))

    if request.method == "POST":
        old_uri = request.form.get("old_uri")
        new_localname = request.form.get("new_name")

        if not old_uri or not new_localname:
            return "Both old URI and new local name are required."

        base_uri = old_uri.rsplit("#", 1)[0] + "#"
        new_uri = URIRef(base_uri + new_localname)

        # Prepare updates
        triples_to_add = []
        triples_to_remove = []

        for s, p, o in g.triples((URIRef(old_uri), None, None)):
            triples_to_remove.append((s, p, o))
            triples_to_add.append((new_uri, p, o))

        for s, p, o in g.triples((None, None, URIRef(old_uri))):
            triples_to_remove.append((s, p, o))
            triples_to_add.append((s, p, new_uri))

        for triple in triples_to_remove:
            g.remove(triple)
        for triple in triples_to_add:
            g.add(triple)

        g.serialize(destination=filepath, format="xml")
        return redirect(url_for('view_ontology'))

    # GET request — show editable list of classes
    response = "<h1>Edit Class Names</h1>"
    response += "<p>Click on a class to rename it:</p><ul>"
    for c in classes:
        response += f'''
        <li>
            {c}
            <form method="post" style="display:inline;">
                <input type="hidden" name="old_uri" value="{c}">
                New name (local part): 
                <input type="text" name="new_name" placeholder="NewClassName">
                <input type="submit" value="Rename">
            </form>
        </li>
        '''
    response += "</ul>"
    response += '<br><a href="/">Back to Home</a>'
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
