from neo4j_viz import Node, Relationship, VisualizationGraph

def visualize_ontology(data):
    ontology = data[0]["Ontology"]
    
    # 1. Create Nodes
    # We use a dictionary to map name -> ID for relationship building
    nodes = []
    label_to_id = {}
    
    for idx, label in enumerate(ontology["Labels"]):
        label_name = label["name"]
        label_to_id[label_name] = idx
        
        # We can scale size based on property count for a nice visual effect
        node_size = 10
        
        nodes.append(
            Node(id=idx, size=node_size, caption=label_name)
        )

    # 2. Create Relationships
    relationships = []
    for schema in ontology["SchemaMap"]:
        source_name = schema["start_label"]
        target_name = schema["end_label"]
        rel_type = schema["type"]
        
        # Only add if both nodes exist in our label list
        if source_name in label_to_id and target_name in label_to_id:
            relationships.append(
                Relationship(
                    source=label_to_id[source_name],
                    target=label_to_id[target_name],
                    caption=rel_type
                )
            )

    # 3. Render the Graph
    VG = VisualizationGraph(nodes=nodes, relationships=relationships)
    return(VG.render(initial_zoom=1.2))

import json
# Run the fix
def generate_save_graph(input_path, output_path):

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Execute the visualization
    html_output = visualize_ontology(data)

    with open(output_path, "w", encoding="utf-8") as f:
        # Accessing the .data attribute from the rendered object
        f.write(html_output.data)
    
    print(f"Success: Ontology visualization saved to {output_path}")  

"""
from pathlib import Path

input_dir = Path("ontologies/report_1")
files = [str(f.name) for f in input_dir.glob("*.txt")]

for i in range(0, len(files)):"""

#generate_save_graph(f"ontologies/report_10/ontology_v_5.txt", f"ontology_graphs/report_10/ontology_graph_v_5.html")