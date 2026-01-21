import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. SETUP & GLOBAL CONFIGURATION
# ==========================================
st.set_page_config(page_title="Lizard Sampling Simulation", layout="wide")

# Define the True Population Parameters (Global Scope)
# Format: 'Name': [Mean, SD, Count]
GROUPS = {
    'Beach':    [50,  5,   4000],  
    'Jungle':   [120, 15,  4000],  
    'Wetlands': [220, 30,  1500],  
    'Caves':    [350, 60,  500]    
}

# ==========================================
# 2. INTRODUCTION & DATA TABLE
# ==========================================
st.title("🦎 Island Lizard Weight Study")

st.markdown("""
**The goal of this study is to estimate the average weight of a population of lizards on a remote island.**

The lizard population has four subtypes, each with different characteristics and population sizes:
""")

# Create a display table for the students (using data from GROUPS)
# We map the simple keys to nicer display names for the table
display_data = []
display_names = {
    'Beach': 'Beach (Sandy)', 
    'Jungle': 'Jungle (Dense)', 
    'Wetlands': 'Wetlands (Swamp)', 
    'Caves': 'Caves (Deep)'
}

for key, params in GROUPS.items():
    display_data.append({
        "Lizard Type": display_names[key],
        "Mean Weight (g)": params[0],
        "Std Dev (g)": params[1],
        "Population Size": params[2]
    })

st.table(pd.DataFrame(display_data))

st.info("👈 **Configure your sampling strategy in the sidebar to begin.**")

# ==========================================
# 3. GENERATE POPULATION (Cached)
# ==========================================
@st.cache_data
def get_population():
    np.random.seed(101) 
    
    pop_list = []
    for name, params in GROUPS.items():
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
# 4. SIDEBAR CONTROLS
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
        n_caves = st.number