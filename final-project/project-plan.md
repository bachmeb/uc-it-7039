# final project plan

## Summary
Add on to the final project for the capstone class by creating a web app running in flask that will accept an ontology.owl file and display the classes, object properties, and datatype properties. 

## Outline
* Create local instance of flask app
* Create a homepage
* Upload OWL file to flask app
* Update flask app to display contents of OWL file
* Update flask app to edit contents of OWL file
* Update flask app to export copy of OWL file
* Update flask app to populate Jena Fuseki
* Deploy flask to EC2
* Create certificate for ALB (fuseki.brian.proximal.dev)
* Route traffic through ALB to Jena Fuseki running in EC2
* Create certificate for ALB (ontology.brian.proximal.dev)
* Route traffic through ALB to Flask app running in EC2 in private subnet
