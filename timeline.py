import streamlit as st
import glob
import pandas as pd
import matplotlib.pyplot as plt # Plotting
import matplotlib.patches as patches # Background
import matplotlib.patheffects as pe
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import seaborn as sns
import datetime as dt # Obviously for time data
from itertools import cycle
from dodger import calculate_offsets
import zipfile

######################################
### Prepare some things in advance ###
######################################
# Default appearance settings
global_settings = {
    "year_font_size": 20,
    "month_font_size": 16,
    "date_dot_size": 10,
    "relationship_line_width": 4,
    "fplus_line_width": 2,
    "dodge_step_size": 0.12,
    "dodge_dates_days": 5
}

# Read symbol images
symbols = {image_file: plt.imread(image_file) for image_file in glob.glob('symbols/*.png')}
symbol_boxes = {key: OffsetImage(image, zoom=0.02) for key, image in symbols.items()}
symbol_keys = [key for key, image in symbols.items()]
symbol_key = cycle(symbol_keys)

# Set color cycles
bg_colors = [
    'xkcd:light pink',
    'xkcd:pale',
    'xkcd:pale blue',
    'xkcd:very pale green',
    'xkcd:egg shell',
    'xkcd:pale peach',
    'xkcd:light sky blue'
]
bg_color = cycle(bg_colors)

color_list = [
    'xkcd:dull purple', 'xkcd:umber', 'xkcd:golden yellow', 'xkcd:pale teal', 'xkcd:pinky red', # 5
    'xkcd:bronze', 'xkcd:bluish', 'xkcd:vermillion', 'xkcd:sickly green', 'xkcd:cranberry', # 10
    'xkcd:barney', 'xkcd:watermelon', 'xkcd:easter purple', 'xkcd:darkish green', 'xkcd:tomato', # 15
    'xkcd:greeny blue', 'xkcd:pastel red', 'xkcd:topaz', 'xkcd:burple', 'xkcd:maroon', # 20 
    'xkcd:olive', 'xkcd:forest green', 'xkcd:periwinkle', 'xkcd:lime', 'xkcd:lilac', # 25
    'xkcd:royal purple', 'xkcd:light orange', 'xkcd:cerulean', 'xkcd:kelly green', 'xkcd:puke green', # 30
]
color = cycle(color_list)

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

with st.expander("Upload everything at once"):
    uploaded_people = st.file_uploader("Choose a file containing data about all relationships, dates, etc.", accept_multiple_files=False)
    if uploaded_people is not None:
        uploaded_people_df = pd.read_csv(uploaded_people)
        st.write(uploaded_people_df)
    else:
        uploaded_people_df = None

    uploaded_specials = st.file_uploader("Choose a file containing data about all 'special activities' you took part in, like ,e.g., threesomes.", accept_multiple_files=False)
    if uploaded_specials is not None:
        uploaded_specials_df = pd.read_csv(uploaded_specials)
        st.write(uploaded_specials_df)
    else:
        uploaded_specials_df = None

    uploaded_circumstances = st.file_uploader("Choose a file containing data about all relevant circumstances, like being abroad.", accept_multiple_files=False)
    if uploaded_circumstances is not None:
        uploaded_circumstances_df = pd.read_csv(uploaded_circumstances)
        st.write(uploaded_circumstances_df)
    else:
        uploaded_circumstances_df = None


tab1, tab2, tab3, tab4 = st.tabs(["Timeline", "Data", "Settings", "Customize"])

with tab2:
    st.write(
        "Please use the 'Upload' expander at the top of this page to upload your data, or clear the example data by clicking on the button below and enter everything manually."
    )
    st.warning(
        "Make sure to download your data regularly, as refreshing the page might delete all your progress!"
    )

    clear_example_data = st.button('Clear example data')
    
    if clear_example_data:
        "This is your data:"
    else:
        "Here is some example data:"

    ###############
    ### Persons ###
    ###############
    if uploaded_people_df is not None:
        df = uploaded_people_df
    else:
        if clear_example_data:
            df = pd.read_csv("maxim_people.csv", nrows=0)
        else:
            df = pd.read_csv("maxim_people.csv")

    df.start = pd.to_datetime(df.start)
    df.end   = pd.to_datetime(df.end)    
    df.person_name  = df.person_name.astype(str)
    df.kind  = df.kind.astype(str)
    df.start = pd.to_datetime(df.start)
    df.end =   pd.to_datetime(df.end)

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
    if "df" not in st.session_state:
        st.session_state["df"] = df
    else:
        df = st.session_state["df"]

    ################
    ### Specials ###
    ################
    if uploaded_specials_df is not None:
        specials = uploaded_specials_df
    else:
        if clear_example_data:
            specials = pd.read_csv("maxim_specials.csv", nrows=0)
        else:
            specials = pd.read_csv("maxim_specials.csv")

    specials.start = pd.to_datetime(specials.start)

    # if 'specials' not in st.session_state:
    #     st.session_state.specials = specials
    # else:
    #     specials = st.session_state.specials

    specials_column_config = {
        "special": st.column_config.TextColumn(label="Label", help="Brief note to act as unique ID", required=True),
        "kind": st.column_config.TextColumn(label="Category", help="Usually FFM or MMF thresomes would go here, but you can define your own categories", required=True),
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
        'participants': st.column_config.TextColumn(label="Participants", help="Participants separated by semicolons. Some fancy plotting options based on this might get added later.", required=False),
    }
    specials = st.data_editor(specials, use_container_width=True, column_config=specials_column_config, num_rows='dynamic')

    #####################
    ### Circumstances ###
    #####################
    # uploaded_circumstances_file = st.file_uploader("Choose a CSV file defining some special circumstances or copy/paste into the table", accept_multiple_files=False)

    if uploaded_circumstances_df is not None:
        circumstances = uploaded_circumstances_df
    else:
        if clear_example_data:
            circumstances = pd.read_csv("maxim_circumstances.csv", nrows=0)
        else:
            circumstances = pd.read_csv("maxim_circumstances.csv")

    circumstances.start = pd.to_datetime(circumstances.start)
    circumstances.end   = pd.to_datetime(circumstances.end)

    # if 'circumstances' not in st.session_state:
    #     st.session_state.circumstances = circumstances
    # else:
    #     circumstances = st.session_state.circumstances

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


with tab3:
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

    ##################
    ### Set filter ###
    ##################
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
    
    if show_dates == "All":
        filtered_df = df
        removed_people = [] 
    elif show_dates == "Kiss":
        filtered_df = df[df.stage != "No action"]
        removed_people = list(df[df.stage == "No action"].person_name.unique())
    elif show_dates == "Sex":
        filtered_df = df[~((df.stage == "Kiss") | (df.stage == "No action"))] # This keeps the longterm stuff
        removed_people = list(df[(df.stage == "Kiss") | (df.stage == "No action")].person_name.unique())
    
    with st.expander("Some or all entries for these people will not be shown"):
        if len(removed_people)==0:
            st.write('No one here')
        else:
            for person in removed_people:
                st.write(person)
        

    ########################
    ### Persons Settings ###
    ########################
    with st.container(border=True):
        st.markdown(
            """
            Here are all the individual people you have entered that you had a longterm arrangement or more than one date remaining after applying the filter.
            For each of them you can set the following:
            * Color: Use one of the named colors: https://matplotlib.org/stable/gallery/color/named_colors.html
            * Offset: How much should the lines and dots be moved up (or down)
            """
        )

        colored_persons = list(filtered_df[filtered_df.kind == "Longterm"].person_name.unique())
        colored_persons.extend(list(filtered_df[filtered_df.kind == "Date"].groupby("person_name").filter(lambda x: len(x) > 1).person_name.unique()))
        ons = set(filtered_df.person_name) - set(colored_persons)

        # with st.expander("These people will be colored grey"):
        #     if len(ons)==0:
        #         st.write('No one here')
        #     else:
        #         for person in ons:
        #             st.write(person)


        if 'person_settings' not in st.session_state:
            person_settings = pd.DataFrame(columns=['person_name','facecolor', 'edgecolor'])
            person_settings.person_name = list(set(colored_persons) | ons)
            person_settings = person_settings.merge(
                calculate_offsets(filtered_df, global_settings["dodge_dates_days"])[['person_name', 'offset']],
                how = 'left',
                on = 'person_name'
            )
            
            person_settings.offset = person_settings.offset.fillna(0)

            person_settings.facecolor = person_settings.facecolor.apply(lambda x: next(color))
            person_settings.edgecolor = person_settings.facecolor

            person_settings.loc[(person_settings['person_name'].isin(ons)), 'facecolor'] = 'grey'
            person_settings.loc[(person_settings['person_name'].isin(ons)), 'edgecolor'] = 'grey'
        
            st.session_state.person_settings = person_settings
        else:
            person_settings = st.session_state.person_settings
            person_settings = person_settings[person_settings.person_name.isin(filtered_df.person_name.unique())]

            


        person_settings_column_config = {
            "person_name": st.column_config.TextColumn(label="Name", disabled = True),
            "offset": st.column_config.NumberColumn(label="Offset", help="Leave empty to use a random value.", step=1),
            "facecolor": st.column_config.TextColumn(label="Color", help="Leave empty to pick automatically.")
        }

        person_settings = st.data_editor(
            person_settings, use_container_width=True,
            column_config=person_settings_column_config,
            column_order = ['person_name', 'facecolor', 'offset']
        )



    #########################
    ### Specials Settings ###
    #########################
    with st.container(border=True):
        st.markdown(
            """
            Here are all the special activities. For each kind of them you can pick a symbol from a list of available emojis. In the second table you can adjust the individual offsets.
            """
        )

    
        if 'specials_summary' not in st.session_state:
            specials_summary = specials.groupby('kind').size().reset_index(name='count').sort_values(by=['count', 'kind'], ascending = False).reset_index(drop=True)
            
            specials_summary['symbol_key'] = ""
            # specials_summary['symbol_url'] = ""

            specials_summary.symbol_key = specials_summary.symbol_key.apply(lambda x: next(symbol_key))
            # specials_summary.symbol_url = specials_summary.symbol_key.apply(lambda x: x)
            specials_summary.edgecolor = "None"

            # Check for known participants

            st.session_state.specials_summary = specials_summary
        else:
            specials_summary = st.session_state.specials_summary

        specials_summary_settings_column_config = {
            "kind": st.column_config.TextColumn(label="Kind", help="Self-defined kind of special activity", disabled = True),
            "count": st.column_config.NumberColumn(label="Count", help="How many special activities of this (self-defined) kind you tracked.", disabled = True),
            "symbol_key": st.column_config.SelectboxColumn(label="Symbol Key", help="Pick a symbol to represent this.", options=symbol_keys),
            # "symbol_url": st.column_config.TextColumn(label="Symbol", width="small")
        }

        specials_summary = st.data_editor(
            specials_summary, use_container_width=True, 
            column_config=specials_summary_settings_column_config,
            hide_index = False)
    
        if 'specials_offset' not in st.session_state:
            specials_offset = specials[['special','kind','start','participants']]
            
            specials_offset['offset'] = 0
            # specials_summary['symbol_url'] = ""

            st.session_state.specials_offset = specials_offset
        else:
            specials_offset = st.session_state.specials_offset

        specials_offset_settings_column_config = specials_column_config
        specials_offset_settings_column_config['offset'] = st.column_config.NumberColumn(label="Offset", help="Modify if needed.", step = 1)

        specials_offset = st.data_editor(
            specials_offset, use_container_width=True, 
            column_config=specials_offset_settings_column_config,
            hide_index = False)

    ##############################
    ### Circumstances Settings ###
    ##############################
    with st.container(border=True):
        st.markdown(
            """
            Here are all the circumstances (living abroad, etc.) you have described. For each of them you can also change the color as before.
            """
        )

        if 'circumstances_summary' not in st.session_state:
            circumstances_summary = circumstances.groupby('situation').size().reset_index(name='count').reset_index(drop=True)
            
            circumstances_summary['color'] = ""

            circumstances_summary.color = circumstances_summary.color.apply(lambda x: next(bg_color))

            st.session_state.circumstances_summary = circumstances_summary
        else:
            circumstances_summary = st.session_state.circumstances_summary

        circumstances_summary_column_config = {
            "situation": st.column_config.TextColumn(label="Situation", disabled = True),
            "count": st.column_config.NumberColumn(label="Count", help="How often this happened.", disabled = True),
            "color": st.column_config.TextColumn(label="Color", help="You can change the color to any named matplotlib color or use the hex code."),
        }

        circumstances_summary = st.data_editor(
            circumstances_summary, use_container_width=True, 
            column_config=circumstances_summary_column_config,
            hide_index = False)

###############
#### GRAPH ####
###############
with tab1:
    "Here is your timeline. You can upload, edit and download your data in the 'Data' tab."
    #############################
    ### Setting up the graph ####
    #############################
    sns.set_theme(style="darkgrid", rc={'axes.facecolor':'#171717', 'figure.facecolor':'#171717'})

    # Find or set extreme values
    min_year = df.start.min().year
    max_year = max(df.start.max(),df.end.max()).year
    if pd.isna(min_year):
        min_year=2000
        max_year=2001

    left =  0
    right = 365

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
    plt.yticks(range(min_year,max_year+1), fontsize = global_settings["year_font_size"], color = 'white')
    # Set month ticks and labels
    first_of_month = [dt.datetime(1,n,1).timetuple().tm_yday for n in range(1,13)]
    plt.xticks(first_of_month + [365],) # Set tick locations at the first of each month and end of year (ignoring leap years)
    ax.set_xticklabels('') # Hide automatic (number of day in the year) labels
    middle_of_month = [day + 15 for day in first_of_month] # Good enough
    ax.set_xticks(middle_of_month, minor=True) # Set minor ticks locations between the month 
    ax.tick_params(axis='x', which='minor', size=0) # Hide them from view
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'], minor=True, fontsize = global_settings["month_font_size"], color = 'white')

    # Years should go from top to bottom
    ax.invert_yaxis()

    fig.canvas.draw()
    renderer = fig.canvas.renderer

    ###############################################
    ### Enrich the data with offsets and colors ###
    ###############################################
    ### Individual people
    # Merge colors and offsets
    plot_df = filtered_df.merge(person_settings, on="person_name", how="left")
    # Set line width
    plot_df["line_width"] = global_settings["fplus_line_width"]
    plot_df.loc[(plot_df['stage'] == 'Relationship'), 'line_width'] = global_settings["relationship_line_width"]
    # Set line style
    plot_df["line_style"] = 'solid'
    plot_df.loc[(plot_df['stage'] == 'FWB'), 'line_style'] = 'dashed'
    # Set markers for dates
    plot_df["marker"] = "o"
    plot_df.loc[(plot_df['stage'] == 'No action'), 'marker'] = '.'
    plot_df.loc[(plot_df['stage'] == 'Kiss'), 'facecolor'] = 'None'
    
    ### Specials
    # Merge symbols and alocate columns
    specials_df = specials.merge(specials_summary, on = "kind", how = "left")
    specials_df = specials_df.merge(specials_offset[['special', 'offset']], on = "special", how = "left")
    specials_df['facecolor'] = 'grey'
    specials_df['edgecolor'] = specials_df.facecolor
    specials_df['size'] = 9

    # Circumstances
    circumstances_df = circumstances.merge(circumstances_summary, on = "situation", how = "left")

    #########################
    ### Plotting the data ###
    #########################
    offset_step = global_settings["dodge_step_size"]

    ### Long-term arrangements are plotted as lines
    lt = plot_df.query("kind == 'Longterm'").copy()
    # There are 4 options for arrangements:
    #   - Started and ended in the same year (simplest case)
    #   - Started in a certain year, but continued past the end of it
    #   - Started before a certain year, but ended in it
    #   - Started and ended in other years, so lasts through the whole year
    for index, row in lt.iterrows():
        for year in range(row.start.year, row.end.year + 1):
            if row.start.year == row.end.year:
                ax.plot(
                    [row.start.dayofyear , row.end.dayofyear],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0,
                )
            elif year == row.start.year:
                # Draw two lines so that the round caps dont' extend outside the area
                ax.plot(
                    [row.start.dayofyear, (365+row.start.dayofyear)/2],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0
                )
                ax.plot(
                    [(365+row.start.dayofyear)/2, 365],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='butt',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0
                )
            elif year == row.end.year:
                # Draw two lines so that the round caps dont' extend outside the area
                ax.plot(
                    [0 , row.end.dayofyear/2],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='butt',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0
                )
                ax.plot(
                    [row.end.dayofyear/2 , row.end.dayofyear],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='round',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0
                )
            else:
                ax.plot(
                    [left , right],
                    [year + row.offset*offset_step, year + row.offset*offset_step],
                    solid_capstyle='butt',
                    linestyle=row.line_style,
                    lw = row.line_width,
                    color = row.facecolor,
                    zorder = 0,
                )


    ### Dates are plotted as dots
    # Filter and calculate helper columns
    dates = plot_df.query("kind == 'Date'").copy()
    for index, row in dates.iterrows():
        ax.scatter(
            row.start.dayofyear, row.start.year + row.offset*offset_step,
            facecolor = row.facecolor,
            edgecolor = row.edgecolor,
            marker = row.marker,
            zorder = 1, 
            path_effects=[pe.Stroke(linewidth=2, foreground='k'), pe.Normal()]
        )

    # Add background circles for the special activities // Removed for now
    # for index, row in specials_df.iterrows():
    #     ax.scatter(
    #         row.start.dayofyear, row.start.year + row.offset*offset_step,
    #         facecolor = row.facecolor,
    #         edgecolor = row.edgecolor,
    #         s = row.size*row.size,
    #         zorder = 5
    #     )
    # Connect the background circles if applicable
    
    # Get x-y-key pairs
    symbol_x=[]
    symbol_y=[]
    symbol_row_key = []
    for index, row in specials_df.iterrows():
        symbol_x.append(row.start.dayofyear)
        symbol_y.append(row.start.year)
        symbol_row_key.append(row.symbol_key)
    # for each value of (x,y), we create
    # an annotation
    for x0, y0, key in zip(symbol_x, symbol_y, symbol_row_key):
        # Get the width and height of the image
        image_extent = symbol_boxes[key].get_tightbbox(renderer)

        # Adjust coordinates to place the center of the image at (x0, y0)
        adjusted_x0 = x0 - (image_extent.x1 - image_extent.x0) / 2
        adjusted_y0 = y0 - (image_extent.y1 - image_extent.y0) / 2

        ab = AnnotationBbox(symbol_boxes[key], (x0, y0), frameon=False, zorder=6)
        ax.add_artist(ab)


    # Add background patches for the defined situations
    bg_width = 0.9 # in years
    for index, row in circumstances_df.iterrows():
        for year in range(row.start.year, row.end.year +1 ):
            if row.start.year == row.end.year:
                ax.add_patch(patches.Rectangle(
                    (row.start.dayofyear,year-0.45),
                    row.end.dayofyear - row.start.dayofyear,bg_width,
                    edgecolor='None',facecolor=row.color,
                    zorder = -9))
            elif year == row.start.year:
                ax.add_patch(patches.Rectangle(
                    (row.start.dayofyear,year-0.45),
                    365 - row.start.dayofyear,bg_width,
                    edgecolor='None',facecolor=row.color,
                    zorder = -9))
            elif year == row.end.year:
                ax.add_patch(patches.Rectangle(
                    (1,year-0.45),
                    row.end.dayofyear,bg_width,
                    edgecolor='None',facecolor=row.color,
                    zorder = -9))

            else:
                ax.add_patch(patches.Rectangle(
                    (1,year-0.45),
                    365,bg_width,
                    edgecolor='None',facecolor=row.color,
                    zorder = -9))


    # # Add alternating patches in the background
    for year in range(min_year, max_year +1 ):
        ax.add_patch(patches.Rectangle(
            (0,year-0.45),
            365,bg_width,
            edgecolor='None',facecolor='white' if year % 2 == 0 else 'white',
            zorder = -99))
        
    st.pyplot(fig)
    plt.savefig("mydatingtimeline.svg")


with st.expander("Download everything"): 
    with zipfile.ZipFile("mydatingtimeline.zip", "w") as zf:
        with zf.open(f"people.csv", "w") as buffer:
            plot_df.to_csv(buffer,index=False)
        with zf.open(f"specials.csv", "w") as buffer:
            specials_df.to_csv(buffer,index=False)
        with zf.open(f"circumstances.csv", "w") as buffer:
            circumstances_df.to_csv(buffer, index=False)

    with open("mydatingtimeline.svg", "rb") as file:
        btn = st.download_button(
                label="Download as SVG",
                data=file,
                file_name="mydatingtimeline.svg",
                mime="image/svg"
            )
    with open("mydatingtimeline.zip", "rb") as file:
        btn = st.download_button(
                label="Download all data as ZIP",
                data=file,
                file_name="mydatingtimeline.zip",
                mime="image/svg"
            )