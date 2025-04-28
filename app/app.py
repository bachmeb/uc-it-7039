from flask import Flask, request, redirect, url_for, render_template, send_file
import os
from rdflib import Graph, URIRef, RDF, OWL
from urllib.parse import urljoin
import urllib3
import json


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return '''
    <html>
    <head>
        <title>Ontology Web App</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Ontology Web App</h1>
        <h2>Ontology</h2>
        <ul>    
            <li><a href="/upload">Upload OWL File</a></li>
            <li><a href="/view">View Last Uploaded OWL</a></li>
            <li><a href="/edit">Edit Class Name</a></li>
            <li><a href="/add">Add New Class</a></li>
            <li><a href="/download">Download OWL File</a></li>
        </ul>
        <h2>Jena Fuseki Database</h2>        
        <ul>    
            <li><a href="/fuseki/list">List all triples in Jena Fuseki database</a></li>
            <li><a href="/fuseki/add">Add New Class to Fuseki</a></li>
            <li><a href="/fuseki/clear">Clear all triples in Fuseki</a></li>
            <li><a href="/fuseki/load">Load Ontology File into Fuseki</a></li>
            <li><a href="/fuseki/download">Download Fuseki data as Ontology File</a></li>
            <li><a href="/fuseki/graph">Visualize the Fuseki Graph Database</a></li>
        </ul>
    </body>
    </html>
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
    <html>
    <head>
        <title>Ontology Web App</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Upload OWL File</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <a href="/">Back to Home</a>
    </body>
    </html>
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

    response = f"""
    <html>
    <head>
        <title>View Ontology</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Ontology: {filename}</h1>

        <h2>Classes</h2>
        <ul>
    """

    if classes:
        response += ''.join(f"<li>{c}</li>" for c in classes)
    else:
        response += "<li><em>None found</em></li>"

    response += "</ul>"

    response += "<h2>Object Properties</h2><ul>"
    if object_properties:
        response += ''.join(f"<li>{p}</li>" for p in object_properties)
    else:
        response += "<li><em>None found</em></li>"
    response += "</ul>"

    response += "<h2>Datatype Properties</h2><ul>"
    if datatype_properties:
        response += ''.join(f"<li>{p}</li>" for p in datatype_properties)
    else:
        response += "<li><em>None found</em></li>"
    response += "</ul>"

    response += """
        <a href="/">Back to Home</a>
    </body>
    </html>
    """

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
    response = """
    <html>
    <head>
        <title>Edit Class Names</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Edit Class Names</h1>
        <p>Click on a class to rename it:</p>
        <ul>
    """

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

    response += """
        </ul>
        <br><a href="/">Back to Home</a>
    </body>
    </html>
    """

    return response


@app.route("/add", methods=["GET", "POST"])
def add_class():
    try:
        with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "r") as f:
            filename = f.read().strip()
    except FileNotFoundError:
        return "No file uploaded yet."

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    g = Graph()
    g.parse(filepath)

    if request.method == "POST":
        new_class_localname = request.form.get("new_class")

        if not new_class_localname:
            return "New class name is required."

        # Try to infer base URI from existing classes
        ns_candidates = [str(s) for s in g.subjects(RDF.type, OWL.Class)]
        if not ns_candidates:
            return "No existing classes found to infer namespace."

        base_uri = ns_candidates[0].rsplit("#", 1)[0] + "#"
        new_class_uri = URIRef(base_uri + new_class_localname)

        # Add the triple
        g.add((new_class_uri, RDF.type, OWL.Class))

        # Save the updated graph
        g.serialize(destination=filepath, format="xml")
        return redirect(url_for('view_ontology'))

    # If GET, show form
    return '''
        <html>
    <head>
        <title>Ontology Web App</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Add New Class</h1>
        <form method="post">
            New Class Name (local part after #): 
            <input type="text" name="new_class" placeholder="NewClassName">
            <input type="submit" value="Add Class">
        </form>
        <a href="/">Back to Home</a>
    </body>
    </html>
    '''


@app.route("/fuseki/list")
def jena_list():
    fuseki_endpoint = "http://localhost:3030/ds/query"

    query = """
    SELECT ?s ?p ?o
    WHERE {
      ?s ?p ?o
    }
    LIMIT 100
    """

    http = urllib3.PoolManager()

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/sparql-results+json"
    }

    response = http.request(
        "POST",
        fuseki_endpoint,
        body=f"query={query}",
        headers=headers
    )

    if response.status != 200:
        return f"Failed to query Fuseki: {response.status} {response.data.decode('utf-8')}"

    results = json.loads(response.data.decode("utf-8"))

    # Build HTML response
    html = """
    <html>
    <head>
        <title>Ontology Web App</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
        <style>
            th {
                cursor: pointer;
                background-color: #333; /* Darker background */
                color: white;           /* White text */
                padding: 8px;
                font-size: 16px;
            }
            th.sorted-asc {
                background-color: #4CAF50; /* Green for ascending */
                color: white;
            }
            th.sorted-desc {
                background-color: #F44336; /* Red for descending */
                color: white;
            }
            td {
                padding: 8px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <h1>Triples from Fuseki /ds Dataset</h1>
        <table border='1' id="triplesTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Subject</th>
                    <th onclick="sortTable(1)">Predicate</th>
                    <th onclick="sortTable(2)">Object</th>
                </tr>
            </thead>
            <tbody>
    """

    for binding in results["results"]["bindings"]:
        s = binding["s"]["value"]
        p = binding["p"]["value"]
        o = binding["o"]["value"]
        html += f"<tr><td>{s}</td><td>{p}</td><td>{o}</td></tr>"

    html += """
            </tbody>
        </table>
        <br><a href='/'>Back to Home</a>

        <script>
            let sortDirection = {};  // Track sort direction for each column

            function sortTable(n) {
                const table = document.getElementById("triplesTable");
                let switching = true;
                let dir = sortDirection[n] === "asc" ? "desc" : "asc";
                sortDirection[n] = dir;
                let rows, i, x, y, shouldSwitch;

                while (switching) {
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (dir === "asc" && x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                        if (dir === "desc" && x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                    if (shouldSwitch) {
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                    }
                }

                // Reset all headers
                const headers = table.getElementsByTagName("TH");
                for (let j = 0; j < headers.length; j++) {
                    headers[j].classList.remove("sorted-asc", "sorted-desc");
                }
                // Highlight sorted column
                if (dir === "asc") {
                    headers[n].classList.add("sorted-asc");
                } else {
                    headers[n].classList.add("sorted-desc");
                }
            }
        </script>

    </body>
    </html>
    """

    return html



@app.route("/fuseki/add", methods=["GET", "POST"])
def jena_add_class():
    if request.method == "POST":
        new_class_localname = request.form.get("new_class")

        if not new_class_localname:
            return "New class name is required."

        # Build SPARQL INSERT query
        fuseki_endpoint = "http://localhost:3030/ds/update"

        base_uri = "http://example.org/"  # <-- You could also make this user-configurable if you want
        new_class_uri = base_uri + new_class_localname

        insert_query = f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        INSERT DATA {{
            <{new_class_uri}> a owl:Class .
        }}
        """

        http = urllib3.PoolManager()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = http.request(
            "POST",
            fuseki_endpoint,
            body=urllib3.request.urlencode({"update": insert_query}),
            headers=headers
        )

        if response.status != 200:
            return f"Failed to add class to Fuseki: {response.status} {response.data.decode('utf-8')}"

        return redirect(url_for('jena_list'))

    # If GET, show form
    return '''
    <html>
    <head>
        <title>Ontology Web App</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Add New Class to Fuseki</h1>
        <form method="post">
            New Class Name (local part after base URI): 
            <input type="text" name="new_class" placeholder="NewClassName">
            <input type="submit" value="Add Class">
        </form>
        <a href="/">Back to Home</a>
    </body>
    </html>
    '''


@app.route("/fuseki/clear", methods=["GET", "POST"])
def jena_clear_dataset():
    if request.method == "POST":
        fuseki_endpoint = "http://localhost:3030/ds/update"

        delete_query = """
        DELETE WHERE { ?s ?p ?o }
        """

        http = urllib3.PoolManager()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = http.request(
            "POST",
            fuseki_endpoint,
            body=urllib3.request.urlencode({"update": delete_query}),
            headers=headers
        )

        if response.status != 200:
            return f"Failed to clear dataset: {response.status} {response.data.decode('utf-8')}"

        return redirect(url_for('jena_list'))

    # If GET, show a confirmation form
    return '''
    <html>
    <head>
        <title>Clear Dataset</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Clear All Triples in Fuseki Dataset</h1>
        <form method="post">
            <p style="color: red;">Warning: This will delete <strong>everything</strong> in the dataset!</p>
            <input type="submit" value="Confirm Clear">
        </form>
        <a href="/">Back to Home</a>
    </body>
    </html>
    '''


@app.route("/fuseki/load", methods=["GET", "POST"])
def jena_load_ontology():
    if request.method == "POST":
        try:
            with open(os.path.join(UPLOAD_FOLDER, "last_uploaded.txt"), "r") as f:
                filename = f.read().strip()
        except FileNotFoundError:
            return "No file uploaded yet."

        filepath = os.path.join(UPLOAD_FOLDER, filename)
        g = Graph()
        g.parse(filepath)

        # Serialize to N-Triples format (easier for SPARQL UPDATE)
        data = g.serialize(format="nt")

        fuseki_endpoint = "http://localhost:3030/ds/update"

        insert_query = "INSERT DATA { " + data + " }"

        http = urllib3.PoolManager()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = http.request(
            "POST",
            fuseki_endpoint,
            body=urllib3.request.urlencode({"update": insert_query}),
            headers=headers
        )

        if response.status != 200:
            return f"Failed to load ontology into Fuseki: {response.status} {response.data.decode('utf-8')}"

        return redirect(url_for('jena_list'))

    # If GET, show a confirmation form
    return '''
    <html>
    <head>
        <title>Load Ontology to Fuseki</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css">
    </head>
    <body>
        <h1>Load Ontology into Jena Fuseki</h1>
        <form method="post">
            <p style="color: green;">This will load the last uploaded OWL file into Fuseki.</p>
            <input type="submit" value="Load Ontology">
        </form>
        <a href="/">Back to Home</a>
    </body>
    </html>
    '''

@app.route("/fuseki/download")
def jena_download_ontology():
    fuseki_endpoint = "http://localhost:3030/ds/query"

    construct_query = """
    CONSTRUCT { ?s ?p ?o }
    WHERE { ?s ?p ?o }
    """

    http = urllib3.PoolManager()

    headers = {
        "Accept": "application/rdf+xml",  # OWL/RDF XML format
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = http.request(
        "POST",
        fuseki_endpoint,
        body=urllib3.request.urlencode({"query": construct_query}),
        headers=headers
    )

    if response.status != 200:
        return f"Failed to fetch ontology from Fuseki: {response.status} {response.data.decode('utf-8')}"

    # Save the ontology to a temporary file
    output_path = os.path.join(UPLOAD_FOLDER, "fuseki_export.owl")
    with open(output_path, "wb") as f:
        f.write(response.data)

    return send_file(output_path, as_attachment=True, download_name="ontology.owl")


@app.route("/fuseki/graph")
def jena_graph():
    fuseki_endpoint = "http://localhost:3030/ds/query"

    query = """
    SELECT ?s ?p ?o
    WHERE {
      ?s ?p ?o
    }
    LIMIT 100
    """

    http = urllib3.PoolManager()

    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = http.request(
        "POST",
        fuseki_endpoint,
        body=urllib3.request.urlencode({"query": query}),
        headers=headers
    )

    if response.status != 200:
        return f"Failed to query Fuseki: {response.status} {response.data.decode('utf-8')}"

    results = json.loads(response.data.decode("utf-8"))

    nodes = {}
    edges = []

    for binding in results["results"]["bindings"]:
        s = binding["s"]["value"]
        p = binding["p"]["value"]
        o = binding["o"]["value"]

        # Add subject and object nodes if not already present
        if s not in nodes:
            nodes[s] = {"id": s, "label": s}
        if o not in nodes:
            nodes[o] = {"id": o, "label": o}

        # Add edge
        edges.append({"from": s, "to": o, "label": p})

    # Build the HTML
    html = """
    <html>
    <head>
        <title>Graph Visualization</title>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
        <style>
            #mynetwork {
                width: 100%;
                height: 800px;
                border: 1px solid lightgray;
            }
        </style>
    </head>
    <body>
        <h1>Graph Visualization</h1>
        <div id="mynetwork"></div>
        <script type="text/javascript">
            var nodes = new vis.DataSet(""" + json.dumps(list(nodes.values())) + """);
            var edges = new vis.DataSet(""" + json.dumps(edges) + """);

            var container = document.getElementById('mynetwork');
            var data = {
                nodes: nodes,
                edges: edges
            };
            var options = {
                nodes: {
                    shape: 'dot',
                    size: 20,
                    font: { size: 14, color: 'black' }
                },
                edges: {
                    arrows: { to: { enabled: true } },
                    font: { align: 'middle', size: 10 }
                },
                physics: {
                    enabled: true,
                    barnesHut: {
                        gravitationalConstant: -30000,
                        springLength: 100
                    }
                }
            };
            var network = new vis.Network(container, data, options);
        </script>
        <br><a href="/">Back to Home</a>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
