import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt # Plotting
import matplotlib.patches as patches # Background
import matplotlib.patheffects as pe
import seaborn as sns
import datetime as dt # Obviously for time data
from itertools import cycle
from dodger import calculate_offsets
import numpy as np

with st.sidebar:
    st.title("Your Dating Timeline")
    """
    If you want to see all your 'slutventures' in one simple graph, this is the app for you!
    """
    st.title("How to use")

    st.header("1: Enter your data")
    """
    If you have a .csv file with your data (e.g., from the last time you used this app), go ahead and upload it in the data tab.
    If this is your first time, you can simply start entering the data row by row there.
    """

    st.header("2: Customize the appearance")
    """
    Sometimes many things happen at once. To tell the individual people apart, all of them will be assigned colors automatically
    and moved around a little. In the 'Customize' tab you then have the option to redefine how certain people should be displayed.
    This is highly recommended if you want to create a visually appealing graph.
    """

    st.header("3: Download the results")
    """
    Once you are happy with the results, download the graph as .png or .svg. The latter format can be edited with, e.g., Inkscape to add labels.
    You should also download your data and your settings file if you plan on coming back and extending the graph,
    as I don't know how to securely save the data. 
    """

with st.expander("Upload/Download area"):
    "Upload everything at once"
    "Download everything at once"
    "Download graph"

tab1, tab2, tab3, tab4 = st.tabs(["Timeline", "Data", "Settings", "Customize"])

with tab2:
    uploaded_data_file = st.file_uploader("Choose a CSV file with your data", accept_multiple_files=False)

    if uploaded_data_file is not None:
        "This is your data:"
        df = pd.read_csv(uploaded_data_file)
    else:
        "Here is some example data:"
        df = pd.read_csv("maxim_people.csv")

    df.start = pd.to_datetime(df.start)
    df.end   = pd.to_datetime(df.end)

    column_config_dict = {
        "person_name": "Name",
        "kind": st.column_config.SelectboxColumn(
            "Category",
            help="""
            Select one. Dates are plotted as dots, longterm arrangements as lines.
            """,
            # width="medium",
            options=[
                "Date",
                "Longterm"
            ],
            required=True,
        ),
        "stage": st.column_config.SelectboxColumn(
            "Stage",
            help="""
            Select one that goes with the category. 
            Dates are plotted as following: 
                No action - Small dot
                Kiss      - Empty circle
                Sex       - Filled circle
            Longtermn arrangements are plotted as following:
                FWB          - Thin dashed line
                Complicated  - Thin solid line with dots on top
                Relationship - Thick solid line
            """,
            # width="medium",
            options=[
                "No action",
                "Kiss",
                "Sex",
                "FWB",
                "Complicated",
                "Relationship",
            ],
            required=True,
        ),
        "start": st.column_config.DateColumn(
            "From/At",
            help="""
            Day of the date or start of the longterm arrangement (stage).
            """,
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date(2030, 1, 1),
            format="DD.MM.YYYY",
            step=1,
        ),
        "end": st.column_config.DateColumn(
            "To",
            help="""
            End of the longterm arrangement (stage). Ignored for dates.
            """,
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date(2030, 1, 1),
            format="DD.MM.YYYY",
            step=1,
        ),
    }
    df = st.data_editor(df, use_container_width=True, column_config=column_config_dict, num_rows='dynamic')

    df.person_name  = df.person_name.astype(str)
    df.kind  = df.kind.astype(str)
    df.start = pd.to_datetime(df.start)
    df.end =   pd.to_datetime(df.end)





    uploaded_circumstances_file = st.file_uploader("Choose a CSV file defining some special circumstances", accept_multiple_files=False)

    if uploaded_circumstances_file is not None:
        "This is your data:"
        circumstances = pd.read_csv(uploaded_circumstances_file)
    else:
        "Here is some example data:"
        circumstances = pd.read_csv("maxim_circumstances.csv")

    circumstances.start = pd.to_datetime(circumstances.start)
    circumstances.end   = pd.to_datetime(circumstances.end)

    if 'circumstances' not in st.session_state:
        st.session_state.circumstances = circumstances
    else:
        circumstances = st.session_state.circumstances

    circumstances_column_config = {
        "situation": st.column_config.TextColumn(label="Situation", required=True),
        "start": st.column_config.DateColumn(
            "From/At",
            help="""
            Beginning of whatever happened.
            """,
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date(2030, 1, 1),
            format="DD.MM.YYYY",
            step=1,
            required=True
        ),
        "end": st.column_config.DateColumn(
            "To",
            help="""
            End of whatever happened.
            """,
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date(2030, 1, 1),
            format="DD.MM.YYYY",
            step=1,
            required=True
        ),
    }
    circumstances = st.data_editor(circumstances, use_container_width=True, column_config=circumstances_column_config, num_rows='dynamic')


    uploaded_specials_file = st.file_uploader("Choose a CSV file with your 'special' activities", accept_multiple_files=False)

    if uploaded_specials_file is not None:
        "This is your data:"
        specials = pd.read_csv(uploaded_specials_file)
    else:
        "Here is some example data:"
        specials = pd.read_csv("maxim_specials.csv")

    specials.start = pd.to_datetime(specials.start)

    if 'specials' not in st.session_state:
        st.session_state.specials = specials
    else:
        specials = st.session_state.specials

    specials_column_config = {
        "special": st.column_config.TextColumn(label="Label", required=True),
        "kind": st.column_config.TextColumn(label="Category", help="Usually FFM or MMF thresomes woud go here, but you can define your own categories", required=True),
        "start": st.column_config.DateColumn(
            "Date",
            help="""
            Day of whatever happened.
            """,
            min_value=dt.date(1900, 1, 1),
            max_value=dt.date(2030, 1, 1),
            format="DD.MM.YYYY",
            step=1,
            required=True
        ),
    }
    specials = st.data_editor(specials, use_container_width=True, column_config=specials_column_config, num_rows='dynamic')



with tab3:
    # Default appearance settings
    global_settings = {
        "year_font_size": 20,
        "month_font_size": 16,
        "date_dot_size": 10,
        "relationship_line_width": 4,
        "fplus_line_width": 2,
        "dodge_step_size": 0.08,
        "dodge_dates_days": 5
    }

    "Here you can customize the general appearance of the graph."
    for key, value in global_settings.items():
        if isinstance(global_settings[key],int):
            global_settings[key] = st.number_input(
                f'`{key}`', step = 1, min_value= 1, 
                value = global_settings[key])
        elif isinstance(global_settings[key],float):
            global_settings[key] = st.number_input(
                f'`{key}`', step = 0.01, min_value= 0.0, 
                value = global_settings[key])

with tab4:
    "Here you can customize how each person is shown."

    st.markdown(
        """
        First, please select the level of detail for the dates (longterm arrangements are always plotted).
        Please note: Changing the filter will currently erase all your inputs.
        """
    )

    show_dates = st.radio(
        "What kind of dates would you like to see in the graph?",
        ["All", "Kiss", "Sex"],
        captions = ["Show all dates.", "Show only dates where there was at least a kiss.", "Show only dates where you had sex."])

    st.markdown(
        """
        Here are all the individual people you have entered that you had a longterm arrangement or more than one date remaining after applying the filter.
        For each of them you can set the following:
        * Color: Use one of the named colors: https://matplotlib.org/stable/gallery/color/named_colors.html
        * Offset: How much should the lines and dots be moved up (or down)
        """
    )
    if show_dates == "All":
        filtered_df = df
        removed_people = [] 
    elif show_dates == "Kiss":
        filtered_df = df[df.stage != "No action"]
        removed_people = list(df[df.stage == "No action"].person_name.unique())
    elif show_dates == "Sex":
        filtered_df = df[~((df.stage == "Kiss") | (df.stage == "No action"))]
        removed_people = list(df[(df.stage == "Kiss") | (df.stage == "No action")].person_name.unique())

    colored_persons = list(filtered_df[filtered_df.kind == "Longterm"].person_name.unique())
    colored_persons.extend(list(filtered_df[filtered_df.kind == "Date"].groupby("person_name").filter(lambda x: len(x) > 1).person_name.unique()))
    ons = set(filtered_df.person_name) - set(colored_persons)

    with st.expander("Some or all entries for these people will not be shown"):
        removed_people = sorted(removed_people)
    with st.expander("These people will be colored grey"):
        ons = sorted(list(ons))

    if 'person_settings' not in st.session_state:
        person_settings = pd.DataFrame(columns=['person_name','color'])
        person_settings.person_name = colored_persons + ons
        person_settings = person_settings.merge(
            calculate_offsets(filtered_df, global_settings["dodge_dates_days"])[['person_name', 'offset']],
            how = 'left',
            on = 'person_name'
        )
        
        person_settings.offset = person_settings.offset.fillna(0)

        kelly_upgrade = [
            '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4',
            '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff',
            '#9a6324', '#800000', '#aaffc3', '#808000', '#ffd8b1',
            '#000075', '#808080']
        kelly = cycle(kelly_upgrade)
        person_settings.color = person_settings.color.apply(lambda x: next(kelly))
        
        person_settings.loc[(person_settings['person_name'].isin(ons)), 'color'] = 'grey'
    
        st.session_state.person_settings = person_settings
    else:
        person_settings = st.session_state.person_settings

    settings_column_config = {
        "person_name": "Name",
        "offset": st.column_config.NumberColumn(label="Offset", help="Leave empty to use a random value.", step=1),
        "color": st.column_config.TextColumn(label="Color", help="Leave empty to pick automatically.")
    }

    person_settings = st.data_editor(person_settings, use_container_width=True, column_config=settings_column_config)

    st.markdown(
        """
        Here are all the circumstances you have described. For each of them you can set the following:
        * Color: Use one of the named colors: https://matplotlib.org/stable/gallery/color/named_colors.html
        """
    )

    st.markdown(
        """
        Here are all the special activities. For each of them you can set the following:
        * Symbol: Allow upload?
        * Size: Relative size of the with respect to the date dots
        """
    )



###############
#### GRAPH ####
###############
    
# Before drawing the graph, we need to extend the data df with the style df


with tab1:
    "Here is your timeline. You can upload, edit and download your data in the 'Data' tab."
    #############################
    ### Setting up the graph ####
    #############################
    sns.set(style="whitegrid")

    # Find or set extreme values
    min_year = df.start.min().year
    max_year = max(df.start.max(),df.end.max()).year
    left =  dt.datetime(100, 1, 1).timetuple().tm_yday
    right = dt.datetime(100,12,31).timetuple().tm_yday

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 15))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(False)

    # Set limits
    plt.xlim([-5, 370])
    plt.ylim([min_year-0.5, max_year+0.5])

    # Set year ticks (labels are fine automatically)
    plt.yticks(range(min_year,max_year+1), fontsize = global_settings["year_font_size"])
    # Set month ticks and labels
    first_of_month = [dt.datetime(1,n,1).timetuple().tm_yday for n in range(1,13)]
    plt.xticks(first_of_month + [365],) # Set tick locations at the first of each month and end of year (ignoring leap years)
    ax.set_xticklabels('') # Hide automatic (number of day in the year) labels
    middle_of_month = [day + 15 for day in first_of_month] # Good enough
    ax.set_xticks(middle_of_month, minor=True) # Set minor ticks locations between the month 
    ax.tick_params(axis='x', which='minor', size=0) # Hide them from view
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'], minor=True, fontsize = global_settings["month_font_size"])

    # Years should go from top to bottom
    ax.invert_yaxis()

    ###############################################
    ### Enrich the data with offsets and colors ###
    ###############################################
    # Merge colors and offsets
    plot_df = df.merge(person_settings, on="person_name", how="left")
    # Set line width
    plot_df["line_width"] = global_settings["fplus_line_width"]
    plot_df.loc[(plot_df['stage'] == 'Relationship'), 'line_width'] = global_settings["relationship_line_width"]
    # Set line style
    plot_df["line_style"] = 'solid'
    plot_df.loc[(plot_df['stage'] == 'FWB'), 'line_style'] = 'dashed'
    
    

    #########################
    ### Plotting the data ###
    #########################
    offset_step = global_settings["dodge_step_size"]

    ### Long-term arrangements are plotted as lines
    # Filter and calculate helper columns
    lt = plot_df.query("kind == 'Longterm'").copy()
    lt["start_year"] = lt.start.dt.year
    lt["start_day"]  = lt.start.dt.dayofyear
    lt["end_year"]   = lt.end.dt.year
    lt["end_day"]    = lt.end.dt.dayofyear

    # There are 4 options for arrangements:
    #   - Started and ended in the same year (simplest case)
    #   - Started in a certain year, but continued past the end of it
    #   - Started before a certain year, but ended in it
    #   - Started and ended in other years, so lasts through the whole year
    for index, row in lt.iterrows():
        for year in range(row.start_year, row.end_year + 1):
            if row.start_year == row.end_year:
                ax.plot(
                    [row.start_day , row.end_day],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.color,
                    zorder = 0
                )
            elif year == row.start_year:
                ax.plot(
                    [row.start_day, right],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.color,
                    zorder = 0
                )
            elif year == row.end_year:
                ax.plot(
                    [left , row.end_day],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.color,
                    zorder = 0
                )
            else:
                ax.plot(
                    [left , right],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.color,
                    zorder = 0
                )


    ### Dates are plotted as dots
    # Filter and calculate helper columns
    dates = plot_df.query("kind == 'Date'").copy()
    dates["date_year"] = dates.start.dt.year
    dates["date_day"]  = dates.start.dt.dayofyear

    for index, row in dates.iterrows():
        ax.scatter(
            row.date_day, row.date_year + row.offset*offset_step,
            color = row.color,
            zorder = 1
        )

    # Add background patches for the defined situations
    for index, row in circumstances.iterrows():
        for year in range(row.start.year, row.end.year +1 ):
            if row.start.year == row.end.year:
                ax.fill_between(
                    range(row.start.dayofyear,row.end.dayofyear), year-0.45, year+0.45,
                    color = row.color,
                    zorder = -10)
            elif year == row.start.year:
                ax.fill_between(
                    range(row.start.dayofyear,365), year-0.45, year+0.45,
                    color = row.color,
                    zorder = -10)
            elif year == row.end.year:
                ax.fill_between(
                    range(0,row.end.dayofyear), year-0.45, year+0.45,
                    color = row.color,
                    zorder = -10)
            else:
                ax.fill_between(
                    range(0,365), year-0.45, year+0.45,
                    color = row.color,
                    zorder = -10)

    # Add alternating patches in the background
    for year in range(min_year, max_year +1 ):
        ax.fill_between(
            range(0,366), year-0.45, year+0.45,
            color = '#e1e1e1' if year % 2 == 0 else '#ebebeb',
            zorder = -99)

    st.pyplot(fig)