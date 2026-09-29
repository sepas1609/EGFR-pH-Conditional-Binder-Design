import json
import os

with open('data/structures/final_evaluated_candidates.json') as f:
    candidates = json.load(f)

# Filter out B02 and A02 which had the RGAP6 coiled coil homology match
clean_candidates = [c for c in candidates if c['name'] not in ['EGFR-pH-HB-B02', 'EGFR-pH-HB-A02']]

# Rank 1 is now EGFR-pH-HB-G01
# Re-index ranks
for i, c in enumerate(clean_candidates, 1):
    c['rank'] = i

# Save clean candidates json
with open('data/structures/clean_evaluated_candidates.json', 'w') as f:
    json.dump(clean_candidates, f, indent=2)

print(f'Prepared {len(clean_candidates)} clean passing candidates. Top design is {clean_candidates[0]["name"]}.')
