import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize model
model = SentenceTransformer('all-MiniLM-L6-v2')

def calculate_metrics(csv_path, similarity_threshold=0.75):
    df = pd.read_csv(csv_path)
    
    # --- Helper Functions ---
    
    def parse_list(val):
        """Parses 'A | B | C' into a list of strings."""
        if pd.isna(val) or str(val).strip() == "": return []
        return [item.strip() for item in str(val).split('|')]

    def get_semantic_matches(gt_items, pr_items, threshold):
        """
        Computes semantic recall and returns matched pairs.
        Returns: 
            recall (float), 
            matches (list of tuples): [(gt_item_str, pr_item_str), ...]
        """
        if not gt_items: return 0.0, []
        if not pr_items: return 0.0, []

        # Encode both lists
        gt_embeddings = model.encode(gt_items)
        pr_embeddings = model.encode(pr_items)

        # Compute Cosine Similarity (Rows: GT, Cols: PR)
        similarity_matrix = cosine_similarity(gt_embeddings, pr_embeddings)

        matched_pairs = []
        gt_matched_indices = set()
        
        # Greedy matching: For each GT item, find best PR match
        for i, gt_item in enumerate(gt_items):
            best_pr_idx = np.argmax(similarity_matrix[i])
            best_score = similarity_matrix[i][best_pr_idx]
            
            if best_score >= threshold:
                gt_matched_indices.add(i)
                matched_pairs.append((gt_item, pr_items[best_pr_idx]))

        recall = len(gt_matched_indices) / len(gt_items)
        return recall, matched_pairs

    def map_triplets_to_source_dict(triplet_str, source_str):
        if pd.isna(triplet_str) or pd.isna(source_str): return {}
        
        trips = parse_list(triplet_str)
        srcs = parse_list(source_str)
        
        mapping = {}
        for i in range(min(len(trips), len(srcs))):
            mapping[trips[i]] = srcs[i]
        return mapping
    
    def format_pairs(pairs):
        """Helper to format list of tuples into a readable string."""
        if not pairs: return ""
        return " | ".join([f"(GT: {gt} -> PR: {pr})" for gt, pr in pairs])

    # --- Main Loop ---
    
    # Define metric columns and new columns for matched pairs
    metrics = ["Entity_Classes_Accuracy", "Relationships_Accuracy", "Triplets_Accuracy", "Position_Accuracy"]
    pair_cols = ["Matched_Entity_Pairs", "Matched_Relationship_Pairs", "Matched_Triplet_Pairs"]
    
    for col in metrics:
        df[col] = 0.0
    for col in pair_cols:
        df[col] = ""

    print(f"Processing {len(df)} rows with Semantic Matching (Threshold: {similarity_threshold})...")

    for i in range(len(df)):
        # 1. Parse Lists
        gt_entities = parse_list(df.at[i, 'Entity_Classes'])
        pr_entities = parse_list(df.at[i, 'Predicted_Entity_Classes'])
        
        gt_rels = parse_list(df.at[i, 'Relationships'])
        pr_rels = parse_list(df.at[i, 'Predicted_Relationships'])
        
        gt_triplets = parse_list(df.at[i, 'Triplets'])
        pr_triplets = parse_list(df.at[i, 'Predicted_Triplets'])

        # 2. Semantic Matching & Storage
        
        # Entities
        ent_acc, ent_pairs = get_semantic_matches(gt_entities, pr_entities, threshold=similarity_threshold)
        df.at[i, "Entity_Classes_Accuracy"] = ent_acc
        df.at[i, "Matched_Entity_Pairs"] = format_pairs(ent_pairs)
        
        # Relationships
        rel_acc, rel_pairs = get_semantic_matches(gt_rels, pr_rels, threshold=similarity_threshold)
        df.at[i, 'Relationships_Accuracy'] = rel_acc
        df.at[i, "Matched_Relationship_Pairs"] = format_pairs(rel_pairs)

        # Triplets
        trip_acc, trip_pairs = get_semantic_matches(gt_triplets, pr_triplets, threshold=similarity_threshold)
        df.at[i, 'Triplets_Accuracy'] = trip_acc
        df.at[i, "Matched_Triplet_Pairs"] = format_pairs(trip_pairs)

        # 4. Position Accuracy
        if len(trip_pairs) > 0:
            gt_map = map_triplets_to_source_dict(df.at[i, 'Triplets'], df.at[i, 'Source_Sentences'])
            pr_map = map_triplets_to_source_dict(df.at[i, 'Predicted_Triplets'], df.at[i, 'Predicted_Source_Sentences'])
            
            location_matches = 0
            valid_comparisons = 0

            for gt_trip, pr_trip in trip_pairs:
                gt_src = gt_map.get(gt_trip)
                pr_src = pr_map.get(pr_trip)

                if gt_src and pr_src:
                    valid_comparisons += 1
                    # Strict string match on source sentence
                    if gt_src.strip().lower() == pr_src.strip().lower():
                        location_matches += 1
            
            if valid_comparisons > 0:
                df.at[i, 'Position_Accuracy'] = location_matches / valid_comparisons
            else:
                df.at[i, 'Position_Accuracy'] = 0.0
        else:
            df.at[i, 'Position_Accuracy'] = np.nan

    df.to_csv(csv_path, index=False)
    print(f"Finished! Total processed: {len(df)}. Saved to {csv_path}")

# Run
calculate_metrics("ontology_data.csv")