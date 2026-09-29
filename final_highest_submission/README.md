# Final Highest Submission Package: Candidate EGFR-pH-HB-G01
## Anthropic × Adaptyv Protein Design Competition 2026 (Challenge 1)

> [!IMPORTANT]
> **Competition Confidentiality Active**:
> In accordance with competition best practices, the winning candidate sequence (`EGFR-pH-HB-G01`) is masked in this public repository to protect intellectual property against automated web scraping prior to the official competition deadline (**October 4, 2026 AoE**).
> 
> **For Direct Submission to ProteinBase**:
> Use your private unmasked files generated on your local machine:
> - `PROTEINBASE_SUBMISSION_UNMASKED_LOCAL.csv`
> - `PROTEINBASE_SUBMISSION_UNMASKED_LOCAL.fasta`

---

### Candidate Summary: EGFR-pH-HB-G01

| Parameter | Value | Assessment |
| :--- | :--- | :--- |
| **Molecule Class** | `single_chain` | Verified single-chain format |
| **Length** | 69 aa | Meets 10–250 aa rule |
| **Cysteine Count** | **0** | Soluble *E. coli* BL21 cytoplasmic yield |
| **ESMFold Monomer pLDDT** | **79.77** | High-confidence 3-helix bundle |
| **Kaggle Complex pLDDT** | **77.28** | #1 Highest complex pLDDT on Tesla T4 GPU |
| **Novelty Score** | **4 / 4** | EBI BLASTP identity < 35% vs Swiss-Prot |
| **Interface Histidines** | 4 (His5, His6, His59, His60) | Warburg acidosis pH switch |
| **Charge Shift ($\Delta Q$)** | **+1.61** | Strong electrostatic engagement at pH 6.5 |
| **Cross-Species Reactivity** | Human & Mouse | Targets 100% conserved Domain III groove |

---

### Package Contents
- `METHODOLOGY.md`: Detailed biophysical methodology and experimental assay documentation.
- `PROTEINBASE_SUBMISSION.csv`: Official template file with masked sequence for public repository.
- `PROTEINBASE_SUBMISSION_UNMASKED_LOCAL.csv`: Unmasked local submission CSV (git-ignored).
- `PROTEINBASE_SUBMISSION_UNMASKED_LOCAL.fasta`: Unmasked local submission FASTA (git-ignored).
- `structures/`: ESMFold monomer coordinate PDB and Kaggle GPU complex PDB.
