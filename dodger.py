import streamlit as st
def calculate_offsets(df):
    df['offsets'] = 0

    rel_people = df[df.kind=="Longterm"].groupby("person_name").agg({
        "start": 'min',
        "end": 'max'
    })

    rel_people['range'] = rel_people.end - rel_people.start
    rel_people = rel_people.sort_values(by="range", ascending = False)

    for row in rel_people.iterrows():
        # Overlapping people
        overlap = rel_people[rel_people.start]

    return rel_people