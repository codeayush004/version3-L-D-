from app.core.database import interns_collection, scores_collection, batches_collection, settings_collection
from typing import Dict, List

# Centralized list of markers for legacy/unattributed records
EXCLUDED_MARKERS = ['', 'unknown', 'none', 'null', 'n/a']

def calculate_weighted_score(scores: Dict, weightages: Dict) -> float:
    """Helper to calculate weighted average score based on settings."""
    if not scores: return 0
    
    valid_scores = {k: v for k, v in scores.items() if isinstance(v, (int, float))}
    if not valid_scores: return 0
    
    if not weightages:
        # Fallback to simple average if no weightages defined
        return round(sum(valid_scores.values()) / len(valid_scores), 1)
    
    weighted_sum = 0
    total_weight = 0
    for sub, score in valid_scores.items():
        if sub in weightages:
            w = weightages.get(sub)
            weighted_sum += score * (w / 100)
            total_weight += (w / 100)
    
    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0

class AnalyticsEngine:
    @staticmethod
    def get_deduplicated_data(manager_id: str = None):
        """Fetches the MOST RECENT intern and score for each unique (EmpID, batch_id) pair."""
        intern_match = {"manager_id": manager_id} if manager_id else {}
        
        intern_pipeline = [
            { "$match": intern_match },
            { "$sort": { "_id": -1 } },
            {
                "$group": {
                    "_id": { "EmpID": "$EmpID", "batch_id": "$batch_id" },
                    "doc": { "$first": "$$ROOT" }
                }
            },
            { "$replaceRoot": { "newRoot": "$doc" } }
        ]
        unique_interns = list(interns_collection.aggregate(intern_pipeline))
        
        # SCORES: Fetch globally for the batches owned by the manager or all if none
        # (Linking is primarily via EmpID + batch_id)
        score_pipeline = [
            { "$sort": { "_id": -1 } },
            {
                "$group": {
                    "_id": { "EmpID": "$EmpID", "batch_id": "$batch_id" },
                    "doc": { "$first": "$$ROOT" }
                }
            },
            { "$replaceRoot": { "newRoot": "$doc" } }
        ]
        unique_scores = list(scores_collection.aggregate(score_pipeline))
        score_map = { (s.get('EmpID'), s.get('batch_id')): s for s in unique_scores }
        
        return unique_interns, score_map

    @staticmethod
    def get_organization_summary(manager_id: str):
        """Generates a high-level summary of all batches using deduplicated data."""
        interns, score_map = AnalyticsEngine.get_deduplicated_data(manager_id)
        all_batches = list(batches_collection.find({"manager_id": manager_id}, {'_id': 0, 'batch_id': 1, 'name': 1, 'department': 1}))
        
        if not all_batches: return "No active batches found in the organization."
        
        batch_stats = []
        for b in all_batches:
            bid = b.get('batch_id')
            b_interns = [i for i in interns if i.get('batch_id') == bid]
            
            # Weighted settings
            b_settings = settings_collection.find_one({"batch_id": bid})
            pass_score = b_settings.get('passing_score', 60) if b_settings else 60
            
            # Performance & Conversion
            total_avg = 0
            count = 0
            conv_count = 0
            for i in b_interns:
                # Calculate conversion for this batch (STRICT: Requires actual date, not 'Pending')
                fte_date = i.get('fte_conversion_date', '').strip().lower()
                if fte_date != "" and fte_date not in EXCLUDED_MARKERS and fte_date != 'pending':
                    conv_count += 1
                
                s_doc = score_map.get((i.get('EmpID'), bid))
                if s_doc:
                    avg = calculate_weighted_score(s_doc.get('scores', {}), b_settings.get('weightages', {}) if b_settings else {})
                    if avg > 0:
                        total_avg += avg
                        count += 1
            
            avg = round(total_avg/count, 1) if count > 0 else 0
            conv_rate = round((conv_count/len(b_interns))*100, 1) if len(b_interns) > 0 else 0
            
            batch_stats.append(f"- **{b['name']}** ({b.get('department', 'Uncategorized')}): {len(b_interns)} interns, Avg: {avg}%, Conversion: {conv_count}/{len(b_interns)} ({conv_rate}%)")

        summary = f"### ORGANIZATION-WIDE SUMMARY\nTotal Unique Interns: {len(interns)}\n\n"
        summary += "\n".join(batch_stats)
        return summary

    @staticmethod
    def get_college_performance(manager_id: str):
        """Aggregates scores by college, excluding legacy markers."""
        interns, score_map = AnalyticsEngine.get_deduplicated_data(manager_id)
        if not interns: return "No intern data found."
        
        college_scores = {}
        for i in interns:
            col = i.get('college', '').strip()
            if not col or col.lower() in EXCLUDED_MARKERS: continue
            
            eid = i.get('EmpID')
            bid = i.get('batch_id')
            s_doc = score_map.get((eid, bid))
            if s_doc:
                # Need weightages for the batch
                settings = settings_collection.find_one({"batch_id": bid})
                avg = calculate_weighted_score(s_doc.get('scores', {}), settings.get('weightages', {}) if settings else {})
                if avg > 0:
                    if col not in college_scores: college_scores[col] = []
                    college_scores[col].append(avg)
        
        if not college_scores: return "No valid college performance data found."
        
        insight = "College Performance Ranking (Valid Records Only):\n"
        stats = []
        for c, score_list in college_scores.items():
            stats.append((c, sum(score_list)/len(score_list), len(score_list)))
            
        for c, avg, count in sorted(stats, key=lambda x: x[1], reverse=True):
            insight += f"- **{c}**: Avg Score: {round(avg, 1)}%, Count: {count} interns\n"
        return insight

    @staticmethod
    def get_conversion_stats(manager_id: str):
        """Aggregates conversion rates, excluding legacy markers."""
        interns, _ = AnalyticsEngine.get_deduplicated_data(manager_id)
        if not interns: return "No conversion data."
        
        stats = {}
        for i in interns:
            col = i.get('college', '').strip()
            if not col or col.lower() in EXCLUDED_MARKERS: continue
            
            fte_date = i.get('fte_conversion_date', '').strip().lower()
            is_converted = (fte_date != "" and fte_date not in EXCLUDED_MARKERS and fte_date != 'pending')
            
            if col not in stats: stats[col] = {"total": 0, "conv": 0}
            stats[col]["total"] += 1
            if is_converted:
                stats[col]["conv"] += 1
        
        if not stats: return "No valid conversion data found."
        
        insight = "FTE Conversion Trends by College (Valid Records):\n"
        ordered = sorted(stats.items(), key=lambda x: x[1]['conv'], reverse=True)
        for col, data in ordered:
            rate = (data["conv"] / data["total"]) * 100
            insight += f"- **{col}**: {data['conv']}/{data['total']} converted ({round(rate, 1)}%)\n"
        return insight

    @staticmethod
    def get_academic_correlation(manager_id: str):
        """Correlates performance with Degree/CGPA, excluding legacy markers."""
        interns, score_map = AnalyticsEngine.get_deduplicated_data(manager_id)
        if not interns: return "No academic data."
        
        degree_map = {} # {degree: {"scores": [], "conv": 0}}
        cgpa_buckets = {"<7": [], "7-8": [], "8-9": [], "9-10": []}
        
        for i in interns:
            col = i.get('college', '').strip()
            if not col or col.lower() in EXCLUDED_MARKERS: continue
            
            deg = i.get('degree') or "Unknown"
            cgpa = i.get('cgpa')
            try: cv = float(cgpa) if cgpa else 0
            except: cv = 0
            
            fte_date = i.get('fte_conversion_date', '').strip().lower()
            is_converted = (fte_date != "" and fte_date not in EXCLUDED_MARKERS and fte_date != 'pending')
            
            if deg not in degree_map: degree_map[deg] = {"scores": [], "conv": 0}
            if is_converted: degree_map[deg]["conv"] += 1
            
            s_doc = score_map.get((i.get('EmpID'), i.get('batch_id')))
            if s_doc:
                # Need weightages
                settings = settings_collection.find_one({"batch_id": i.get('batch_id')})
                avg = calculate_weighted_score(s_doc.get('scores', {}), settings.get('weightages', {}) if settings else {})
                if avg > 0:
                    degree_map[deg]["scores"].append(avg)
                    
                    if cv < 7: cgpa_buckets["<7"].append(avg)
                    elif cv < 8: cgpa_buckets["7-8"].append(avg)
                    elif cv < 9: cgpa_buckets["8-9"].append(avg)
                    else: cgpa_buckets["9-10"].append(avg)

        if not degree_map: return "No academic performance records found."
        
        # Performance and Conversion by Degree
        insight = "Performance and Conversion by Degree (Unique Records):\n"
        # We need to compute total interns per degree again to be sure
        deg_totals = {}
        for i in interns:
            d = i.get('degree') or "Unknown"
            deg_totals[d] = deg_totals.get(d, 0) + 1
            
        ordered_degrees = sorted(degree_map.items(), key=lambda x: sum(x[1]["scores"])/len(x[1]["scores"]) if x[1]["scores"] else 0, reverse=True)
        for d, data in ordered_degrees:
            scores = data["scores"]
            avg = round(sum(scores)/len(scores), 1) if scores else 0
            conv = data["conv"]
            total = deg_totals.get(d, 0)
            rate = round((conv/total)*100, 1) if total > 0 else 0
            insight += f"- **{d}**: Avg {avg}%, Conversion: {conv}/{total} ({rate}%)\n"
            
        insight += "\nCGPA vs Performance Correlation (Unique Records):\n"
        for buck, l in cgpa_buckets.items():
            if l:
                avg_score = round(sum(l)/len(l), 1)
                insight += f"- **CGPA {buck}**: {avg_score}% avg score (Count: {len(l)} interns)\n"
        return insight
    @staticmethod
    def get_top_performers(manager_id: str, limit: int = 5):
        """Calculates top performers across all batches for a manager, using batch-specific weightages."""
        interns, score_map = AnalyticsEngine.get_deduplicated_data(manager_id)
        if not interns: return "No intern data available for ranking."
        
        batch_settings_cache = {}
        ranked_list = []
        for i in interns:
            eid = i.get('EmpID')
            bid = i.get('batch_id')
            s_doc = score_map.get((eid, bid))
            if not s_doc: continue
            
            if bid not in batch_settings_cache:
                settings = settings_collection.find_one({"batch_id": bid})
                batch_settings_cache[bid] = settings.get('weightages', {}) if settings else {}
            
            weightages = batch_settings_cache[bid]
            final_score = calculate_weighted_score(s_doc.get('scores', {}), weightages)
            
            # Fetch feedback for top performers
            from app.core.database import feedback_collection
            f_doc = feedback_collection.find_one({"EmpID": eid, "batch_id": bid}, sort=[("_id", -1)])
            feedback_text = f_doc.get('text', '--') if f_doc else '--'
            
            if final_score > 0:
                ranked_list.append({
                    "Name": i.get('Name'),
                    "EmpID": eid,
                    "Batch": i.get('mapped_batch') or bid,
                    "Score": final_score,
                    "Feedback": feedback_text
                })
            
        if not ranked_list: return "No valid scores found to rank interns."
        top_interns = sorted(ranked_list, key=lambda x: x['Score'], reverse=True)[:limit]
        
        insight = f"Top {len(top_interns)} Performers Across All Batches:\n"
        for idx, t in enumerate(top_interns, 1):
            insight += f"{idx}. **{t['Name']}** ({t['EmpID']}) - Batch: {t['Batch']} | Overall: **{t['Score']}%** | Feedback: {t['Feedback']}\n"
        return insight
