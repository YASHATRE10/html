import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURATION & DATA ---
st.set_page_config(page_title="WHO-Based Energy Tracker", layout="wide")

# Data Sources: 
# 1. Mortality: Markandya & Wilkinson (2007) / Our World in Data (Deaths per TWh)
# 2. Emissions: IPCC / UNECE (gCO2eq per kWh)
# Note: These are global averages.
ENERGY_DATA = {
    "Coal": {"mortality": 24.62, "emissions": 820, "color": "#2c3e50"},  # Mortality per TWh, gCO2 per kWh
    "Oil": {"mortality": 18.43, "emissions": 720, "color": "#34495e"},
    "Natural Gas": {"mortality": 2.82, "emissions": 490, "color": "#7f8c8d"},
    "Biomass": {"mortality": 4.63, "emissions": 230, "color": "#d35400"},
    "Hydropower": {"mortality": 1.30, "emissions": 24, "color": "#2980b9"},
    "Wind": {"mortality": 0.04, "emissions": 11, "color": "#16a085"},
    "Nuclear": {"mortality": 0.03, "emissions": 12, "color": "#8e44ad"},
    "Solar": {"mortality": 0.02, "emissions": 45, "color": "#f1c40f"}
}

# --- HELPER FUNCTIONS ---
def calculate_impact(mix_dict, total_kwh):
    """
    Calculates total emissions (kg) and estimated mortality risk based on the mix.
    """
    total_emissions_kg = 0
    total_deaths_est = 0
    
    # Convert total user kWh to TWh for mortality calculation
    total_twh = total_kwh / 1_000_000_000
    
    for source, percentage in mix_dict.items():
        if percentage > 0:
            # Energy from this source
            source_kwh = total_kwh * (percentage / 100)
            source_twh = total_twh * (percentage / 100)
            
            # Emissions (g -> kg)
            emissions_g = source_kwh * ENERGY_DATA[source]["emissions"]
            total_emissions_kg += emissions_g / 1000
            
            # Mortality (Deaths per TWh * source TWh)
            total_deaths_est += source_twh * ENERGY_DATA[source]["mortality"]
            
    return total_emissions_kg, total_deaths_est

# --- UI LAYOUT ---

# Header
st.title("⚡ Clean Energy Transition Tracker")
st.markdown("""
This tool quantifies the health and environmental impact of your energy usage.
*Methodology:* Health metrics are based on *WHO-cited studies (Markandya & Wilkinson)* measuring premature deaths caused by air pollution and accidents per unit of energy.
""")

st.markdown("---")

# Sidebar: User Inputs
with st.sidebar:
    st.header("1. Your Energy Usage")
    monthly_usage = st.number_input("Monthly Electricity Usage (kWh)", value=500, step=50)
    
    st.header("2. Current Energy Mix (%)")
    st.caption("Adjust sliders to match your current grid source (must sum to 100).")
    
    coal_mix = st.slider("Coal", 0, 100, 40)
    gas_mix = st.slider("Natural Gas", 0, 100, 30)
    oil_mix = st.slider("Oil", 0, 100, 5)
    hydro_mix = st.slider("Hydropower", 0, 100, 10)
    solar_mix = st.slider("Solar/Wind", 0, 100, 10)
    nuclear_mix = st.slider("Nuclear", 0, 100, 5)
    
    current_mix = {
        "Coal": coal_mix,
        "Natural Gas": gas_mix,
        "Oil": oil_mix,
        "Hydropower": hydro_mix,
        "Solar": solar_mix, # Simplified for UI
        "Nuclear": nuclear_mix
    }
    
    total_mix = sum(current_mix.values())
    if total_mix != 100:
        st.error(f"Total mix is {total_mix}%. Please adjust to equal 100%.")
    else:
        st.success("Mix looks good!")

# Main Dashboard
if total_mix == 100:
    
    # --- CALCULATION ---
    # 1. Current Scenario
    curr_co2, curr_deaths = calculate_impact(current_mix, monthly_usage * 12) # Annualized
    
    # 2. Renewable Transition Scenario (100% Solar/Wind split)
    green_mix = {k:0 for k in current_mix}
    green_mix["Solar"] = 50
    green_mix["Wind"] = 50 # Adding wind implicitly for the 'green' scenario
    green_co2, green_deaths = calculate_impact(green_mix, monthly_usage * 12)

    # --- VISUALIZATION ---
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌍 Carbon Footprint (Annual)")
        delta_co2 = curr_co2 - green_co2
        st.metric(
            label="CO2 Emissions (kg)", 
            value=f"{curr_co2:,.0f}", 
            delta=f"-{delta_co2:,.0f} kg (if 100% Green)",
            delta_color="inverse"
        )
        st.info(f"Switching to renewables saves roughly *{delta_co2/1000:.1f} tonnes* of CO2 per year.")

    with col2:
        st.subheader("🫁 Health Impact (WHO Basis)")
        # Scaling up for visibility (Deaths per 100,000 people with this usage)
        # This is an abstraction to make the small numbers understandable
        risk_factor = (curr_deaths / green_deaths) if green_deaths > 0 else 0
        
        st.metric(
            label="Relative Mortality Risk", 
            value=f"{risk_factor:.1f}x Higher", 
            delta="High Risk",
            delta_color="inverse"
        )
        st.warning(f"Current mix has a *{risk_factor:.1f}x higher* associated death rate than solar/wind due to air pollution.")

    st.markdown("---")

    # Charts
    st.subheader("Interactive Comparisons")
    
    tab1, tab2 = st.tabs(["Comparison Chart", "Health Impact Analysis"])
    
    with tab1:
        # Data for chart
        plot_data = pd.DataFrame({
            "Scenario": ["Current Mix", "100% Renewable"],
            "CO2 Emissions (kg)": [curr_co2, green_co2],
            "Mortality Score (Normalized)": [curr_deaths, green_deaths]
        })
        
        # Create Bar Chart
        fig = go.Figure(data=[
            go.Bar(name='CO2 Emissions (kg)', x=plot_data['Scenario'], y=plot_data['CO2 Emissions (kg)'], marker_color='#e74c3c'),
            go.Bar(name='Health Risk Score', x=plot_data['Scenario'], y=plot_data['Mortality Score (Normalized)'], marker_color='#2E8B57')
        ])
        fig.update_layout(barmode='group', title="Annual Impact: Current vs. Renewable")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.write("### The Hidden Cost of Energy")
        st.write("The chart below compares the *Death Rate per TWh* of energy production. This is the standard metric used to evaluate energy safety.")
        
        # Prepare data for scatter plot
        source_names = list(ENERGY_DATA.keys())
        death_rates = [ENERGY_DATA[k]["mortality"] for k in source_names]
        colors = [ENERGY_DATA[k]["color"] for k in source_names]
        
        fig2 = px.bar(
            x=source_names, 
            y=death_rates, 
            color=source_names,
            color_discrete_sequence=colors,
            title="Deaths per TWh (Air Pollution & Accidents)",
            labels={'y': 'Deaths per TWh', 'x': 'Energy Source'}
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        st.caption("Data Source: Markandya & Wilkinson (2007); Sovacool et al. (2016); Our World in Data.")

else:
    st.info("Please adjust the sliders in the sidebar to equal 100% to see your results.")

# --- ACTIONABLE ADVICE ---
st.markdown("---")
st.subheader("💡 Campus Action Plan")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("*1. Audit*")
    st.write("Use smart plugs to identify 'phantom loads' in labs and dorms.")
with col_b:
    st.markdown("*2. Switch*")
    st.write("Advocate for campus administration to purchase 'Green Tariffs' from the grid.")
with col_c:
    st.markdown("*3. Optimize*")
    st.write("Implement 'Daylight Harvesting'—dimming lights when the sun is out.")