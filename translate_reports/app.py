import os
from typing import List, TypedDict
from pathlib import Path
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from dotenv import load_dotenv
load_dotenv() 
import os

def build_graph():

    class TranslationState(TypedDict):
        original_report: str
        translated_report: str

    llm = ChatOpenAI(
        model="gpt-oss:120b",
        openai_api_key=os.environ['OLLAMA_TOKEN'], # Your personal API-Key
        openai_api_base="https://core-llmtest.med.uni-muenchen.de/ollama/v1", # Often mapped to /v1
        temperature=0
    )

    def translate_file(state: TranslationState):
        original_report = state["original_report"]
        

        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt = f.read()

        prompt = [
            SystemMessage(content=prompt),
            HumanMessage(content=original_report)
        ]
        
        response = llm.invoke(prompt)
        return {"translated_report": response.content}

    
    # Build the Graph
    workflow = StateGraph(TranslationState)
    workflow.add_node("translate", translate_file)

    # The loop back
    workflow.add_edge(START, "translate")
    workflow.add_edge("translate", END)

    return(workflow.compile())

graph=build_graph()

input_dir = Path("reports_de")
files = [str(f.name) for f in input_dir.glob("*.md")]

for i in range(2, len(files)):
    print(i)
    file_path="reports_de/"+files[i]
    
    with open(file_path, "r", encoding="utf-8") as f:
        original_report = f.read()
    
    translated_report = (graph.invoke({"original_report":original_report}))["translated_report"]

    output_dir = Path("reports_en")
    output_dir.mkdir(exist_ok=True)
  
    output_path = "reports_en/" + f"en_{files[i]}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_report)

    