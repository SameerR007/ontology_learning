from pathlib import Path

def get_version_number(path):
    # Extracts the number from filenames like ontology_v_5.txt
    return int(path.stem.split("_")[-1])

report_dir = Path("ontologies") / f"report_1"
ontology_files = list(report_dir.glob("ontology_v_*.txt"))
print(ontology_files)
if ontology_files:
    latest_file = max(ontology_files, key=get_version_number)
    print(latest_file)
    with latest_file.open("r", encoding="utf-8") as f:
        existing_ontology = f.read()
else:
    existing_ontology = None