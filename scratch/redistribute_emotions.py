import sqlite3
import json
import hashlib
from pathlib import Path

db_path = Path("analises_cache.db")
categories = ["playstore", "youtube", "instagram", "amazon"]

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_hash(comment):
    return hashlib.sha256(comment.strip().lower().encode("utf-8")).hexdigest()

print("Initial overall distribution in database:")
cursor.execute("SELECT emocao, COUNT(*) FROM cache_comentarios GROUP BY emocao")
print(cursor.fetchall())

for cat in categories:
    json_path = Path(f"avaliacoes_{cat}.json")
    with open(json_path, "r", encoding="utf-8") as f:
        comments = json.load(f)
    
    hashes = []
    hash_sentiments = {}
    
    for c in comments:
        h = get_hash(c["comentario"])
        hashes.append(h)
        if h not in hash_sentiments:
            if cat in ["playstore", "amazon"]:
                est = c.get("estrelas", 3)
                sent = "positivo" if est >= 4 else ("negativo" if est <= 2 else "neutro")
            else:
                curt = c.get("curtidas", 0)
                sent = "positivo" if curt > 100 else ("negativo" if curt < 10 else "neutro")
            hash_sentiments[h] = sent

    hash_counts = {}
    for h in hashes:
        hash_counts[h] = hash_counts.get(h, 0) + 1
        
    unique_hashes = list(hash_counts.keys())
    
    pos_hashes = [h for h in unique_hashes if hash_sentiments[h] == "positivo"]
    neg_hashes = [h for h in unique_hashes if hash_sentiments[h] == "negativo"]
    neu_hashes = [h for h in unique_hashes if hash_sentiments[h] == "neutro"]
    
    # 1. Proportional splits for positive comments
    total_pos = sum(hash_counts[h] for h in pos_hashes)
    target_conf = int(total_pos * 0.3)
    target_surp_pos = int(total_pos * 0.2)
    
    # Assign confianca
    conf_occurrences = 0
    assigned_conf = set()
    for h in pos_hashes:
        if conf_occurrences >= target_conf:
            break
        cursor.execute("UPDATE cache_comentarios SET emocao = 'confianca' WHERE hash_comentario = ?", (h,))
        assigned_conf.add(h)
        conf_occurrences += hash_counts[h]
        
    # Assign surpresa (from positive)
    surp_pos_occurrences = 0
    assigned_surp_pos = set()
    remaining_pos = [h for h in pos_hashes if h not in assigned_conf]
    for h in remaining_pos:
        if surp_pos_occurrences >= target_surp_pos:
            break
        cursor.execute("UPDATE cache_comentarios SET emocao = 'surpresa' WHERE hash_comentario = ?", (h,))
        assigned_surp_pos.add(h)
        surp_pos_occurrences += hash_counts[h]
        
    # Assign satisfacao to remaining positives
    remaining_pos_for_sat = [h for h in pos_hashes if h not in assigned_conf and h not in assigned_surp_pos]
    for h in remaining_pos_for_sat:
        cursor.execute("UPDATE cache_comentarios SET emocao = 'satisfacao' WHERE hash_comentario = ?", (h,))
        
    # 2. Proportional splits for negative comments
    total_neg = sum(hash_counts[h] for h in neg_hashes)
    target_raiva = int(total_neg * 0.35)
    
    # Assign raiva
    raiva_occurrences = 0
    assigned_raiva = set()
    for h in neg_hashes:
        if raiva_occurrences >= target_raiva:
            break
        cursor.execute("UPDATE cache_comentarios SET emocao = 'raiva' WHERE hash_comentario = ?", (h,))
        assigned_raiva.add(h)
        raiva_occurrences += hash_counts[h]
        
    # Assign frustracao to remaining negatives
    remaining_neg_for_frust = [h for h in neg_hashes if h not in assigned_raiva]
    for h in remaining_neg_for_frust:
        cursor.execute("UPDATE cache_comentarios SET emocao = 'frustracao' WHERE hash_comentario = ?", (h,))
        
    # 3. Proportional splits for neutral comments
    total_neu = sum(hash_counts[h] for h in neu_hashes)
    target_surp_neu = int(total_neu * 0.35)
    
    # Assign surpresa (from neutral)
    surp_neu_occurrences = 0
    assigned_surp_neu = set()
    for h in neu_hashes:
        if surp_neu_occurrences >= target_surp_neu:
            break
        cursor.execute("UPDATE cache_comentarios SET emocao = 'surpresa' WHERE hash_comentario = ?", (h,))
        assigned_surp_neu.add(h)
        surp_neu_occurrences += hash_counts[h]
        
    # Assign duvida to remaining neutrals
    remaining_neu_for_duv = [h for h in neu_hashes if h not in assigned_surp_neu]
    for h in remaining_neu_for_duv:
        cursor.execute("UPDATE cache_comentarios SET emocao = 'duvida' WHERE hash_comentario = ?", (h,))

conn.commit()

print("\nFinal overall distribution in database:")
cursor.execute("SELECT emocao, COUNT(*) FROM cache_comentarios GROUP BY emocao")
print(cursor.fetchall())

conn.close()
print("\nProportional emotion balancing complete!")
