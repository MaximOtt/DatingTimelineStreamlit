import streamlit as st
import pandas as pd
from itertools import cycle


def apply_filter():
    print('Executing apply_filter()')
    if st.session_state['filter_choice'] == "All":
        st.session_state['filtered_people'] = st.session_state['people']
        st.session_state['removed_people'] = [] 
    elif st.session_state['filter_choice'] == "Kiss":
        st.session_state['filtered_people'] = st.session_state['people'][st.session_state['people'].stage != "No action"]
        st.session_state['removed_people'] = list(st.session_state['people'][st.session_state['people'].stage == "No action"].name.unique())
    elif st.session_state['filter_choice'] == "Sex":
        st.session_state['filtered_people'] = st.session_state['people'][
            ~((st.session_state['people'].stage == "Kiss") | (st.session_state['people'].stage == "No action"))
        ] # This keeps the longterm stuff
        st.session_state['removed_people'] = list(st.session_state['people'][
            (st.session_state['people'].stage == "Kiss") | (st.session_state['people'].stage == "No action")
        ].name.unique())




def calculate_people_summary():
    print('Executing calculate_people_summary()')
    st.session_state['people_to_color'] = list(
        st.session_state['filtered_people'][st.session_state['filtered_people'].kind == "Longterm"].name.unique()
    )
    st.session_state['people_to_color'].extend(list(
        st.session_state['filtered_people'][st.session_state['filtered_people'].kind == "Date"].groupby("name").filter(lambda x: len(x) > 1).name.unique()
    ))
    st.session_state['ons'] = set(st.session_state['filtered_people'].name) - set(st.session_state['people_to_color'])

    st.session_state['people_settings'] = pd.DataFrame(columns=['name','facecolor', 'edgecolor'])
    st.session_state['people_settings'].name = list(set(st.session_state['people_to_color']) | st.session_state['ons'])
        
    st.session_state['people_settings'].name  = st.session_state['people_settings'].name.astype(str)

    color = cycle(st.session_state['color_list'])
    if len(st.session_state['people_settings']) >0:
        st.session_state['people_settings'] = st.session_state['people_settings'].merge(
            calculate_offsets(st.session_state['filtered_people'])[['name', 'offset']],
            how = 'left',
            on = 'name'
        )
    
        st.session_state['people_settings'].offset = st.session_state['people_settings'].offset.fillna(0)

        st.session_state['people_settings'].facecolor = st.session_state['people_settings'].facecolor.apply(lambda x: next(color))
        st.session_state['people_settings'].edgecolor = st.session_state['people_settings'].facecolor

        st.session_state['people_settings'].loc[(st.session_state['people_settings']['name'].isin(st.session_state['ons'])), 'facecolor'] = 'grey'
        st.session_state['people_settings'].loc[(st.session_state['people_settings']['name'].isin(st.session_state['ons'])), 'edgecolor'] = 'grey'

def calculate_specials_summary():
    print('Executing calculate_specials_summary()')
    specials_summary = st.session_state['specials'].groupby('kind').size().reset_index(name='count').sort_values(by=['count', 'kind'], ascending = False).reset_index(drop=True)

    specials_summary['symbol_key'] = ""
    # specials_summary['symbol_url'] = ""

    symbol_key = cycle(st.session_state['symbol_key_list'])
    specials_summary.symbol_key = specials_summary.symbol_key.apply(lambda x: next(symbol_key))
    # specials_summary.symbol_url = specials_summary.symbol_key.apply(lambda x: x)
    specials_summary.edgecolor = "None"

    # Check for known participants
    st.session_state['specials_summary'] = specials_summary

def calculate_circumstances_summary():
    circumstances_summary = st.session_state['circumstances'].groupby('situation').size().reset_index(name='count').reset_index(drop=True)
    circumstances_summary['color'] = ""
    bg_color = cycle(st.session_state['bg_colors'])
    circumstances_summary.color = circumstances_summary.color.apply(lambda x: next(bg_color))

    st.session_state['circumstances_summary'] = circumstances_summary

def calculate_offsets(df):
    # Split the df to plot by the number of known participants and treat the cases separately
    # No known participants:
    # > Offset must be dodged like a regular date
    # > Edge color is off, so that only the symbol remains
    # Exactly one known participant:
    # > Treated as part of the date group when calculating offset, so that it is placed on the same height
    # > Face and edge is exactly the color of the participant
    # More than one known participant:
    # > Event is duplicated for each participant with their colors and offsets
    # > Treated as part of the date group when calculating offset, so that it is placed on the same height for each
    # > Facecolor is off, but edgecolor for each copy is set to the participants color, so that we get an empty circle with symbol inside
    # > Lines with the color gradient are drawn to connect the circles 
    # specials['known_participant_list'] = specials.participants.str.split(';').apply(lambda x: [
    #     participant.strip() for participant in x
    # ])
    # known_people = df.name.unique()
    # specials.known_participant_list = specials.known_participant_list.apply(lambda x: [participant for participant in x if participant in known_people])
    # specials['known'] = specials.known_participant_list.apply(len)
    # st.write(specials.known_participant_list)

    # specials_with_randoms = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_randoms['name'] = 'random' + specials_with_randoms.index.astype(str)
    # specials_with_one = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_one['name'] = specials_with_one['known_participant_list'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    # specials_with_multiple = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_multiple = specials_with_multiple.explode('known_participant_list')
    # specials_with_multiple['name'] = specials_with_multiple.known_participant_list
    # st.write(specials_with_multiple)

    print('Executing calculate_offsets()')
    closeness_limit = st.session_state['global_settings']['dodge_dates_days']

    # Check relationships first
    rel_people = df[df.kind=="Longterm"].groupby("name").agg({
        "start": 'min',
        "end": 'max'
    }).reset_index()

    rel_people['range'] = rel_people.end - rel_people.start
    rel_people = rel_people.sort_values(by="range", ascending=False)

    rel_people['offset'] = 0

    for fixed_name in rel_people.name.unique():
        # Fetch current offset. This will not be changed
        current_offset = rel_people.loc[rel_people.name == fixed_name, 'offset'].iloc[0]
        # Fetch current range borders
        current_start = rel_people.loc[rel_people.name == fixed_name, 'start'].iloc[0]
        current_end   = rel_people.loc[rel_people.name == fixed_name, 'end'].iloc[0]

        # Find overlapping (shorter) relationships
        overlap = rel_people[(
            (
            (  (current_start <= rel_people.start) & (rel_people.start <= current_end)  ) |
            (  (current_start <= rel_people.end)   & (rel_people.end  <=  current_end)  ) |
            (  (rel_people.start <= current_start) & (current_end <= rel_people.end)  ) 
            ) &
            (rel_people.offset == current_offset) &
            (rel_people.name != fixed_name)
        )]
        if len(overlap) > 0:
            for name_to_shift in overlap.name.unique():
                rel_people.loc[(rel_people.name == name_to_shift), 'offset'] -= 1

    date_people = df[
        ~(df.name.isin(rel_people.name))
    ].copy() # We need all individual dates with people that there was no relationship with
    date_people['offset'] = 0
    

    for name in date_people.name.unique():
        blocked_by_relationships = []
        blocked_by_dates = []
        date_days = list(date_people[date_people.name == name].start)
        current_offset = date_people.loc[date_people.name == name, 'offset'].iloc[0]

        for day in date_days:

            blocked_by_relationships.extend(list(set(rel_people[(
                (rel_people.start <= day) & (day <= rel_people.end) # Relationships are fixed, just dodge any overlaps
            )].offset)))

            blocked_by_dates.extend(
                list(set(
                    date_people[date_people.name != name][
                        (abs(date_people[date_people.name != name].start - day).dt.days <= closeness_limit) #&  # Date next to other date
                        # (date_people.offset == current_offset) # and on the same offset
            ].offset)))
  
        blocked = set(blocked_by_relationships) | set(blocked_by_dates)
        unblocked = set(range(0,10,1)) - blocked

        if len(blocked)>0:
            date_people.loc[(date_people.name == name), 'offset'] = min(unblocked)

    return pd.concat([rel_people, date_people])[['name', 'offset']].drop_duplicates()