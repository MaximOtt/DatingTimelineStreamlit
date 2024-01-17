import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt # Plotting
import matplotlib.patches as patches # Background
import datetime as dt # Obviously for time data

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
    and randomly moved around a little. in the 'Customize' tab you have the option to define how certain people should be displayed.
    This is highly recommended if you want to create a visually appealing graph.
    """

    st.header("3: Download the results")
    """
    Once you are happy with the results, download the graph as .png or .svg. The latter format can be edited with, e.g., Inkscape to add labels.
    You can also download your data and your settings file if you plan on coming back and extending the graph,
    as I don't know how to securely save the data. 
    """

with st.expander("Upload/Download area"):
    "Upload data"
    "Download data"
    "Download graph"

tab1, tab2, tab3, tab4 = st.tabs(["Timeline", "Data", "Settings", "Customize"])

with tab2:
    uploaded_data_file = st.file_uploader("Choose a CSV file with your data", accept_multiple_files=False)

    df = pd.read_csv("poc.csv") # Dev only

    "This is your data"
    if uploaded_data_file is not None:
        df = pd.read_csv(uploaded_data_file)

    df = st.data_editor(df, use_container_width=True)

    df.person_name  = df.person_name.astype(str)
    df.kind  = df.kind.astype(str)
    df.start = pd.to_datetime(df.start)
    df.end =   pd.to_datetime(df.end)

with tab3:
    # Default appearance settings
    global_settings = {
        "year_font_size": 16,
        "month_font_size": 16,
        "date_dot_size": 10,
        "relationship_line_width": 10,
        "fplus_line_width": 10,
    }

    "Here you can customize the general appearance of the graph."
    for key, value in global_settings.items():
        global_settings[key] = st.number_input(
            f'`{key}`', step = 1, min_value= 1, 
            value = global_settings[key])

with tab4:
    "Here you can customize how each person is shown."

    uploaded_settings_file = st.file_uploader("Choose a CSV file with your settings", accept_multiple_files=False)

    st.markdown(
        """
        Here are all the individual people you have entered. For each of them you can set the following:
        * Color: Use one of the named colors: https://matplotlib.org/stable/gallery/color/named_colors.html
        * Offset: How much should the lines and dots be moved up (or down)
        * Size: Relative size of the date dots and width of the f+/relationship lines with respect to others
        """
    )
    if uploaded_settings_file is not None:
        df = pd.read_csv(uploaded_settings_file)
        st.write(df)
    else:
        st.write(df)

    "Here are all the circumstances you have entered."

    "Here are all the special activities you have participated in."


###############
#### GRAPH ####
###############
    
# Before drawing the graph, we need to extend the data df with the style df


with tab1:
    "Here is your timeline. You can upload, edit and download your data in the 'Data' tab."
    #############################
    ### Setting up the graph ####
    #############################
    # Find or set extreme values
    min_year = min(min(df.start),min(df.end)).year
    max_year = max(max(df.start),max(df.end)).year
    left =  dt.datetime(100, 1, 1).timetuple().tm_yday
    right = dt.datetime(100,12,31).timetuple().tm_yday

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 15))

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

    #########################
    ### Plotting the data ###
    #########################

    ### Long-term arrangements are plotted as lines
    # Filter and calculate helper columns
    lt_type = ['relationship', 'complicated']
    lt = df.query("kind in @lt_type").copy()
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
                    [year, year],
                    # [year - row.offset , year - offset],
                    solid_capstyle='round',
                    # linestyle=row.lines_tyle,
                    # lw = row.line_width,
                    # color = row.color
                )
            elif year == row.start_year:
                ax.plot(
                    [row.start_day, right],
                    [year, year],
                    # [year - row.offset , year - offset],
                    solid_capstyle='round',
                    # linestyle=row.lines_tyle,
                    # lw = row.line_width,
                    # color = row.color
                )
            elif year == row.end_year:
                ax.plot(
                    [left , row.end_day],
                    [year, year],
                    # [year - row.offset , year - offset],
                    solid_capstyle='round',
                    # linestyle=row.lines_tyle,
                    # lw = row.line_width,
                    # color = row.color
                )
            else:
                ax.plot(
                    [left , right],
                    [year, year],
                    # [year - row.offset , year - offset],
                    solid_capstyle='round',
                    # linestyle=row.lines_tyle,
                    # lw = row.line_width,
                    # color = row.color
                )


    ### Dates are plotted as dots
    # Filter and calculate helper columns
    dates = df.query("kind == 'date'").copy()
    dates["date_year"] = dates.start.dt.year
    dates["date_day"]  = dates.start.dt.dayofyear

    ax.scatter(dates.date_day, dates.date_year)


    st.pyplot(fig)