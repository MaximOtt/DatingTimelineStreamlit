import streamlit as st
import pandas as pd
# def calculate_offsets(df, specials, closeness_limit): # Removed for now
def calculate_offsets(df, closeness_limit):
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
    # known_people = df.person_name.unique()
    # specials.known_participant_list = specials.known_participant_list.apply(lambda x: [participant for participant in x if participant in known_people])
    # specials['known'] = specials.known_participant_list.apply(len)
    # st.write(specials.known_participant_list)

    # specials_with_randoms = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_randoms['person_name'] = 'random' + specials_with_randoms.index.astype(str)
    # specials_with_one = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_one['person_name'] = specials_with_one['known_participant_list'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None)
    # specials_with_multiple = specials[specials.known_participant_list.apply(lambda x: len(x) == 0)]
    # specials_with_multiple = specials_with_multiple.explode('known_participant_list')
    # specials_with_multiple['person_name'] = specials_with_multiple.known_participant_list
    # st.write(specials_with_multiple)

    # Check relationships first
    rel_people = df[df.kind=="Longterm"].groupby("person_name").agg({
        "start": 'min',
        "end": 'max'
    }).reset_index()

    rel_people['range'] = rel_people.end - rel_people.start
    rel_people = rel_people.sort_values(by="range", ascending=False)

    rel_people['offset'] = 0

    for fixed_name in rel_people.person_name.unique():
        # Fetch current offset. This will not be changed
        current_offset = rel_people.loc[rel_people.person_name == fixed_name, 'offset'].iloc[0]
        # Fetch current range borders
        current_start = rel_people.loc[rel_people.person_name == fixed_name, 'start'].iloc[0]
        current_end   = rel_people.loc[rel_people.person_name == fixed_name, 'end'].iloc[0]

        # Find overlapping (shorter) relationships
        overlap = rel_people[(
            (
            (  (current_start <= rel_people.start) & (rel_people.start <= current_end)  ) |
            (  (current_start <= rel_people.end)   & (rel_people.end  <=  current_end)  ) |
            (  (rel_people.start <= current_start) & (current_end <= rel_people.end)  ) 
            ) &
            (rel_people.offset == current_offset) &
            (rel_people.person_name != fixed_name)
        )]
        if len(overlap) > 0:
            for name_to_shift in overlap.person_name.unique():
                rel_people.loc[(rel_people.person_name == name_to_shift), 'offset'] -= 1

    date_people = df[
        ~(df.person_name.isin(rel_people.person_name))
    ] # We need all individual dates with people that there was no relationship with
    date_people['offset'] = 0
    

    for name in date_people.person_name.unique():
        blocked_by_relationships = []
        blocked_by_dates = []
        date_days = list(date_people[date_people.person_name == name].start)
        current_offset = date_people.loc[date_people.person_name == name, 'offset'].iloc[0]

        for day in date_days:

            blocked_by_relationships.extend(list(set(rel_people[(
                (rel_people.start <= day) & (day <= rel_people.end) # Relationships are fixed, just dodge any overlaps
            )].offset)))

            blocked_by_dates.extend(
                list(set(
                    date_people[date_people.person_name != name][
                        (abs(date_people.start - day).dt.days <= closeness_limit) #&  # Date next to other date
                        # (date_people.offset == current_offset) # and on the same offset
            ].offset)))
  
        blocked = set(blocked_by_relationships) | set(blocked_by_dates)
        unblocked = set(range(0,10,1)) - blocked

        if len(blocked)>0:
            date_people.loc[(date_people.person_name == name), 'offset'] = min(unblocked)

    return pd.concat([rel_people, date_people])[['person_name', 'offset']].drop_duplicates()