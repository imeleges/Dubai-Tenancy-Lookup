import pandas as pd
import streamlit as st
import altair as alt
import numpy as np

st.set_page_config(
    page_title="DTL - Dubai Tenancy Lookup",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# URL stored in secret place 😶‍🌫️
DATA_URL = st.secrets["DATA_URL"]

@st.cache_data
def load_data():
    data = pd.read_csv(DATA_URL, sep=';', parse_dates=["registration_date", "start_date","end_date"])
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data = data.astype({'ecn': 'int64', 'pid': 'int64', 'annual_amount': 'int64', 'contract_amount': 'int64'})
    return data


# Main page
st.title("Dubai Tenancy Lookup")
st.markdown("#### Access information about your tenancy contract and rented property")
st.markdown("""
            After entering your Ejari number, you'll be able to see:

            - All the properties registered under your Ejari number, including their ID, area or neighbourhood, building or complex, property size.
            - By accessing the history (prices from other tenants in the past) for each of your registered properties, you can track the fluctuations in rental prices over time and gain insights into the changing rental market in Dubai.
            - Details about your tenancy contract, including renting dates, type of contract, contract amount, and annual rent amount.

            With **Dubai Tenancy Lookup**, you can stay informed about your tenancy contract and the rental market in your area. It's a useful tool for tenants who want to have a clear overview of their rental history and ensure that they're paying a fair price for their property.
            """)

# Disclaimer
with st.expander("⚠️ Disclaimer"):
    st.markdown(""" 
    - The information provided on **Dubai Tenancy Lookup** is sourced from the Dubai Land Department (DLD) and is provided on an "as is" basis. While making every effort to ensure that the information in the database is accurate and up-to-date, there's no guarantee that it is free from errors or omissions.

    - In the event that you find any discrepancies in the information provided, such as missing dates of your contract or incorrect amounts, please be aware that **Dubai Tenancy Lookup** rely on the information provided by the DLD and do not have control over the accuracy or completeness of this data.

    - Also to emphasize that **Dubai Tenancy Lookup** is a tool for :red[**information purposes only**] and do not provide legal or financial advice, not responsible for any actions that you may take based on the information provided by this tool. You are solely responsible for verifying the information provided and for making any decisions based on that information.

    - **Dubai Tenancy Lookup** is not responsible for any damages or losses that may arise from the use of this tool or the information provided therein.
    """)


# Sidebar options
st.sidebar.title("Navigation")

ecn_field, ecn_message = st.columns([1.5,3])

with ecn_field:
    ecn = st.text_input('Enter your Ejari number', placeholder='000000000000000')
    if ecn != '':
        try:
            ecn = int(ecn)  # try to convert the variable to an integer
        except ValueError:  # if it's not convertible, catch the ValueError exception
            st.markdown(f"Oh no 😱 **:red[{ecn}]** is NOT a number")
            ecn = ''
with ecn_message:
    st.write("What is Ejari?")
    st.write("It's a unique ID number assigned to a registered tenancy contract in Dubai, and it consists of 15 digits.")


load_status = st.sidebar.warning('Wait, please. Loading all data and caching it for a quicker access later.')
data = load_data()
load_status.success('All data has been loaded successfully and cached!')

st.sidebar.markdown("#### Clear all cache!")
with st.sidebar.expander("🧹 Clear all cache!"):
    if st.button("clear and reload"):
        st.cache_data.clear()
        st.experimental_rerun()

def is_there(number,column):
    if np.isin(number, data[column].values):
        return True
    else:
        st.error(f"😢 Sorry, but **:red[{number}]** not found. ")
        return False

if ecn != '' and is_there(ecn,"ecn"):
    # Gathering all relevant data
    ecn_data = data[data['ecn'] == ecn]
    ecn_data = ecn_data.fillna("Missing Data")
    property_dict = {}

    pids = ecn_data['pid'].to_list()
    areas = ecn_data['area'].to_list()
    property_sizes = ecn_data['property_size'].to_list()
    projects = ecn_data['project'].to_list()

    for i in range(len(pids)):
        property_dict.update({
            pids[i]: {"area": areas[i],
                "property_size": property_sizes[i],
                "project": projects[i]
                }
            })
    
    
    # Building up the layout
    st.markdown(f"#### Data found for Ejari: **:green[{ecn}]**")
    
    # Display the table with ECN avalible in DB
    ecn_data.reset_index(drop=True, inplace=True)
    ecn_data_columns = ['ecn', 'registration_date', 'start_date', 'end_date', 'pid', 'version', 'area', 'contract_amount', 'annual_amount','property_size', 'project']
    st.dataframe(ecn_data[ecn_data_columns].style.format(precision=2, thousands=''), use_container_width=True)

    st.markdown("___")

    # Display the relevant information such as rented appartment, property size, building/complex, etc.
    st.markdown("#### Property")
    pid_title_1, pid_title_2, pid_title_3, pid_title_4, pid_title_5 = st.columns([1,1,1,1,0.5])

    with pid_title_1:
        st.markdown(f"**Property ID**")
    with pid_title_2:
        st.markdown(f"**Area / Neighbourhood**")
    with pid_title_3:
        st.markdown(f"**Building / Complex**")
    with pid_title_4:
        st.markdown(f"**Property Size (sq.m)**")
    with pid_title_5:
        st.markdown("**Price Chart**")

    for key in property_dict:
        pid_1, pid_2, pid_3, pid_4, pid_5 = st.columns([1,1,1,1,0.5])

        with pid_1:
            st.markdown(f":green[{key}]")
        with pid_2:
            if property_dict[key]['area'] == "Missing Data":
                st.markdown(f":red[{property_dict[key]['area']}]")
            else:
                st.markdown(f"{property_dict[key]['area']}")
        with pid_3:
            if property_dict[key]['project'] == "Missing Data":
                st.markdown(f":red[{property_dict[key]['project']}]")
            else:
                st.markdown(f"{property_dict[key]['project']}")
        with pid_4:
            if property_dict[key]['property_size'] == "Missing Data":
                st.markdown(f":red[{property_dict[key]['property_size']}]")
            else:
                st.markdown(f"{property_dict[key]['property_size']}")
        with pid_5:
            btn_showchart = st.button("show chart", key=f"PID_{key}")


    def pid_prices(pid):
        """Property renting prices chart"""

        pid_data = data[data['pid'] == pid]
        st.markdown(f"#### Renting prices for PID: :green[{pid}]")

        pidchart_title = f"Property renting prices"
        pid_altairchart = alt.Chart(pid_data).mark_line(point=alt.OverlayMarkDef(size=100, filled=False, fill="white")).encode(
            alt.X('start_date:T', title='Renting start dates'),
            alt.Y('annual_amount:Q', title='Annual amount'),
            tooltip=[
                alt.Tooltip('start_date:T', title='Start ranting date'),
                alt.Tooltip('end_date:T', title='End ranting date'),
                alt.Tooltip('annual_amount:Q', title='Annual amount', format=',.0f'),
                alt.Tooltip('contract_amount:Q', title='Contract amount', format=',.0f'),
                alt.Tooltip('version', title='New/Renewed'),
            ]
        ).properties(
            title=alt.TitleParams(
                text=pidchart_title,
                fontSize=16,
                color='gray'
            )
        )


        st.altair_chart(pid_altairchart, use_container_width=True)

    for item in st.session_state.items():
        if item[1]:
            pid_prices(int(item[0][4:]))
                

