from datetime import datetime, timedelta

DAYS_LOOKBACK = 30
today_date_obj = datetime.now()
start_date_obj = today_date_obj - timedelta(days=DAYS_LOOKBACK)

today_date = today_date_obj.strftime("%Y-%m-%d")
start_date = start_date_obj.strftime("%Y-%m-%d")

garment_simulation_query = f"""
# Research Directive: Garment Simulation & Computational Fashion

**Objective:** Conduct a targeted research sweep for the latest advancements in computer graphics, computational physics, and programmatic design related to simulating clothing on virtual human avatars.

## 1. Constraints & Scope (Strict Adherence Required)
*   **Timeframe:** Focus **STRICTLY** on research, codebases, and technical articles published or released between **{start_date}** and **{today_date}**.
*   **Quantity:** Curate a maximum of **10 distinct items**.
*   **Ranking:** Order items by direct relevance to the *Target Research Domains* below (most impactful first).
*   **Context:** Do not include older research unless absolutely necessary for foundational context (clearly labeled as "Background").

## 2. Target Research Domains

### A. Programmatic Pattern Design & "Garment-Code"
*   **Sewing Pattern Languages:** Frameworks treating garments as code (e.g., similar to *GarmentCode*). Usage of parametric design for massive dataset generation.
*   **2D-to-3D Logic:** Algorithms solving the assembly of 2D flat patterns onto 3D bodies (seaming forces, topology).
*   **Inverse Design:** Optimization techniques to derive 2D pattern parameters from target 3D shapes/fits.

### B. Physics-Based Modeling
*   **Solver Comparison:** Advances in Mass-Spring, FEM (Finite Element Method), and PBD (Position-Based Dynamics).
*   **Performance:** New trade-offs discovered between physical accuracy, stability, and computational cost.

### C. Collision Handling
*   **Robustness:** Novel techniques for self-collision and cloth-body interaction.
*   **High-Velocity:** Solutions for "tunneling" artifacts in fast-motion scenarios.

### D. AI & Data-Driven Methods
*   **Neural Physics:** Neural Cloth Simulation, Graph Neural Networks (GNNs), and neural surrogates replacing traditional solvers.
*   **Datasets:** New or updated datasets for training (e.g., successors or expansions to CLOTH3D).

### E. Real-Time vs. High-Fidelity
*   **VTON:** Specific requirements for Virtual Try-On in e-commerce vs. offline VFX.
*   **Consumer Hardware:** Optimization for mobile/web real-time simulation.

### F. Material Realism
*   **Complex Behaviors:** Modeling anisotropy, hysteresis, and specific fabrics (silk, denim).
*   **Parameter Estimation:** Capturing digital material parameters from physical world data.

## 3. Deliverable Requirements
Provide a detailed synthesis of the gathered intelligence. For each of the top 10 items, include:
*   **Title & Source:** (Link/Citation)
*   **Relevance:** Which domain (A-F) it impacts and why.
*   **Key Innovation:** What specific problem does it solve?
"""
