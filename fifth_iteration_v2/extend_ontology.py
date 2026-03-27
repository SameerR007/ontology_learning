import json

def merge_properties(existing_props, new_props):
    """Merges two lists of properties, preventing duplicate keys."""
    if not existing_props:
        existing_props = []
    
    # Create a dictionary of existing properties for quick lookup by key
    existing_dict = {prop["key"]: prop for prop in existing_props}
    
    for prop in new_props:
        # Only add the property if the key doesn't already exist
        if prop["key"] not in existing_dict:
            existing_props.append(prop)
            
    return existing_props

def update_ontology(existing_data, diff_data, output_file_path):
    """Merges a diff ontology JSON into an existing ontology JSON."""
    

    existing_ontology = existing_data[0]["Ontology"]
    
    # Catch if the entire diff_data is just an empty list []
    if not diff_data:
        diff_data = [
            {
                "Ontology": {
                    "Labels": [],
                    "RelationshipTypes": [],
                    "SchemaMap": []
                }
            }
        ]
    
    diff_ontology = diff_data[0]["Ontology"]

    # ==========================================
    # 2. Merge Labels (Explicit Index Method)
    # ==========================================

    for new_label in diff_ontology.get("Labels", []):
        name = new_label["name"]
        label_found = False
        
        # Search the existing list for a match
        for i, existing_label in enumerate(existing_ontology["Labels"]):
            if existing_label["name"] == name:
                # Merge the properties and explicitly assign back to the list index
                merged_props = merge_properties(
                    existing_label.get("properties", []), 
                    new_label.get("properties", [])
                )
                existing_ontology["Labels"][i]["properties"] = merged_props
                label_found = True
                break # Stop searching once found
                
        # If not found after searching the whole list, append as new
        if not label_found:
            existing_ontology["Labels"].append(new_label)

    # ==========================================
    # 3. Merge RelationshipTypes (Explicit Index Method)
    # ==========================================

    for new_rel in diff_ontology.get("RelationshipTypes", []):
        name = new_rel["name"]
        rel_found = False
        
        # Search the existing list for a match
        for i, existing_rel in enumerate(existing_ontology["RelationshipTypes"]):
            if existing_rel["name"] == name:
                # Merge the properties and explicitly assign back to the list index
                merged_props = merge_properties(
                    existing_rel.get("properties", []), 
                    new_rel.get("properties", [])
                )
                existing_ontology["RelationshipTypes"][i]["properties"] = merged_props
                rel_found = True
                break # Stop searching once found
                
        # If not found after searching the whole list, append as new
        if not rel_found:
            existing_ontology["RelationshipTypes"].append(new_rel)

    # ==========================================
    # 4. Merge SchemaMap
    # ==========================================

    for new_schema in diff_ontology.get("SchemaMap", []):
        # Prevent duplicate mappings (A -> B -> C)
        if new_schema not in existing_ontology["SchemaMap"]:
            existing_ontology["SchemaMap"].append(new_schema)

    # ==========================================
    # 5. Save and Output
    # ==========================================
    text_output = json.dumps(existing_data, indent=4, ensure_ascii=False)
    
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(text_output)
    
    print(f"Successfully merged updates! Saved to {output_file_path}")

# ==========================================
# Execution Block
# ==========================================
if __name__ == "__main__":
    # Example usage: Uncomment and replace with your actual file names to run
    # update_ontology('existing_ontology.json', 'diff_ontology.json', 'updated_ontology.json')
    pass