import streamlit as st
import pandas as pd
def calculate_offsets(df):
    df['offsets'] = 0

    # Check relationships first
    rel_people = df[df.kind=="Longterm"].groupby("person_name").agg({
        "start": 'min',
        "end": 'max'
    }).reset_index()

    rel_people['range'] = rel_people.end - rel_people.start
    rel_people = rel_people.sort_values(by="range", ascending = False)

    rel_people['offset'] = 0

    for index, row in rel_people.iterrows():
        # Overlapping people
        # st.write("###################################")
        # Get updated offset
        current_offset = rel_people.loc[rel_people.person_name == row.person_name, 'offset'].iloc[0]
        # st.write(
        #     "Current person:", row.person_name, "with offset", current_offset
        # )
        overlap_found = True
        while overlap_found:
            overlap = rel_people[(
                (
                (  (row.start <= rel_people.start) & (rel_people.start <= row.end)  ) |
                (  (row.start <= rel_people.end)   & (rel_people .end  <= row.end)  )  
                ) &
                (rel_people.offset == current_offset) &
                (rel_people.person_name != row.person_name)
            )]
            # st.write(row.person_name, current_offset)
            # st.write(overlap)

            if len(overlap) == 0:
                # st.write("No more overlaps!")
                overlap_found = False
            else:
                # st.write(
                #     "Overlap found! Update offset of",
                #     rel_people.loc[(
                #         rel_people.person_name == overlap.person_name.iloc[0]
                #     ), 'person_name']
                # )
                # st.write("Old offset", rel_people.loc[(
                #     rel_people.person_name == overlap.person_name.iloc[0]
                # ), 'offset'])
                rel_people.loc[(
                    rel_people.person_name == overlap.person_name.iloc[0]
                ), 'offset'] += 1

    # Now move the rest of the dates away from the relationships first and them further away from each other if necessary
    closeness_limit = 5 # How many dates should lie between dates so that they are allowed to be the same height

    date_people = df[
        ~(df.person_name.isin(rel_people.person_name))
    ].groupby('person_name').start.agg('min').reset_index().sort_values(by='start') # We need all individual dates
    date_people['offset'] = 0

    for index, row in date_people.iterrows():
        blocked_by_relationships = set(rel_people[(
            (rel_people.start <= row.start) & (row.start <= rel_people.end) # Relationships are fixed, just dodge any overlaps
        )].offset)

        blocked_by_dates = set(date_people[
            (date_people.start - row.start < pd.Timedelta(days=5)) &  # Date next to other date
            (date_people.offset == row.offset) # and on the same offset
        ].offset)

        blocked = blocked_by_relationships | blocked_by_dates
        unblocked = set(range(0,10,1)) - blocked
        if len(blocked)>0:
            date_people.loc[(date_people.person_name == row.person_name), 'offset'] = min(unblocked)


    return pd.concat([rel_people, date_people])