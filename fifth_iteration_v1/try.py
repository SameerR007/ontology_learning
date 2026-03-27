
import json

with open(f"ontologies/report_10/ontology_v_10.txt", "r", encoding="utf-8") as f:
    existing_ontology = f.read()

existing_ontology = json.loads(existing_ontology)

existing_ontology = existing_ontology[0]["Ontology"]

print(f"No. of labels = {len(existing_ontology['Labels'])}")
print(f"No. of relationships = {len(existing_ontology['RelationshipTypes'])}")
print(f"No. of triplets = {len(existing_ontology['SchemaMap'])}")