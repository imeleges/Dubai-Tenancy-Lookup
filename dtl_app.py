import pandas as pd
import streamlit as st
import altair as alt
import pydeck as pdk
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta

# Get the current date and time in format as "23 Mar 2023"
# current_date = datetime.datetime.now().strftime("%d %b %Y")

st.set_page_config(
    page_title = "DTL - Dubai Tenancy Lookup",
    page_icon = "🏠",
    layout = "wide",
    initial_sidebar_state = "expanded",
)

st.markdown('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.3/font/bootstrap-icons.css">', unsafe_allow_html=True)

# Custom colour set based on https://flatuicolors.com/palette/defo
colours = {
    "Turquoise": "#1abc9c",  # greenish blue
    "Emerald": "#2ecc71",  # bright green
    "Peter River": "#3498db",  # light blueish
    "Amethyst": "#9b59b6",  # purple
    "Wet Asphalt": "#34495e",  # dark grayish blue
    "Green Sea": "#16a085",  # blueish green
    "Nephritis": "#27ae60",  # bright greenish blue
    "Belize Hole": "#2980b9",  # darker blue than Peter River
    "Wisteria": "#8e44ad",  # purplish blue
    "Midnight Blue": "#2c3e50",  # dark blue
    "Sun Flower": "#f1c40f",  # bright yellow
    "Carrot": "#e67e22",  # orange
    "Alizarin": "#e74c3c",  # dark red
    "Clouds": "#ecf0f1",  # light gray
    "Concrete": "#95a5a6",  # gray
    "Orange": "#f39c12",  # orange
    "Pumpkin": "#d35400",  # orangey red
    "Pomegranate": "#c0392b",  # dark red
    "Silver": "#bdc3c7",  # light grayish blue
    "Asbestos": "#7f8c8d",  # dark gray
    "Cornflower Blue": "#6495ED",
}

# Making an icon, that should help to save some space in code.
def bi_icon(name, size, colour):
    return f"<i class='bi bi-{name}' style='font-size: {size}rem; color: {colour};'></i>"

# URL stored in secret place 😶‍🌫️
DATA_URL = st.secrets["DATA_URL"]
DATA_URL_PROJECTS = st.secrets["DATA_URL_PROJECTS"]

# Loading data and caching it
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_URL, sep = ',', parse_dates = ["registration_date", "start_date","end_date"])
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis = 'columns', inplace = True)
    
    data = data.astype({'ecn': 'int64',
                        'pid': 'int64', 
                        'annual_amount': 'int64', 
                        'contract_amount': 'int64', 
                        'property_size': 'float64'
                        })
    return data

@st.cache_data
def load_projects():
    projects = pd.read_csv(DATA_URL_PROJECTS, sep = ',', parse_dates = ["start_date", "completion_date"])
    lowercase = lambda x: str(x).lower()
    projects.rename(lowercase, axis = 'columns', inplace = True)

    return projects

# Adding a logo to the top left corner of the sidebar and hiding the menu and footer text
def add_logo():
    st.markdown(
        """
        <style>
            [class="css-6qob1r e1fqkh3o3"] {
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='cornflowerblue' class='bi bi-buildings' viewBox='0 0 16 16'%3E%3Cpath d='M14.763.075A.5.5 0 0 1 15 .5v15a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5V14h-1v1.5a.5.5 0 0 1-.5.5h-9a.5.5 0 0 1-.5-.5V10a.5.5 0 0 1 .342-.474L6 7.64V4.5a.5.5 0 0 1 .276-.447l8-4a.5.5 0 0 1 .487.022ZM6 8.694 1 10.36V15h5V8.694ZM7 15h2v-1.5a.5.5 0 0 1 .5-.5h2a.5.5 0 0 1 .5.5V15h2V1.309l-7 3.5V15Z'/%3E%3Cpath d='M2 11h1v1H2v-1Zm2 0h1v1H4v-1Zm-2 2h1v1H2v-1Zm2 0h1v1H4v-1Zm4-4h1v1H8V9Zm2 0h1v1h-1V9Zm-2 2h1v1H8v-1Zm2 0h1v1h-1v-1Zm2-2h1v1h-1V9Zm0 2h1v1h-1v-1ZM8 7h1v1H8V7Zm2 0h1v1h-1V7Zm2 0h1v1h-1V7ZM8 5h1v1H8V5Zm2 0h1v1h-1V5Zm2 0h1v1h-1V5Zm0-2h1v1h-1V3Z'/%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-size: 7em;
                padding-top: 50px;
                background-position: center 20px;
            }

            # [class="css-6qob1r e1fqkh3o3"]::before {
            #     content: "Navigation";
            #     margin-left: 20px;
            #     margin-top: 20px;
            #     font-size: 30px;
            #     position: relative;
            #     top: 100px;
            # }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Drawing measure mean/median rule
def rule_onchart(df, column, measure):
    rule = alt.Chart(df).mark_rule(color = colours['Pomegranate'] if measure == 'median' else colours['Orange']).encode(
        y = f"{measure}({column}):Q",
        size = alt.value(2),
        tooltip = [
            alt.Tooltip(f"{measure}({column}):Q", title=f"{measure.capitalize()}", format = ',.0f')
        ]
    )
    return rule

# Drawing a bar chart with a median line and highlighting the active bar with a different colour
def building_properties_size(building_name, size, usage):
    df = data[(data['project'] == building_name) & (data['usage'] == usage)].copy()
    df.reset_index(drop=True, inplace=True)

    median_str = '{:,.0f}'.format(np.median(df['annual_amount']))
    mean_str = '{:,.0f}'.format(np.mean(df['annual_amount']))

    st.markdown(f"##### Property size for building/complex: {building_name}")
    st.caption(f" {bi_icon('square-fill', 1, colours['Pomegranate'])} Median {median_str} &nbsp;|&nbsp; {bi_icon('square-fill', 1, colours['Orange'])} Mean {mean_str}", unsafe_allow_html=True)

    bar = alt.Chart(df).mark_bar().encode(
        x = alt.X('property_size:O',
                # bin=alt.Bin(extent=[df['property_size'].min(), df['property_size'].max()], step=10),
                sort = 'ascending',
                axis = alt.Axis(labelAngle = 0),
                title = "Property size (sq.m)"
                ),
        y = alt.Y('median(annual_amount):Q', title = "Annual price [MEDIAN]"),
        tooltip = [
                    alt.Tooltip('median(annual_amount):Q', title = 'Median Annual amount', format = ',.0f'),
                    alt.Tooltip('property_size:O', title = 'Property size (sq.m)'),
                    alt.Tooltip('count()', title = 'Number of observations')
                ],
        color = alt.condition(
            alt.datum.property_size == size,
            alt.value(colours['Nephritis']), 
            alt.value(colours['Peter River']))
    )

    count = alt.Chart(df).mark_bar(color = 'grey').encode(
        x = alt.X('property_size:O', sort = 'ascending'),
        y = 'count()'
    )

    st.altair_chart((bar 
                     + rule_onchart(df, 'annual_amount', 'median') 
                     + rule_onchart(df, 'annual_amount', 'mean') 
                     + count), use_container_width=True)

# Drawing a bar chart with a mean line for properties with similar size and highlighting the active bar with a different colour
def building_properties_similar(building_name, size, usage):
    df = data[(data['project'] == building_name) & (data['usage'] == usage) & (data['property_size'].between(size - 10, size + 10))].copy()
    df.reset_index(drop=True, inplace=True)

    median_str = '{:,.0f}'.format(np.median(df['annual_amount']))
    mean_str = '{:,.0f}'.format(np.mean(df['annual_amount']))

    st.markdown(f"##### Prices for similar property size (+/- 10 sq.m) in: {building_name}")
    st.caption(f" {bi_icon('square-fill', 1, colours['Pomegranate'])} Median {median_str} &nbsp;|&nbsp; {bi_icon('square-fill', 1, colours['Orange'])} Mean {mean_str}", unsafe_allow_html=True)

    bar = alt.Chart(df).mark_bar().encode(
        x = alt.X('property_size:O',
                sort = 'ascending',
                axis = alt.Axis(labelAngle = 0),
                title = "Property size (sq.m)"
                ),
        y = alt.Y('mean(annual_amount):Q', title = "Annual price [MEAN]"),
        tooltip = [
                    alt.Tooltip('mean(annual_amount):Q', title = 'Mean Annual amount', format = ',.0f'),
                    alt.Tooltip('property_size:O', title = 'Property size (sq.m)'),
                    alt.Tooltip('count()', title = 'Number of observations')
                ],
        color = alt.condition(
            alt.datum.property_size == size,
            alt.value(colours['Nephritis']), 
            alt.value(colours['Peter River']))
     )

    count = alt.Chart(df).mark_bar(color = 'gray').encode(
        x = alt.X('property_size:O', sort = 'ascending'),
        y = 'count()'
    )

    st.altair_chart((bar 
                     + rule_onchart(df, 'annual_amount', 'mean') 
                     + rule_onchart(df, 'annual_amount', 'median') 
                     + count), use_container_width = True)
    
# Property renting prices chart
def pid_prices(pid):
    """Property renting prices chart"""

    pid_data = data[data['pid'] == pid]
    
    pidchart_title = f"Property renting prices for all avalible period"
    pid_altairchart = alt.Chart(pid_data).mark_line(point = alt.OverlayMarkDef(size = 100, filled = False, fill = "white")).encode(
        alt.X('start_date:T', title = 'Renting start dates'),
        alt.Y('annual_amount:Q', title = 'Annual amount'),
        tooltip=[
            alt.Tooltip('start_date:T', title = 'Start ranting date'),
            alt.Tooltip('end_date:T', title = 'End ranting date'),
            alt.Tooltip('annual_amount:Q', title = 'Annual amount', format = ',.0f'),
            alt.Tooltip('contract_amount:Q', title = 'Contract amount', format = ',.0f'),
            alt.Tooltip('version', title = 'New/Renewed'),
        ]
    ).properties(
        title = alt.TitleParams(
            text = pidchart_title,
            fontSize = 16,
            color = 'gray'
        )
    )

    text = pid_altairchart.mark_text(
        align = "left",
        baseline = "middle",
        fontSize = 13,
        dx = 8,
        dy = -15,
        color = '#fff'
    ).encode(text = "annual_amount:Q")

    st.altair_chart(pid_altairchart + text, use_container_width = True)

add_logo()

# Main page
st.markdown(f"# {bi_icon('buildings', 3, colours['Cornflower Blue'])} Dubai Tenancy Lookup", unsafe_allow_html=True)
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
st.sidebar.caption(f"App updated: 27 March 2023")

ecn_field, ecn_message = st.columns([1.5,3])

if 'ecn' not in st.session_state:
    st.session_state['ecn'] = ''

with ecn_field:
    entered_ecn = st.text_input('Enter your Ejari number', placeholder='000000000000000')
    if entered_ecn != '':
        try:
            st.session_state['ecn'] = int(entered_ecn)  # try to convert the variable to an integer
        except ValueError:  # if it's not convertible, catch the ValueError exception
            st.markdown(f"Oh no 😱 **:red[{entered_ecn}]** is NOT a number")
            st.session_state['ecn'] = ''

with ecn_message:
    st.write("What is Ejari?")
    st.write("It's a unique ID number assigned to a registered tenancy contract in Dubai, and it consists of 15 digits.")


load_status = st.sidebar.warning('Wait, please. Loading all data and caching it for a quicker access later.')
data = load_data()
projects = load_projects()
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
        st.error(f"😢 Sorry, but Ejari number **:red[{number}]** is not found. ")
        return False


def period_between_dates(dataframe, start_date_column, end_date_column):
    # get the minimum and maximum dates from the specified columns
    min_date = dataframe[start_date_column].min()
    max_date = dataframe[end_date_column].max()

    # if the maximum date is in the future, use the current date instead
    if max_date > datetime.datetime.now():
        max_date = datetime.datetime.now()

    # calculate the period between the minimum and maximum dates using dateutil.relativedelta
    delta = relativedelta(max_date, min_date)
    years = delta.years
    months = delta.months
    days = delta.days

    # return a formatted string with the period between the minimum and maximum dates
    return f"{years} years {months} months {days} days"

ecn_exist = st.session_state['ecn'] != '' and is_there(st.session_state['ecn'],"ecn")

if ecn_exist:
    # Gathering all relevant data
    ecn_data = data[data['ecn'] == st.session_state['ecn']].copy()
    ecn_data.fillna("Missing Data", inplace = True)
    ecn_data = ecn_data.reset_index(drop=True)

    property_dict = {
        "start_date": ecn_data['start_date'].min().strftime('%d %b %Y'),
        "end_date": ecn_data['end_date'].max().strftime('%d %b %Y'),
        "pid": ecn_data['pid'].iloc[0],
        "area": ecn_data['area'].iloc[0],
        "property_size": ecn_data['property_size'].iloc[0],
        "usage": f"{ecn_data['usage'].iloc[0]}",
        "project": f"{ecn_data['project'].iloc[0]}",
        "property_type": f"{ecn_data['property_type'].iloc[0]}",
        "property_subtype": f"{ecn_data['property_subtype'].iloc[0]}",
        "nearest_metro": f"{ecn_data['nearest_metro'].iloc[0]}",
        "nearest_mall": f"{ecn_data['nearest_mall'].iloc[0]}",
    }

    # Building up the layout
    st.markdown(f"#### Data found for Ejari: **:green[{st.session_state['ecn']}]**")
    
    # Display the table with ECN avalible in DB
    ecn_data.reset_index(drop = True, inplace = True)
    # st.dataframe(ecn_data.style.format(precision = 2, thousands = ''), use_container_width = True)
    st.markdown("___")

    # Displaying relevant information such as rented apartments, property size, building/complex, etc.
    st.markdown(f"#### {bi_icon('card-checklist', 1.5, colours['Concrete'])} Property overview", unsafe_allow_html=True)

    property_ttl_1, property_ttl_2, property_ttl_3, property_ttl_4, property_ttl_5 = st.columns([1.5,1,1,1,1])

    def if_missing(column):
        if property_dict[column] == "Missing Data":
            st.markdown(f":red[{property_dict[column]}]")
        else:
            st.markdown(f"{property_dict[column]}")

    with property_ttl_1:
        st.markdown(f"**Renting dates**")
        st.markdown(f"""{bi_icon('dot', 1, colours['Emerald'])} {property_dict['start_date']} 
                        {bi_icon('dot', 1, colours['Alizarin'])} {property_dict['end_date']}  
                    """, unsafe_allow_html=True) 
    with property_ttl_2:
        st.markdown(f"**Usage**")
        if_missing("usage")
    with property_ttl_3:
        st.markdown(f"**Type**")
        if_missing("property_type")
    with property_ttl_4:
        st.markdown(f"**Subtype**")
        if_missing("property_subtype")
    with property_ttl_5:
        st.markdown(f"**Property Size (sq.m)**")
        if_missing("property_size")
    st.markdown("")

if ecn_exist:
    st.markdown(f"#### {bi_icon('bar-chart', 1.5, colours['Concrete'])} Property renting prices", unsafe_allow_html=True)
    pid_prices(property_dict['pid'])

# Building
if ecn_exist and property_dict['project'] != "Missing Data":
    st.markdown(f"#### {bi_icon('info-square', 1.5, colours['Concrete'])} Building's Information for {property_dict['project']}", unsafe_allow_html=True)

    current_project = projects[projects['project_name'] == property_dict['project']].copy()

    project_dict = {
        "project_name": current_project['project_name'].iloc[0],
        "developer_name": current_project['developer_name'].iloc[0],
        "start_date": current_project['start_date'].iloc[0].strftime('%d %b %Y'),
        "completion_date": current_project['completion_date'].iloc[0].strftime('%d %b %Y'),
        "area": current_project['area'].iloc[0],
        "total_units": f"{current_project['total_units'].fillna(0).astype(int).iloc[0]}",
        "lat": f"{float(current_project['lat'].iloc[0])}",
        "long": f"{float(current_project['long'].iloc[0])}",
    }
     
    # Description & Map
    bld_decription, bld_map = st.columns([1,2])
    with bld_decription: 
        st.markdown(f"##### {bi_icon('building', 1, colours['Concrete'])} **Building description**", unsafe_allow_html=True)
        st.markdown(f"""
            Developer: **{project_dict['developer_name']}**\n
            Construction dates: **{project_dict['start_date']} - {project_dict['completion_date']}**\n
            Total units: **{project_dict['total_units'] if project_dict['total_units'] != 0 else ":red[Missing Data]"}**\n
            Transport station: **{property_dict['nearest_metro']}**\n
            Shopping centre: **{property_dict['nearest_mall']}**\n
            Area: **{project_dict['area'] if project_dict['area'] != 0 else ":red[Missing Data]"}**\n
            """ , unsafe_allow_html=True)
    with bld_map:
        def map_location(lat, long):
            st.pydeck_chart(pdk.Deck(
                map_style = 'mapbox://styles/mapbox/dark-v11',
                initial_view_state = pdk.ViewState(
                    latitude = 25.0813566,
                    longitude = 55.1364633,
                    zoom = 12.5,
                    height = 300,
                    # width = 300
                ),
                layers=[
                    pdk.Layer(
                        'ScatterplotLayer',
                        data = current_project,
                        get_position = '[long, lat]',
                        get_color = '[39, 174, 96, 160]',
                        get_radius = 100,
                        auto_highlight = True
                    ),
                ],
            ))
        
        map_location(project_dict['lat'], project_dict['long'])


if ecn_exist and property_dict['project'] != "Missing Data":
    building_properties_size(property_dict['project'],property_dict['property_size'],property_dict['usage'])
    building_properties_similar(property_dict['project'],property_dict['property_size'],property_dict['usage'])
elif ecn_exist and property_dict['project'] == "Missing Data":
    st.markdown(f"Sorry, but building's :red[info is missing] for the property. There's nothing to show 😢")

st.markdown("___")
