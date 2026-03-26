from neo4j import GraphDatabase
import networkx as nx
import matplotlib.pyplot as plt

def visualize_and_save(uri, user, password, filename="graph.png"):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    G = nx.MultiDiGraph()

    with driver.session() as session:
        # Fetch nodes and relationships
        result = session.run("MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50")
        
        for record in result:
            node_a = record['n']
            node_b = record['m']
            rel = record['r']
            
            # Add nodes with labels as attributes
            G.add_node(node_a.id, label=list(node_a.labels)[0])
            G.add_node(node_b.id, label=list(node_b.labels)[0])
            # Add relationship
            G.add_edge(node_a.id, node_b.id, type=rel.type)

    # Plotting
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    # Draw nodes colored by label
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=2000, font_size=10)
    
    # Draw edge labels (the relationships)
    edge_labels = nx.get_edge_attributes(G, 'type')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    plt.savefig(filename)
    plt.show()
    driver.close()

visualize_and_save("bolt://localhost:7687", "neo4j", "test1234")