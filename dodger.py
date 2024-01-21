import streamlit as st
import pandas as pd
def calculate_offsets(df,closeness_limit):

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
        # st.write(fixed_name, "will keep it's current offset of", current_offset)
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
        # st.write("These people overlap:", overlap)
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
        # st.write('################################################################')
        # st.write("Looking at", name, "with offset", current_offset)
        # st.write("dates with them:")
        # st.write(date_people[date_people.person_name == name])
        for day in date_days:
            # st.write(">>>>>>>><<")
            # st.write('Looking at date:', day)
            blocked_by_relationships.extend(list(set(rel_people[(
                (rel_people.start <= day) & (day <= rel_people.end) # Relationships are fixed, just dodge any overlaps
            )].offset)))
            # st.write("These relationships happened at the same time", set(rel_people[(
            #     (rel_people.start <= day) & (day <= rel_people.end) # Relationships are fixed, just dodge any overlaps
            # )].person_name))
            # st.write("... with these offsets", set(rel_people[(
            #     (rel_people.start <= day) & (day <= rel_people.end) # Relationships are fixed, just dodge any overlaps
            # )].offset))
            blocked_by_dates.extend(
                list(set(
                    date_people[date_people.person_name != name][
                        (abs(date_people.start - day).dt.days <= closeness_limit) #&  # Date next to other date
                        # (date_people.offset == current_offset) # and on the same offset
            ].offset)))
            # st.write("These dates happened close to this date", date_people[date_people.person_name != name][
            #         (abs(date_people.start - day).dt.days <= closeness_limit) #&  # Date next to other date
            #         # (date_people.offset == current_offset) # and on the same offset
            #     ])
            # st.write("... with these offsets", set(date_people[date_people.person_name != name][
            #         (date_people.start - day < pd.Timedelta(days=closeness_limit)) #&  # Date next to other date
            #         # (date_people.offset == current_offset) # and on the same offset
            #     ].offset))
            # st.write("blocked by rel", blocked_by_relationships)
            # st.write("blocked by dates", blocked_by_dates)
        blocked = set(blocked_by_relationships) | set(blocked_by_dates)
        # st.write("Therefore, these offsets are blocked", blocked)
        unblocked = set(range(0,10,1)) - blocked
        # st.write("And this one will be picked as the new one", min(unblocked))
        # st.write(date_days, blocked, unblocked)
        if len(blocked)>0:
            date_people.loc[(date_people.person_name == name), 'offset'] = min(unblocked)
            # st.write("new offset", date_people.loc[(date_people.person_name == name), 'offset'])
        # st.write(date_people)

    return pd.concat([rel_people, date_people])