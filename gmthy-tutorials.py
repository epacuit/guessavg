
import streamlit as st
import pymongo
import numpy as np
import pandas as pd
import altair as alt
import math

st.header("Guess the average")
st.write("Guess a number between 1 and 100.   The number closest to 2/3 of the average of the guesses is the winner.")

the_password = st.secrets.admin_pwd

query_params = st.experimental_get_query_params()

def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


if 'round' in query_params.keys(): 
    show_guess_form = True
    round = f"Round {query_params['round'][0]}"
else: 
    show_guess_form = False

if 'results' in query_params.keys(): 
    showing_results = True
else: 
    showing_results = False


if 'already_submitted' not in st.session_state:
    st.session_state['already_submitted'] = False

if showing_results: 
    client = pymongo.MongoClient(st.secrets.mongodb_url)

    db = client.StableVoting.PPE

    password = st.sidebar.text_input("Show results", type="password")
    guess_round = st.sidebar.selectbox('Round',
        ('Round 1', 'Round 2', 'Both'), disabled = password != the_password)
    document = None
    if guess_round == 'Both': 
        document_r1 = db.find_one({"game_name": "Guess the average", "round": 'Round 1'})
        document_r2 = db.find_one({"game_name": "Guess the average", "round": 'Round 2'})
    else: 
        document = db.find_one({"game_name": "Guess the average", "round": guess_round})
    if document is not None and password == the_password:
        st.sidebar.write(f"{'1 person has ' if len(document['guesses']) == 1 else str(len(document['guesses'])) + ' people have '} submitted a guess.")
    show_results = st.sidebar.button("Show", disabled=password != the_password)
    
if showing_results and show_results and guess_round in ['Round 1', 'Round 2']: 

    guesses = document["guesses"]

    guesses = sorted(guesses, key = lambda ng : ng["guess"])
    two_thirds_average = float(2.0) / float(3.0) * np.average([ng["guess"] for ng in guesses])
    distances = [math.fabs(ng["guess"] - two_thirds_average) for ng in guesses]
    min_dist = min(distances)
    st.write(f"2/3 of the average of the guesses is **{two_thirds_average}**")
    df = pd.DataFrame({
        'num': list(range(1, len(guesses) + 1)),
        'guess': [ng["guess"] for ng in guesses],
        'name': [ng["name"] for ng in guesses],
        'closest': [math.fabs(ng["guess"] - two_thirds_average) == min_dist for ng in guesses],
        })
    c = alt.Chart(df).mark_circle(size=200).encode(
        x=alt.X('num', axis=alt.Axis(labels=False, title='')), y='guess', color='closest', tooltip=["name", 'guess'])


    st.altair_chart(c, use_container_width=True)

if showing_results and show_results and guess_round in ['Both']: 
    guesses_r1 = document_r1["guesses"]
    guesses_r2 = document_r2["guesses"]

    two_thirds_average_r1 = float(2.0) / float(3.0) * np.average([ng["guess"] for ng in guesses_r1])
    two_thirds_average_r2 = float(2.0) / float(3.0) * np.average([ng["guess"] for ng in guesses_r2])
    distances_r1 = [math.fabs(ng["guess"] - two_thirds_average_r1) for ng in guesses_r1]
    min_dist_r1 = min(distances_r1)
    distances_r2 = [math.fabs(ng["guess"] - two_thirds_average_r2) for ng in guesses_r2]
    min_dist_r2 = min(distances_r2)
    st.write(f"2/3 of the average of the guesses for Round 1 is **{two_thirds_average_r1}**")
    st.write(f"2/3 of the average of the guesses for Round 2 is **{two_thirds_average_r2}**")
    df = pd.DataFrame({
        'num': list(range(1, len(guesses_r1) + 1)) + list(range(1, len(guesses_r2) + 1)),
        'guess': [ng["guess"] for ng in guesses_r1] + [ng["guess"] for ng in guesses_r2],
        'name': [ng["name"] for ng in guesses_r1] + [ng["name"] for ng in guesses_r2],
        'round': ['Round 1' for _ in guesses_r1] + ['Round 2' for _ in guesses_r2],
        })
    c = alt.Chart(df).mark_circle(size=200).encode(
        x=alt.X('num', axis=alt.Axis(labels=False, title='')), y='guess', color='round', tooltip=["name", 'guess'])


    st.altair_chart(c, use_container_width=True)
   

if not showing_results and round in ['Round 1', 'Round 2']:
    guess_submitted = False
    name = st.text_input("Name")

    
    guess = st.text_input("Guess")
    if guess.isnumeric() or isfloat(guess): 
        guess = float(guess)

        if guess < 1 or guess > 100: 
            st.error("Your guess must be between 1 and 100.")
        #else:
        #    st.write(guess)
    elif guess != '': 
        st.error("Your guess must be a number between 1 and 100.")

    if st.button("Submit guess"):
        if name.strip() == '': 
            st.error("Please enter your name.")
        elif type(guess) not in [int, float] or guess < 1 or guess > 100:
            st.error("Your guess must be a number between 1 and 100.")
        else:
            if not st.session_state['already_submitted']: 
                st.session_state['already_submitted'] = True
                client = pymongo.MongoClient(st.secrets.mongodb_url)

                db = client.StableVoting.PPE
                db.update_one( {"game_name": "Guess the average", "round": round}, {"$push": {"guesses": {"name": name, "guess": guess}}}, upsert=True)
                st.write(f"Thank you, {name}, you submitted: {guess}.")
                st.balloons()
            else: 
                st.write(f"You already submitted your guess.")


