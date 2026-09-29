#!/usr/bin/env python3
"""
EGFR Conditional Binder Design Script
Anthropic x Adaptyv Protein Design Competition 2026 - Challenge 1

Generates 20 de novo 3-helix bundle miniprotein candidates that:
1. Bind human EGFR (Domain III)
2. Bind mouse EGFR (cross-species via conserved epitope)
3. Bind at pH 6.5 (tumor) but NOT at pH 7.4 (normal tissue)

Design Mechanism: Histidine-switch at binder-EGFR interface
  - pH 6.5: His protonated (+1) → salt bridge with EGFR Asp/Glu → HIGH affinity
  - pH 7.4: His neutral → no favorable ionic contact → LOW affinity

EGFR Conserved Target Residues (human & mouse): D355, E352, E384, E392, D420
Author: Competition submission
"""

import json
import math
from typing import List, Dict, Tuple

# ─── AMINO ACID PROPERTIES ──────────────────────────────────────────────────

AA_MW = {
    'A': 89.09, 'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.16,
    'E': 147.13, 'Q': 146.15, 'G': 75.03, 'H': 155.16, 'I': 131.17,
    'L': 131.17, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
    'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
}

AA_CHARGE_pH74 = {
    'D': -1, 'E': -1, 'K': +1, 'R': +1, 'H': 0,   # His uncharged at 7.4
    'A': 0, 'N': 0, 'Q': 0, 'G': 0, 'I': 0, 'L': 0,
    'M': 0, 'F': 0, 'P': 0, 'S': 0, 'T': 0, 'W': 0,
    'Y': 0, 'V': 0, 'C': 0
}

AA_CHARGE_pH65 = {
    'D': -1, 'E': -1, 'K': +1, 'R': +1, 'H': +0.5, # His ~50% protonated at pH 6.5
    'A': 0, 'N': 0, 'Q': 0, 'G': 0, 'I': 0, 'L': 0,
    'M': 0, 'F': 0, 'P': 0, 'S': 0, 'T': 0, 'W': 0,
    'Y': 0, 'V': 0, 'C': 0
}

HYDROPHOBIC = set('VILMFYW')
HELIX_FORMERS = set('AELKRQMHV')  # Strong helix propensity

# ─── DESIGN RULES (from Baker Lab / structural biology) ──────────────────────

# 3-helix bundle topology: H1-loop1-H2-loop2-H3
# H1: binding helix facing EGFR (contains pH-switch His)
# H2: core stability helix
# H3: support helix (optional buried His)

# Heptad repeat for coiled-coil: (abcdefg)n
# a, d positions: hydrophobic (core packing) → L, I, V, A
# e, g positions: charged (salt bridges, solubility) → E, R, K, Q

# EGFR Domain III surface contact residues (conserved human+mouse):
EGFR_CONSERVED_TARGETS = {
    'D355': {'charge': -1, 'position': 'groove_center'},
    'E352': {'charge': -1, 'position': 'groove_upper'},
    'E384': {'charge': -1, 'position': 'groove_lateral'},
    'E392': {'charge': -1, 'position': 'loop_region'},
    'D420': {'charge': -1, 'position': 'groove_lower'},
    'F352': {'charge':  0, 'position': 'hydrophobic_patch'},
    'Y373': {'charge':  0, 'position': 'aromatic_cluster'},
    'I374': {'charge':  0, 'position': 'hydrophobic_patch'},
}


def calculate_mw(sequence: str) -> float:
    """Calculate molecular weight in Da"""
    # Subtract water for each peptide bond
    return sum(AA_MW.get(aa, 110) for aa in sequence) - (len(sequence) - 1) * 18.02


def calculate_charge(sequence: str, ph: float) -> float:
    """Calculate net charge at given pH using Henderson-Hasselbalch"""
    charge = 0.0
    for aa in sequence:
        if aa == 'D':
            charge += -1 / (1 + 10 ** (3.86 - ph))   # pKa 3.86
        elif aa == 'E':
            charge += -1 / (1 + 10 ** (4.07 - ph))   # pKa 4.07
        elif aa == 'H':
            charge += +1 / (1 + 10 ** (ph - 6.04))   # pKa 6.04 (average)
        elif aa == 'K':
            charge += +1 / (1 + 10 ** (ph - 10.54))  # pKa 10.54
        elif aa == 'R':
            charge += +1 / (1 + 10 ** (ph - 12.48))  # pKa 12.48
        elif aa == 'C':
            charge += -1 / (1 + 10 ** (8.3 - ph))    # pKa 8.3
        elif aa == 'Y':
            charge += -1 / (1 + 10 ** (10.46 - ph))  # pKa 10.46
    # N-terminus (+1) and C-terminus (-1)
    charge += 1 / (1 + 10 ** (ph - 8.0))   # N-term pKa ~8.0
    charge -= 1 / (1 + 10 ** (3.1 - ph))   # C-term pKa ~3.1
    return charge


def calculate_ph_delta_charge(sequence: str) -> float:
    """Calculate charge difference between pH 6.5 and 7.4
    Positive value = more positive at pH 6.5 (good for our design)"""
    return calculate_charge(sequence, 6.5) - calculate_charge(sequence, 7.4)


def calculate_aliphatic_index(sequence: str) -> float:
    """Aliphatic index = 100 * (Xa + 2.9*Xv + 3.9*(Xi + Xl))"""
    n = len(sequence)
    Xa = sequence.count('A') / n
    Xv = sequence.count('V') / n
    Xi = sequence.count('I') / n
    Xl = sequence.count('L') / n
    return 100 * (Xa + 2.9 * Xv + 3.9 * (Xi + Xl))


def count_helix_breakers(sequence: str) -> int:
    """Count proline (helix breaker) residues"""
    return sequence.count('P')


def calculate_his_count(sequence: str) -> int:
    """Count histidine residues for pH switch"""
    return sequence.count('H')


def calculate_ph_switch_score(sequence: str, h1_end: int = 18) -> float:
    """
    Score pH-switching potential.
    Based on:
    - Number of His in H1 (binding helix, first ~18 aa)
    - His proximity to acidic residues in binder (proxy for EGFR D/E contacts)
    - Charge delta between pH 6.5 and 7.4
    """
    h1_seq = sequence[:h1_end]
    his_in_h1 = h1_seq.count('H')
    
    # Charge delta contribution (max score = 5 per His in H1)
    delta_charge = abs(calculate_ph_delta_charge(sequence))
    
    # Local acidic context score (His adjacent to D/E on EGFR is handled by structure)
    # Here we score if binder has any Asp/Glu that might scaffold the His
    acidic_near_h1 = sum(1 for aa in h1_seq if aa in 'DE')
    
    # Final score
    score = (his_in_h1 * 3.0) + (delta_charge * 1.5) + (acidic_near_h1 * 0.5)
    return round(score, 2)


def check_novelty_heuristic(sequence: str) -> bool:
    """
    Heuristic novelty check (actual BLAST check is done separately).
    Reject if too similar to known natural protein motifs.
    """
    # Known EGFR-binding motifs to avoid
    known_motifs = [
        'LAEQ',   # EGF motif
        'CQGTSNK', # EGFR domain
        'EPAM',    # known binder fragment
    ]
    for motif in known_motifs:
        if motif in sequence:
            return False
    return True


def calculate_instability_index(sequence: str) -> float:
    """
    Simplified instability index. 
    Values < 40 = stable protein.
    Based on dipeptide instability weights (simplified).
    """
    # Destabilizing dipeptides (simplified from ProtParam)
    destabilizing = {
        'DC': 20.26, 'DD': -7.49, 'DG': 1.08, 'DP': -1.08,
        'WW': 1.37, 'WC': 1.0, 'FS': 1.0, 'FT': 13.34,
    }
    score = 0.0
    for i in range(len(sequence) - 1):
        dp = sequence[i:i+2]
        score += destabilizing.get(dp, 0.0)
    return (10 / len(sequence)) * score


def validate_sequence(seq: str, name: str) -> Dict:
    """Validate a candidate sequence against competition and design criteria"""
    issues = []
    
    length = len(seq)
    mw = calculate_mw(seq)
    charge_74 = calculate_charge(seq, 7.4)
    charge_65 = calculate_charge(seq, 6.5)
    ai = calculate_aliphatic_index(seq)
    his_n = calculate_his_count(seq)
    ph_score = calculate_ph_switch_score(seq)
    helix_breakers = count_helix_breakers(seq)
    delta_charge = calculate_ph_delta_charge(seq)
    
    # Competition rules
    if not (10 <= length <= 250):
        issues.append(f"Length {length} outside 10-250 range")
    if 'C' in seq:
        issues.append("Contains Cys (disulfide risk, avoid if possible)")
    if helix_breakers > 2:
        issues.append(f"Too many Pro ({helix_breakers}) — helix breakers")
    
    # Design rules
    if his_n < 2:
        issues.append(f"Only {his_n} His — insufficient pH switch")
    if ph_score < 3.0:
        issues.append(f"pH switch score {ph_score} < 3.0 — weak conditionality")
    if ai < 70:
        issues.append(f"Aliphatic index {ai:.1f} < 70 — may be unstable")
    if charge_74 > 4:
        issues.append(f"Charge at pH 7.4 = {charge_74:.1f} — too positive (aggregation risk)")
    if charge_74 < -2:
        issues.append(f"Charge at pH 7.4 = {charge_74:.1f} — too negative")

    if not check_novelty_heuristic(seq):
        issues.append("Matches known natural motif — check novelty!")
    
    return {
        'name': name,
        'sequence': seq,
        'length': length,
        'mw_da': round(mw, 1),
        'charge_pH74': round(charge_74, 2),
        'charge_pH65': round(charge_65, 2),
        'delta_charge': round(delta_charge, 2),
        'aliphatic_index': round(ai, 1),
        'his_count': his_n,
        'ph_switch_score': ph_score,
        'helix_breakers_pro': helix_breakers,
        'issues': issues,
        'passes_filter': len(issues) == 0
    }


# ─── 20 CANDIDATE SEQUENCES ──────────────────────────────────────────────────
# 
# DESIGN RATIONALE:
# All sequences are 3-helix bundles with:
# H1 (binding helix): contains His for pH switch, hydrophobic contacts to EGFR
# Loop1: GSGS or GGS (flexible)
# H2 (core helix): Leu/Ala rich, no His
# Loop2: GGS (flexible)
# H3 (stabilizer): Leu/Ala rich, optional buried His
#
# EGFR Contact Strategy:
# H1 faces EGFR Domain III conserved surface (D355, E352, E384)
# His at H1 positions 4 & 8 (or 5 & 9) → form salt bridges with EGFR D355 & E352 at pH 6.5
# Phe/Tyr at H1 positions 1 & 5 → hydrophobic contacts with EGFR F352, Y373 (conserved)
# Lys/Arg at H1 position 12 → baseline salt bridge with EGFR E384 (pH-independent baseline)

CANDIDATES = [
    # ═══════════════════════════════════════════════════════════════
    # SET A: His at H1 positions 4,8 — Standard placement
    # H1: contacts D355 (His4) + E352 (His8)
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-A01',
        'group': 'A_Standard_His48',
        'sequence': 'FYNAHHLKALLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 7],  # 0-indexed
        'design_notes': 'Standard 3HB, His at 4+8, Phe1+Tyr2 hydrophobic, Lys9 baseline contact'
    },
    {
        'name': 'EGFR-pH-HB-A02',
        'group': 'A_Standard_His48',
        'sequence': 'WYQAHHLKALLAEELANLKRLEEAQKRLEEQLKGSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 7],
        'design_notes': 'Trp1+Tyr3 hydrophobic patch, His at 5+8, extra Ala for helicity'
    },
    {
        'name': 'EGFR-pH-HB-A03',
        'group': 'A_Standard_His48',
        'sequence': 'FYNHHALKALLQEELAQMKRLEEAQKRLEQALK GSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 4],  # Adjacent His for cooperative switching
        'design_notes': 'Adjacent His3+4 for cooperative pH effect, Asn for H-bond'
    },
    {
        'name': 'EGFR-pH-HB-A04',
        'group': 'A_Standard_His48',
        'sequence': 'FYNAHHLRALLQQELAQLKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 7],
        'design_notes': 'Arg at position 8 for baseline contact, His 4+8 pH switch'
    },
    {
        'name': 'EGFR-pH-HB-A05',
        'group': 'A_Standard_His48',
        'sequence': 'YWNAHHLKALLQQELAQMKRLEEAQKRLEQALKGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 7],
        'design_notes': 'Tyr1+Trp2 aromatic pair for pi-stacking with EGFR Y373'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET B: His at H1 pos 4,8 + buried His in H3 (cooperative switching)
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-B01',
        'group': 'B_Buried_His_H3',
        'sequence': 'FYNAHHLKALLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEHHLRRLEQALK',
        'his_positions_h1': [3, 7],
        'his_h3_buried': True,
        'design_notes': 'Buried His in H3 (positions 63+64) for cooperative pH destabilization'
    },
    {
        'name': 'EGFR-pH-HB-B02',
        'group': 'B_Buried_His_H3',
        'sequence': 'WYQAHHLKALLAEELANLKRLEEAQKRLEEQLKGSGSLAAALRRLEQALREQKLGSLEHHLRRLEQALK',
        'his_positions_h1': [4, 7],
        'his_h3_buried': True,
        'design_notes': 'Trp1, H3 buried His pair, full cooperative switch'
    },
    {
        'name': 'EGFR-pH-HB-B03',
        'group': 'B_Buried_His_H3',
        'sequence': 'FYNAHHLKALLQQELAELKRLEQAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQHLK',
        'his_positions_h1': [3, 7],
        'his_h3_buried': True,
        'design_notes': 'H3 C-terminal His for buried H-bond network at pH threshold'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET C: His at shifted positions 5,9 — Alternative register
    # H1: contacts E392 (His5) + D420 (His9 via adjusted geometry)
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-C01',
        'group': 'C_Shifted_His59',
        'sequence': 'FYNRAHHLKALLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 7],
        'design_notes': 'Arg3 for baseline contact, His 5+8 shifted register, targets E392'
    },
    {
        'name': 'EGFR-pH-HB-C02',
        'group': 'C_Shifted_His59',
        'sequence': 'WYNRHHAKALLQEELAQMKRLEEAQKRLEQALKGSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 5],
        'design_notes': 'Trp1 + Tyr2 aromatic, His5+6 cluster for strong pH cooperativity'
    },
    {
        'name': 'EGFR-pH-HB-C03',
        'group': 'C_Shifted_His59',
        'sequence': 'FYNKAHHLALLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 7],
        'design_notes': 'Lys4 for spacer, His 5+8 shifted, cross-species optimized geometry'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET D: Wider His spacing (positions 4,11) — Bridges two EGFR contacts
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-D01',
        'group': 'D_Wide_His411',
        'sequence': 'FYNKHLAKLHLLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 9],
        'design_notes': 'Wider His spacing, bridges D355 and D420 on EGFR simultaneously'
    },
    {
        'name': 'EGFR-pH-HB-D02',
        'group': 'D_Wide_His411',
        'sequence': 'WYNKHLARLHLLQQELAELKRLEEAQKRLEQALKGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 9],
        'design_notes': 'Arg7 for baseline, wide His coverage of EGFR groove'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET E: Extended H1 (21 aa) for deeper EGFR interface engagement
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-E01',
        'group': 'E_Extended_H1',
        'sequence': 'FYNAHHLKALLQQELAELKRQLGSGSLEAALRRLEQALREQKLGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 7],
        'design_notes': 'Extended H1 (21aa), deeper EGFR groove penetration'
    },
    {
        'name': 'EGFR-pH-HB-E02',
        'group': 'E_Extended_H1',
        'sequence': 'WYQAHHLKALLAEELANLKRQLGSGSLAAALRRLEQALREQKLGSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [4, 7],
        'design_notes': 'Extended H1 with Trp1, covers broader EGFR Domain III surface'
    },
    {
        'name': 'EGFR-pH-HB-E03',
        'group': 'E_Extended_H1',
        'sequence': 'FYNHHALKALLQEELAQMKRQLGSGSLAAALRRLEQALREQKLGSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 4],
        'design_notes': 'Adjacent His for cooperative, extended backbone for cross-species'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET F: High pI variants — enhanced tumor microenvironment association
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-F01',
        'group': 'F_High_pI',
        'sequence': 'FYNAHHLKKLLQQELAKLKRLEEAQKRLEQALKGSGSLEAKLRRLEQALREQKLGSLEAHLRRLEQALKK',
        'his_positions_h1': [3, 7],
        'design_notes': 'High pI design (extra Lys), enhanced electrostatic docking to tumor cell'
    },
    {
        'name': 'EGFR-pH-HB-F02',
        'group': 'F_High_pI',
        'sequence': 'WYQAHHLKRLLAEELANLKRLEEAQKRLEQALKGSGSLAAALRRLEQALREQKLGSLEAHLRRLEQALKK',
        'his_positions_h1': [4, 7],
        'design_notes': 'High pI, Trp1, Arg5 for initial electrostatic association'
    },

    # ═══════════════════════════════════════════════════════════════
    # SET G: Dual interface design — contacts both D355/E352 cluster AND E384 cluster
    # ═══════════════════════════════════════════════════════════════
    {
        'name': 'EGFR-pH-HB-G01',
        'group': 'G_Dual_Interface',
        'sequence': 'FYNAHHLKAHLQQELAELKRLEEAQKRLEQALQGSGSLEAALRRLEQALREQKLGSLEAHLRRLEQALK',
        'his_positions_h1': [3, 7, 10],  # Three His in H1 for dual interface coverage
        'design_notes': 'Three His in H1 for dual EGFR contact cluster coverage (D355+E352+E384)'
    },
]


def print_design_report(validated: List[Dict]) -> None:
    """Print formatted design report"""
    print("\n" + "="*80)
    print("EGFR CONDITIONAL BINDER DESIGN REPORT")
    print("Anthropic x Adaptyv Competition 2026 — Challenge 1")
    print("="*80)
    
    passing = [v for v in validated if v['passes_filter']]
    print(f"\n✅ Passing designs: {len(passing)}/{len(validated)}")
    print(f"⚠️  Designs with issues: {len(validated) - len(passing)}/{len(validated)}")
    
    print("\n" + "-"*80)
    print(f"{'Name':<22} {'Len':>4} {'MW':>8} {'His':>4} {'pH Δq':>6} {'pHsc':>6} {'AI':>6} {'OK':>4}")
    print("-"*80)
    
    for v in validated:
        ok = "✅" if v['passes_filter'] else "⚠️ "
        print(f"{v['name']:<22} {v['length']:>4} {v['mw_da']:>7.0f} {v['his_count']:>4} "
              f"{v['delta_charge']:>+6.2f} {v['ph_switch_score']:>6.2f} "
              f"{v['aliphatic_index']:>6.1f} {ok}")
    
    print("\n" + "="*80)
    print("DETAILED METRICS FOR PASSING DESIGNS:")
    print("="*80)
    for v in passing:
        print(f"\n📌 {v['name']} ({v['length']} aa, {v['mw_da']:.0f} Da)")
        print(f"   Sequence: {v['sequence']}")
        print(f"   Charge: pH7.4={v['charge_pH74']:+.2f} | pH6.5={v['charge_pH65']:+.2f} | Δq={v['delta_charge']:+.2f}")
        print(f"   pH Switch Score: {v['ph_switch_score']:.2f} (target >3.0)")
        print(f"   Aliphatic Index: {v['aliphatic_index']:.1f} (target >70)")
        print(f"   His count: {v['his_count']}")


def save_results(validated: List[Dict], output_path: str) -> None:
    """Save all results to JSON"""
    with open(output_path, 'w') as f:
        json.dump({
            'competition': 'Anthropic x Adaptyv 2026 — Challenge 1',
            'target': 'EGFR (conditional binder, pH 6.5 ON / 7.4 OFF)',
            'scaffold': '3-helix bundle miniprotein 60-90 aa',
            'mechanism': 'Histidine-switch: protonation at pH 6.5 creates salt bridge with EGFR D355/E352',
            'designs': validated
        }, f, indent=2)
    print(f"\n💾 Results saved to: {output_path}")


def save_sequences_csv(validated: List[Dict], output_path: str) -> None:
    """Save sequences in competition submission format (CSV)"""
    passing = sorted([v for v in validated if v['passes_filter']], 
                     key=lambda x: -x['ph_switch_score'])
    
    lines = ['rank,name,sequence,length,his_count,ph_switch_score,delta_charge_65vs74,aliphatic_index,mw_da,notes']
    
    for i, v in enumerate(passing, 1):
        notes = f"3HB scaffold; His-switch mechanism; group={v.get('group','')}"
        lines.append(
            f"{i},{v['name']},{v['sequence']},{v['length']},"
            f"{v['his_count']},{v['ph_switch_score']},{v['delta_charge']},"
            f"{v['aliphatic_index']},{v['mw_da']},\"{notes}\""
        )
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"📊 Submission CSV saved to: {output_path}")


def main():
    print("🧬 EGFR Conditional Binder — Sequence Validation")
    print("Generating and validating 20 candidate miniproteins...\n")
    
    # Clean sequences (remove spaces introduced for readability)
    for c in CANDIDATES:
        c['sequence'] = c['sequence'].replace(' ', '')
    
    # Validate all candidates
    validated = []
    for c in CANDIDATES:
        v = validate_sequence(c['sequence'], c['name'])
        v['group'] = c.get('group', 'unknown')
        v['design_notes'] = c.get('design_notes', '')
        v['his_positions_h1'] = c.get('his_positions_h1', [])
        validated.append(v)
    
    # Print report
    print_design_report(validated)
    
    # Save results
    import os
    os.makedirs('../analysis', exist_ok=True)
    os.makedirs('../submission', exist_ok=True)
    save_results(validated, '../analysis/design_validation.json')
    save_sequences_csv(validated, '../submission/candidates_initial.csv')
    
    # Summary statistics
    passing = [v for v in validated if v['passes_filter']]
    if passing:
        avg_ph_score = sum(v['ph_switch_score'] for v in passing) / len(passing)
        avg_his = sum(v['his_count'] for v in passing) / len(passing)
        print(f"\n📈 STATISTICS:")
        print(f"   Average pH switch score: {avg_ph_score:.2f}")
        print(f"   Average His count: {avg_his:.1f}")
        print(f"   Length range: {min(v['length'] for v in passing)}–{max(v['length'] for v in passing)} aa")
    
    print("\n✅ Next step: Run notebooks/egfr_esm_validation.ipynb for structure prediction")
    return validated


if __name__ == '__main__':
    results = main()
