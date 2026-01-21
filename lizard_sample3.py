import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. SETUP THE APP CONFIGURATION & INTRO
# ==========================================
st.set_page_config(page_title="Lizard Sampling Simulation", layout="wide")

st.title("🦎 Island Lizard Weight Study")

st.markdown("""
**The goal of this study is to estimate the average weight of a population of lizards on a remote island.**

The lizard population has four subtypes, each with different characteristics and subpopulation sizes:
""")

# Create a summary table of the population parameters
population_stats = pd.DataFrame({
    "Lizard Type": ["Beach (Sandy)", "Jungle (Dense)", "Wetlands (Swamp)", "Caves (Deep)"],
    "Mean Weight (g)": [50, 120, 220, 350],
    "Std Dev (g)": [5, 15, 30, 60],
    "Population Size": [4000, 4000, 1500, 500]
})

# Display the table (Hide the index to make it look cleaner)
st.table(population_stats)

st.info("👈 **Configure your sampling strategy in the sidebar to begin.**")

# ==========================================
# 2. GENERATE POPULATION (Cached)
# ==========================================
@st.cache_data
def get_population():
    np.random.seed(101) 
    # These match the table displayed above
    groups = {
        'Beach':    [50,  5,   4000],  
        'Jungle':   [120, 15,  4000],  
        'Wetlands': [220, 30,  1500],  
        'Caves':    [350, 60,  500]    
    }
    
    pop_list = []
    for name, params in groups.items():
        mu, sigma, n_count = params
        weights = np.random.normal(mu, sigma, n_count)
        
        # Bias Logic (Catchability)
        if name == 'Caves': catch_prob = 0.05 
        elif name == 'Wetlands': catch_prob = 0.6 
        else: catch_prob = 1.0
        
        pop_list.append(pd.DataFrame({
            'ID': [f"{name[0]}_{i}" for i in range(n_count)],
            'Habitat': name,
            'Weight_g': weights,
            'Catch_Prob': catch_prob 
        }))

    return pd.concat(pop_list).reset_index(drop=True)

full_pop = get_population()
true_mean = full_pop['Weight_g'].mean()

# ==========================================
# 3. SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.header("📋 Sampling Strategy")
    
    # Checkboxes
    enable_stratified = st.checkbox("Enable Manual Stratified Sampling")
    enable_bias = st.checkbox("Enable 'Field Conditions' (Bias)")
    
    st.divider()
    
    # Dynamic Input Fields
    if enable_stratified:
        st.subheader("Stratified Quotas")
        st.caption("Enter the number of lizards to catch from each habitat:")
        n_beach = st.number_input("Beach (N=4000)", min_value=0, value=25)
        n_jungle = st.number_input("Jungle (N=4000)", min_value=0, value=25)
        n_wetland = st.number_input("Wetlands (N=1500)", min_value=0, value=25)
        n_caves = st.number_input("Caves (N=500)", min_value=0, value=25)
    else:
        st.subheader("Simple Random Sample")
        n_total = st.number_input("Total Sample Size", min_value=1, max_value=10000, value=100)
    
    st.divider()
    
    # The "Action" Button
    run_btn = st.button("Draw Sample", type="primary")

# ==========================================
# 4. MAIN SIMULATION LOGIC
# ==========================================
if run_btn:
    sample_df = pd.DataFrame()
    
    # --- STRATIFIED LOGIC ---
    if enable_stratified:
        strata_requests = {
            'Beach': n_beach, 'Jungle': n_jungle, 
            'Wetlands': n_wetland, 'Caves': n_caves
        }
        sub_samples = []
        for habitat, n_req in strata_requests.items():
            if n_req > 0:
                sub_pop = full_pop[full_pop['Habitat'] == habitat]
                # If requesting more than exists, take all
                to_take = min(n_req, len(sub_pop))
                sub_samples.append(sub_pop.sample(n=to_take))
        
        if sub_samples:
            sample_df = pd.concat(sub_samples)
            st.success(f"✅ Stratified Sample Drawn: {len(sample_df)} lizards.")
        else:
            st.error("⚠️ You requested 0 lizards.")

    # --- SIMPLE LOGIC ---
    else:
        weights = 'Catch_Prob' if enable_bias else None
        if enable_bias:
            st.warning("⚠️ Field Conditions Active: Heavy lizards are harder to find (Undercoverage Bias)!")
        
        sample_df = full_pop.sample(n=n_total, weights=weights)
        st.success(f"✅ Random Sample Drawn: {len(sample_df)} lizards.")

    # ==========================================
    # 5. RESULTS DISPLAY
    # ==========================================
    if not sample_df.empty:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        sample_mean = sample_df['Weight_g'].mean()
        error = sample_mean - true_mean
        
        col1.metric("True Pop Mean", f"{true_mean:.2f} g")
        col2.metric("Sample Mean", f"{sample_mean:.2f} g", delta=f"{error:.2f} g", delta_color="inverse")
        col3.metric("Sample Size", f"{len(sample_df)}")

        # --- PLOTS ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # Histogram
        ax1.hist(full_pop['Weight_g'], bins=60, alpha=0.2, color='gray', label='Population', density=True)
        ax1.hist(sample_df['Weight_g'], bins=40, alpha=0.7, color='blue', label='Sample', density=True)
        ax1.axvline(true_mean, color='black', linestyle='--', label='True Mean')
        ax1.axvline(sample_mean, color='red', linestyle='-', label='Sample Mean')
        ax1.set_title("Weight Distribution")
        ax1.legend()

        # Bar Chart
        counts = sample_df['Habitat'].value_counts().reindex(groups.keys(), fill_value=0)
        # Colors: Beach(Sand), Jungle(Green), Wetlands(Teal), Caves(DarkGrey)
        colors = ['#E6D7A3', '#32CD32', '#00CED1', '#696969']
        
        ax2.bar(counts.index, counts.values, color=colors)
        ax2.set_title("Count by Habitat")
        ax2.set_ylabel("Number of Lizards")
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=15) # Tilt labels slightly
        
        st.pyplot(fig)

        # --- DOWNLOAD BUTTON ---
        csv = sample_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name='lizard_sample.csv',
            mime='text/csv',
        )