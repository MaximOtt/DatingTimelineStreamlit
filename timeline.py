import streamlit as st
import glob
import pandas as pd
import matplotlib.pyplot as plt # Plotting
import matplotlib.patches as patches # Background
import matplotlib.patheffects as pe
import matplotlib.offsetbox as ob
import matplotlib.font_manager as fp
# from matplotlib.offsetbox import OffsetImage, AnnotationBbox
# from matplotlib.font_manager import FontProperties
import seaborn as sns
import datetime as dt # Obviously for time data
from itertools import cycle
from utils import *
import zipfile

if 'app_run_counter' not in st.session_state:
    st.session_state['app_run_counter'] = 1
    print('')
    print('#### PAGE REFRESH ####')
else:
    st.session_state['app_run_counter'] += 1

print('')
print('### App Run Counter:', st.session_state['app_run_counter'])
######################################
### Prepare some things in advance ###
######################################
# Default appearance settings
if 'global_settings' not in st.session_state:
    st.session_state['global_settings'] = {
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
symbol_boxes = {key: ob.OffsetImage(image, zoom=0.02) for key, image in symbols.items()}
st.session_state['symbol_key_list'] = [key for key, image in symbols.items()]
# symbol_key = cycle(symbol_keys)

# Set color cycles
st.session_state['bg_colors'] = [
    'xkcd:light pink',
    'xkcd:pale',
    'xkcd:pale blue',
    'xkcd:very pale green',
    'xkcd:egg shell',
    'xkcd:pale peach',
    'xkcd:light sky blue'
]
bg_color = cycle(st.session_state['bg_colors'])

st.session_state['color_list'] = [
    'xkcd:dull purple', 'xkcd:umber', 'xkcd:golden yellow', 'xkcd:pale teal', 'xkcd:pinky red', # 5
    'xkcd:bronze', 'xkcd:bluish', 'xkcd:vermillion', 'xkcd:sickly green', 'xkcd:cranberry', # 10
    'xkcd:barney', 'xkcd:watermelon', 'xkcd:easter purple', 'xkcd:darkish green', 'xkcd:tomato', # 15
    'xkcd:greeny blue', 'xkcd:pastel red', 'xkcd:topaz', 'xkcd:burple', 'xkcd:maroon', # 20 
    'xkcd:olive', 'xkcd:forest green', 'xkcd:periwinkle', 'xkcd:lime', 'xkcd:lilac', # 25
    'xkcd:royal purple', 'xkcd:light orange', 'xkcd:cerulean', 'xkcd:kelly green', 'xkcd:puke green', # 30
]
# color = cycle(st.session_state['color_list'])

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


tab1, tab2, tab3, tab4 = st.tabs(["Timeline", "Data", "Customize", "Settings"])

# tab1: Timeline
# tab2: Data Upload/Input/Edit/View
# tab3: General Plot Settings
# tab4: Data Summary and Customization

############################
### General Settings Tab ###
############################
with tab4:
    "Here you can customize the general appearance of the graph."
    for key, value in st.session_state['global_settings'].items():
        if isinstance(st.session_state['global_settings'][key],int):
            st.session_state['global_settings'][key] = st.number_input(
                f'`{key}`', step = 1, min_value= 1, 
                value = st.session_state['global_settings'][key])
        elif isinstance(st.session_state['global_settings'][key],float):
            st.session_state['global_settings'][key] = st.number_input(
                f'`{key}`', step = 0.01, min_value= 0.0, 
                value = st.session_state['global_settings'][key])

################
### Data Tab ###
################
with tab2:
    st.write(
        "Please use the 'Upload' expander at the top of this page to upload your data, or clear the example data by clicking on the button below and enter everything manually."
    )
    st.warning(
        "Make sure to download your data regularly, as refreshing the page might delete all your progress!"
    )


    print('Start of Data tab')
    ###############
    ### Persons ###
    ###############
    # When the page is rendered for the first time, we want to show example data and obviously not delete anything
    if 'reinitialize' not in st.session_state:
        st.session_state["reinitialize"] = True
    

    col1, col2 = st.columns(2)
    with col1:
        button_a = st.button('Show example data', use_container_width=True)
    with col2:
        button_b = st.button('Delete everything', use_container_width=True)
    
    if button_a or button_b:
        print('A button was True, reinitialize is set to True')
        st.session_state["reinitialize"] = True

    # Dataframe initialization should happen only when certain conditions are met
    # Otherwise, the data frame should be loaded from sessionstate
    
    if st.session_state['reinitialize']:
        if button_a:
            st.session_state['people'] =        pd.read_csv("eg_people.csv")
            st.session_state['specials'] =      pd.read_csv("eg_specials.csv")
            st.session_state['circumstances'] = pd.read_csv("eg_circumstances.csv")
        elif button_b:
            st.session_state['people'] =        pd.read_csv("eg_people.csv", nrows=0)
            st.session_state['specials'] =      pd.read_csv("eg_specials.csv", nrows=0)
            st.session_state['circumstances'] = pd.read_csv("eg_circumstances.csv", nrows=0)
        elif uploaded_people is not None:
            st.session_state['people'] = uploaded_people_df
            if uploaded_specials is not None:
                st.session_state['specials'] = uploaded_specials_df
            else:
                st.session_state['specials'] = pd.read_csv("eg_specials.csv", nrows=0)
            if uploaded_circumstances is not None:
                st.session_state['circumstances'] = uploaded_circumstances_df
            else:
                st.session_state['circumstances'] = pd.read_csv("eg_circumstances.csv", nrows=0)
        else:
            st.session_state['people'] =        pd.read_csv("eg_people.csv")
            st.session_state['specials'] =      pd.read_csv("eg_specials.csv")
            st.session_state['circumstances'] = pd.read_csv("eg_circumstances.csv")
        
        st.session_state['people'].start = pd.to_datetime(st.session_state['people'].start)
        st.session_state['people'].end   = pd.to_datetime(st.session_state['people'].end)    
        st.session_state['people'].name  = st.session_state['people'].name.astype(str)
        st.session_state['people'].kind  = st.session_state['people'].kind.astype(str)
        st.session_state['people'].start = pd.to_datetime(st.session_state['people'].start)
        st.session_state['people'].end =   pd.to_datetime(st.session_state['people'].end)
        st.session_state['specials'].start = pd.to_datetime(st.session_state['specials'].start)
        st.session_state['circumstances'].start = pd.to_datetime(st.session_state['circumstances'].start)
        st.session_state['circumstances'].end   = pd.to_datetime(st.session_state['circumstances'].end)

        st.session_state['reinitialize'] = False
        button_a = False
        button_b = False


with tab3:
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

    st.session_state['filter_choice'] = st.radio(
        "What kind of dates would you like to see in the graph?",
        ["All", "Kiss", "Sex"],
        captions = ["Show all dates.", "Show only dates where there was at least a kiss.", "Show only dates where you had sex."])
    
    apply_filter()

with tab2:
    ###########################
    ### Display data frames ###        
    ###########################
    st.markdown('#### Individials')
    people_column_config_dict = {
        "name": "Name",
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
            required=True
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
    st.session_state['people'] = st.data_editor(
        st.session_state['people'], column_config=people_column_config_dict,
        on_change=calculate_people_summary, 
        use_container_width=True, num_rows='dynamic'
    )
    
    if 'people_settings' not in st.session_state:
        calculate_people_summary()
    
    if set(st.session_state['people'].name) != set(st.session_state['people_settings'].name):
        print('Triggered rerun')
        calculate_people_summary()
        st.rerun()

    st.markdown('#### Special activities')
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
    st.session_state['specials'] = st.data_editor(st.session_state['specials'], use_container_width=True, column_config=specials_column_config, num_rows='dynamic')

    if 'specials_summary' not in st.session_state:
        calculate_specials_summary()
    
    if set(st.session_state['specials'].kind) != set(st.session_state['specials_summary'].kind):
        print('Triggered rerun')
        calculate_specials_summary()
        st.rerun()

    st.markdown('#### Circumstances')
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
    st.session_state['circumstances'] = st.data_editor(st.session_state['circumstances'], use_container_width=True, column_config=circumstances_column_config, num_rows='dynamic')

    if 'circumstances_summary' not in st.session_state:
        calculate_circumstances_summary()
    
    if set(st.session_state['circumstances'].situation) != set(st.session_state['circumstances_summary'].situation):
        print('Triggered rerun')
        calculate_circumstances_summary()
        st.rerun()

with tab3:
    with st.expander("Some or all entries for these people will not be shown"):
        if len(st.session_state['removed_people'])==0:
            st.write('No one here')
        else:
            for person in st.session_state['removed_people']:
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

        people_settings_column_config = {
            "name": st.column_config.TextColumn(label="Name", disabled = True),
            "offset": st.column_config.NumberColumn(label="Offset", help="You can edit this.", step=1),
            "facecolor": st.column_config.TextColumn(label="Color", help="You can edit this.")
        }
        
        st.session_state['people_settings'] = st.data_editor(
            st.session_state['people_settings'], use_container_width=True,
            column_config = people_settings_column_config,
            column_order = ['name', 'facecolor', 'offset']
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

        specials_summary_settings_column_config = {
            "kind": st.column_config.TextColumn(label="Kind", help="Self-defined kind of special activity", disabled = True),
            "count": st.column_config.NumberColumn(label="Count", help="How many special activities of this (self-defined) kind you tracked.", disabled = True),
            "symbol_key": st.column_config.SelectboxColumn(label="Symbol Key", help="Pick a symbol to represent this.", options=st.session_state['symbol_key_list']),
            # "symbol_url": st.column_config.TextColumn(label="Symbol", width="small")
        }

        st.session_state['specials_summary'] = st.data_editor(
            st.session_state['specials_summary'], use_container_width=True, 
            column_config=specials_summary_settings_column_config,
            hide_index = False)
    
        if 'specials_offset' not in st.session_state:
            specials_offset = st.session_state['specials'][['special','kind','start','participants']]
            
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
            calculate_circumstances_summary()
        
        

        circumstances_summary_column_config = {
            "situation": st.column_config.TextColumn(label="Situation", disabled = True),
            "count": st.column_config.NumberColumn(label="Count", help="How often this happened.", disabled = True),
            "color": st.column_config.TextColumn(label="Color", help="You can change the color to any named matplotlib color or use the hex code."),
        }

        st.session_state['circumstances_summary'] = st.data_editor(
            st.session_state['circumstances_summary'], use_container_width=True, 
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
    min_year = st.session_state['filtered_people'].start.min().year
    max_year = max(st.session_state['filtered_people'].start.max(),st.session_state['filtered_people'].end.max()).year
    if pd.isna(min_year):
        min_year=2000
        max_year=2001

    left =  0
    right = 365

    # Create figure
    fig, ax = plt.subplots(
        # 2,1, sharex=True, sharey=False, 
        # height_ratios=[max_year-min_year,2], 
        figsize=(10,15)
    )
    plt.subplots_adjust(hspace=0.0)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.grid(False)

    # Set limits
    ax.set_xlim([-5, 370])
    ax.set_ylim([min_year-0.5, max_year+0.5])

    # Set year ticks (labels are fine automatically)
    # plt.yticks(range(min_year,max_year+1), fontsize = st.session_state['global_settings']["year_font_size"], color = 'white')
    ax.set_yticks(range(min_year, max_year+1))
    ax.set_yticklabels(range(min_year, max_year+1), fontsize=st.session_state['global_settings']["year_font_size"], color='white')

    # Set month ticks and labels
    first_of_month = [dt.datetime(1,n,1).timetuple().tm_yday for n in range(1,13)]
    ax.set_xticks(first_of_month + [365],) # Set tick locations at the first of each month and end of year (ignoring leap years)
    ax.set_xticklabels('') # Hide automatic (number of day in the year) labels
    middle_of_month = [day + 15 for day in first_of_month] # Good enough
    ax.set_xticks(middle_of_month, minor=True) # Set minor ticks locations between the month 
    ax.tick_params(axis='x', which='minor', size=0) # Hide them from view
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'], minor=True, fontsize = st.session_state['global_settings']["month_font_size"], color = 'white')

    # Years should go from top to bottom
    ax.invert_yaxis()

    fig.canvas.draw()
    renderer = fig.canvas.renderer

    ###############################################
    ### Enrich the data with offsets and colors ###
    ###############################################
    ### Individual people
    # Merge colors and offsets
    people_plot_df = st.session_state['filtered_people'].merge(st.session_state['people_settings'], on="name", how="left")
    # Set line width
    people_plot_df["line_width"] = st.session_state['global_settings']["fplus_line_width"]
    people_plot_df.loc[(people_plot_df['stage'] == 'Relationship'), 'line_width'] = st.session_state['global_settings']["relationship_line_width"]
    # Set line style
    people_plot_df["line_style"] = 'solid'
    people_plot_df.loc[(people_plot_df['stage'] == 'FWB'), 'line_style'] = 'dashed'
    # Set markers for dates
    people_plot_df["marker"] = "o"
    people_plot_df.loc[(people_plot_df['stage'] == 'No action'), 'marker'] = '.'
    people_plot_df.loc[(people_plot_df['stage'] == 'Kiss'), 'facecolor'] = 'None'
    
    ### Specials
    # Merge symbols and alocate columns
    specials_plot_df = st.session_state['specials'].merge(st.session_state['specials_summary'], on = "kind", how = "left")
    specials_plot_df = specials_plot_df.merge(specials_offset[['special', 'offset']], on = "special", how = "left")
    specials_plot_df['facecolor'] = 'grey'
    specials_plot_df['edgecolor'] = specials_plot_df.facecolor
    specials_plot_df['size'] = 9

    # Circumstances
    circumstances_plot_df = st.session_state['circumstances'].merge(st.session_state['circumstances_summary'], on = "situation", how = "left")

    #########################
    ### Plotting the data ###
    #########################
    offset_step = st.session_state['global_settings']["dodge_step_size"]

    ### Long-term arrangements are plotted as lines
    lt = people_plot_df.query("kind == 'Longterm'").copy()
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
    dates = people_plot_df.query("kind == 'Date'").copy()
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
    for index, row in specials_plot_df.iterrows():
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
    for index, row in circumstances_plot_df.iterrows():
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
                    364,bg_width,
                    edgecolor='None',facecolor=row.color,
                    zorder = -9))


    # # Add alternating patches in the background
    for year in range(min_year, max_year +1 ):
        ax.add_patch(patches.Rectangle(
            (0,year-0.45),
            365,bg_width,
            edgecolor='None',facecolor='white' if year % 2 == 0 else 'white',
            zorder = -99))
        
    # Add legend annotations
    font_prop = fp.FontProperties(family='monospace')
    ax.annotate('',
            xy=(1, max_year+0.8), xycoords='data',
            xytext=(364, max_year+0.8), textcoords='data',
            arrowprops=dict(facecolor='white', lw=1, arrowstyle='-'),
            horizontalalignment='center', verticalalignment='center', 
            annotation_clip=False)
    ax.annotate((
            'What the symbols mean'
        ),
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-1), textcoords='offset fontsize',
        fontproperties=font_prop,
        annotation_clip=False, 
        color = 'white',
        size=16)
    ax.annotate((
              '       |  Thick solid:  Relationship'+
            '\nLines  |  Thin solid:   It\'s complicated'+
            '\n       |  Dotted:       Friends with benefits'
        ), 
        fontproperties=font_prop,
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-5.5), textcoords='offset fontsize',
        annotation_clip=False, 
        color = 'white',
        size = 13)
    ax.annotate((
              '       |  Small dot:      Date with no \'action\''+
            '\nPoints |  Empty circle:   There was a kiss'+
            '\n       |  Filled circle:  You had sex'
        ), 
        fontproperties=font_prop,
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-9.5), textcoords='offset fontsize',
        annotation_clip=False, 
        color = 'white',
        size = 13)
    ax.annotate((
              'Everyone who appears more than once gets a color.\nOne-time meetings are grey.'
        ), 
        fontproperties=font_prop,
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-12.5), textcoords='offset fontsize',
        annotation_clip=False, 
        color = 'white',
        size = 13)
    ax.annotate((
              'Emojis represent special activities like, e.g., threesomes.'
        ), 
        fontproperties=font_prop,
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-14), textcoords='offset fontsize',
        annotation_clip=False, 
        color = 'white',
        size = 13)
    ax.annotate((
              'Colored background denotes a special situation, e.g., living abroad.'
        ), 
        fontproperties=font_prop,
        xy=(1, max_year+0.9), xycoords='data', 
        xytext=(0,-15.5), textcoords='offset fontsize',
        annotation_clip=False, 
        color = 'white',
        size = 13)
    
    # Show and save figure
    st.pyplot(fig)
    plt.savefig("mydatingtimeline.svg")
    plt.savefig("mydatingtimeline.jpeg")


with st.expander("Download everything"): 
    with zipfile.ZipFile("mydatingtimeline.zip", "w") as zf:
        with zf.open(f"people.csv", "w") as buffer:
            people_plot_df.to_csv(buffer,index=False)
        with zf.open(f"specials.csv", "w") as buffer:
            specials_plot_df.to_csv(buffer,index=False)
        with zf.open(f"circumstances.csv", "w") as buffer:
            circumstances_plot_df.to_csv(buffer, index=False)

    with open("mydatingtimeline.svg", "rb") as file:
        btn = st.download_button(
                label="Download as SVG",
                data=file,
                file_name="mydatingtimeline.svg",
                mime="image/svg"
            )
    with open("mydatingtimeline.jpeg", "rb") as file:
        btn = st.download_button(
                label="Download as JPEG",
                data=file,
                file_name="mydatingtimeline.jpeg",
                mime="image/jpeg"
            )
    with open("mydatingtimeline.zip", "rb") as file:
        btn = st.download_button(
                label="Download all data as ZIP",
                data=file,
                file_name="mydatingtimeline.zip",
                mime="image/svg"
            )