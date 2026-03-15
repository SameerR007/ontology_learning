import pandas as pd
import os
import operator
from typing import List, TypedDict, Annotated
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Updated Pydantic Models ---
class Triplet(BaseModel):
    subject: str = Field(description="The source entity class")
    relationship: str = Field(description="The relationship verb")
    object: str = Field(description="The target entity class")
    source_sentence: str = Field(description="The exact sentence from the text containing this triplet")

class FullOntology(BaseModel):
    entity_classes: List[str] = Field(description="List of all unique entity classes")
    relationships: List[str] = Field(description="List of all unique relationship types")
    triplets: List[Triplet] = Field(description="List of subject-relationship-object-sentence objects")

# --- State Definition ---
class SectionState(TypedDict):
    text: str
    extracted_options: Annotated[List[str], operator.add] 
    winning_response: str
    final_ontology: FullOntology # Stores the full structured object

# --- Nodes ---
# (Nodes model_1, model_2, and grader remain largely the same, 
# just ensure your prompts ask for all fields)

def extract_with_model_1(state):
    llm = ChatGoogleGenerativeAI(model="gemma-3-4b-it")
    # Your prompt should ask for a full ontology breakdown
    with open(os.path.join(BASE_DIR, "ontology_prompts/extract_ontology.txt"), "r", encoding="utf-8") as f:
        prompt = f.read()
    result = llm.invoke(prompt.format(text=state['text']))
    return {"extracted_options": [result.content]}

def extract_with_model_2(state):
    llm = ChatGoogleGenerativeAI(model="gemma-3-4b-it")
    with open(os.path.join(BASE_DIR, "ontology_prompts/extract_ontology.txt"), "r", encoding="utf-8") as f:
        prompt = f.read()
    result = llm.invoke(prompt.format(text=state['text']))
    return {"extracted_options": [result.content]}

def grade_candidates(state):
    llm = ChatGoogleGenerativeAI(model="gemma-3-27b-it")
    candidate_1 = state["extracted_options"][0]
    candidate_2 = state["extracted_options"][1]
    with open(os.path.join(BASE_DIR, "ontology_prompts/grade_ontology.txt"), "r", encoding="utf-8") as f:
        prompt = f.read() 
    response = llm.invoke(prompt.format(candidate_1=candidate_1, candidate_2=candidate_2))
    return {"winning_response": response.content}

def format_ontology(state):
    """Schema Node: Forces the winning text into the Pydantic model using the original text as reference."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    structured_llm = llm.with_structured_output(FullOntology)
    
    with open(os.path.join(BASE_DIR, "ontology_prompts/format_ontology.txt"), "r", encoding="utf-8") as f:
        prompt_template = f.read() 
    
    # CRITICAL CHANGE: We pass the original text so the LLM can 
    # extract the exact "source_sentence" for each triplet.
    result = structured_llm.invoke(
        prompt_template.format(
            winning_ontology=state["winning_response"],
            original_text=state["text"]
        )
    )
    return {"final_ontology": result}


# --- Graph Construction ---
def build_graph():
    builder = StateGraph(SectionState)
    builder.add_node("model_1", extract_with_model_1)
    builder.add_node("model_2", extract_with_model_2)
    builder.add_node("grader", grade_candidates)
    builder.add_node("formatter", format_ontology)
    
    builder.add_edge(START, "model_1")
    builder.add_edge(START, "model_2")
    builder.add_edge("model_1", "grader")
    builder.add_edge("model_2", "grader")
    builder.add_edge("grader", "formatter")
    builder.add_edge("formatter", END)
    
    return builder.compile()

# --- CSV Processing Logic -
def process_csv(input_csv, output_csv):
    # Load the data
    df = pd.read_csv(input_csv)
    graph = build_graph()
    
    # Initialize the columns with empty strings to avoid 'SettingWithCopy' warnings
    new_cols = ['Predicted_Entity_Classes', 'Predicted_Relationships', 'Predicted_Triplets', 'Predicted_Source_Sentences']
    for col in new_cols:
        if col not in df.columns:
            df[col] = ""

    # Using range(len(df)) is fine, but we must use .at to update the dataframe
    for i in range(0, len(df)):
        print(f"Processing row {i + 1}/{len(df)}...")
        
    
        # 1. Run the graph logic
        # Use .at[i, 'column'] to get the input text
        report_text = df.at[i, 'Input_Text']
        result = graph.invoke({"text": report_text, "extracted_options": []})
        ont = result["final_ontology"]
        
        # 2. Format the outputs
        entity_classes_str = " | ".join(ont.entity_classes)
        rels_str = " | ".join(ont.relationships)
        
        trip_list = [f"({t.subject}, {t.relationship}, {t.object})" for t in ont.triplets]
        triplets_str = " | ".join(trip_list)
        
        # Use dict.fromkeys to keep unique sentences while preserving order
        src_list = [t.source_sentence for t in ont.triplets]
        sources_str = " | ".join(src_list)
        
        # 3. Save directly back to the dataframe at the current index
        df.at[i, 'Predicted_Entity_Classes'] = entity_classes_str
        df.at[i, 'Predicted_Relationships'] = rels_str
        df.at[i, 'Predicted_Triplets'] = triplets_str
        df.at[i, 'Predicted_Source_Sentences'] = sources_str


    # Final save
    df.to_csv(output_csv, index=False)
    print(f"Finished! Total processed: {len(df)}. Saved to {output_csv}")

if __name__ == "__main__":
    process_csv("ontology_data.csv", "ontology_data.csv")
