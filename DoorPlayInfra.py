import streamlit as st
import pandas as pd
import random
import time
import os

MIN_LOCATION = -1.1
MAX_LOCATION = 1.85
WAIT_TIME_ON_DOOR = 4

SOUNDS = {
    "lock": "./sounds/click_1s.wav",
    "reward": "./sounds/new_reward.mp3",
    "punishment": "./sounds/monster.mp3",
    "beep": "./sounds/beep_for_anticipation.mp3"
}

MESSAGES = {
    "MIDDLE_SUMMARY_STR1_HE": "בואו ננוח מעט.\n",
    "MIDDLE_SUMMARY_STR2Key_HE": "לחצו על הרווח כשאתם מוכנים להמשיך.",
    "MIDDLE_SUMMARY_STR2Joy_HE": "לחצו על הג'ויסטיק כשאתם מוכנים להמשיך.",
    "MIDDLE_SUMMARY_STR1_EN": "Let's rest a bit.\n",
    "MIDDLE_SUMMARY_STR2Key_EN": "Press the spacebar when you're ready.",
    "MIDDLE_SUMMARY_STR2Joy_EN": "Press the joystick when you're ready.",
    "FINAL_SUMMARY_STR1_EN": "You scored ",
    "FINAL_SUMMARY_STR2_EN": "Coins!\n Well done!\n\nThank you for your participation.",
    "FINAL_SUMMARY_STR1_HE": "צברת ",
    "FINAL_SUMMARY_STR2_HE": "מטבעות\n כל הכבוד!\n\n תודה על השתתפותך בניסוי."
}

def normalize_location(location):
    if location > MAX_LOCATION:
        location = MAX_LOCATION
    elif location < MIN_LOCATION:
        location = MIN_LOCATION

    if location > 0:
        location_normalized = round((location * 100) / MAX_LOCATION)
    else:
        location_normalized = round((location * 100) / (-1 * MIN_LOCATION))

    return round(location_normalized / 2 + 50)

def update_movement_in_dict(dict_for_df, location_normalized):
    dict_for_df['CurrentTime'] = round(time.time() - dict_for_df['StartTime'], 2)
    dict_for_df['CurrentDistance'] = location_normalized
    if location_normalized > dict_for_df.get('Distance_max', 0):
        dict_for_df['Distance_max'] = location_normalized
    if location_normalized < dict_for_df.get('Distance_min', 100):
        dict_for_df['Distance_min'] = location_normalized

    return dict_for_df

def setup_door(params, reward, punishment, scale):
    random.seed()
    if params['startingDistance'] == 'Random':
        location = round(random.uniform(MIN_LOCATION, MAX_LOCATION), 2)
    elif params['startingDistance'] == '40-60':
        location = round(random.uniform(MIN_LOCATION / 5, MAX_LOCATION / 5), 2)
    else:
        location = 0

    image_path = f"{params['doorImagePathPrefix']}p{punishment}r{reward}{params['imageSuffix']}"

    st.image(image_path, caption=f"Reward: {reward}, Punishment: {punishment}", use_column_width=False, width=int(500 * scale))
    return location

def move_screen(location, units):
    location += units / 100
    location = normalize_location(location)
    return location

def play_sound(sound_type):
    sound_path = SOUNDS.get(sound_type)
    if sound_path and os.path.exists(sound_path):
        st.audio(sound_path, format="audio/wav")
    else:
        st.warning(f"Sound file for {sound_type} not found.")

def inter_trial_interval(iti_time):
    st.write("Inter-trial interval (ITI) phase...")
    progress = st.progress(0)
    for i in range(100):
        time.sleep(iti_time / 100)
        progress.progress(i + 1)

def display_message(key):
    if key in MESSAGES:
        st.write(MESSAGES[key])

def prompt_user_ready():
    display_message("MIDDLE_SUMMARY_STR1_EN")
    st.write("Press the button when you're ready.")
    if st.button("Ready"):
        st.write("Proceeding...")

def show_screen_pre_match(params, session):
    if session in [2, 3]:
        if params["language"] == "Hebrew":
            message = MESSAGES["MIDDLE_SUMMARY_STR1_HE"] + (MESSAGES["MIDDLE_SUMMARY_STR2Key_HE"] if params["keyboardMode"] else MESSAGES["MIDDLE_SUMMARY_STR2Joy_HE"])
        else:
            message = MESSAGES["MIDDLE_SUMMARY_STR1_EN"] + (MESSAGES["MIDDLE_SUMMARY_STR2Key_EN"] if params["keyboardMode"] else MESSAGES["MIDDLE_SUMMARY_STR2Joy_EN"])
        st.write(message)
    else:
        screen_names = ["practice_start", "start_main_game"]
        image_path = f"./img/Instructions{'Hebrew' if params['language'] == 'Hebrew' else 'English'}/{screen_names[session]}.jpeg"
        st.image(image_path, caption="Instruction Screen", use_column_width=True)
    st.button("Continue")

def show_screen_post_simulation(params):
    image_path = f"./img/Instructions{'Hebrew' if params['language'] == 'Hebrew' else 'English'}/SimulationRunEnd.jpeg"
    st.image(image_path, caption="Simulation End", use_column_width=True)
    st.button("Continue")

def show_wheel(params):
    award_choice = random.choice([5, 6, 7])
    movie_path = f"./img/Wheels/{award_choice}_{params['language'][:3]}.mp4"
    st.video(movie_path)
    st.button("Continue")

def show_screen_post_match(params, coins=0):
    if params["language"] == "Hebrew":
        message = MESSAGES["FINAL_SUMMARY_STR1_HE"] + f"{coins} " + MESSAGES["FINAL_SUMMARY_STR2_HE"]
    else:
        message = MESSAGES["FINAL_SUMMARY_STR1_EN"] + f"{coins} " + MESSAGES["FINAL_SUMMARY_STR2_EN"]
    st.write(message)
    st.button("Finish")

def start_door(params, reward, punishment, total_coins, dict_for_df, miniDf, summary_df, highValue=False, scenarioIndex=0):
    scale = 1.0
    location = setup_door(params, reward, punishment, scale)
    dict_for_df['DistanceAtStart'] = location * 100

    # Initialize tracking variables
    dict_for_df['Distance_max'] = round(normalize_location(location))
    dict_for_df['Distance_min'] = round(normalize_location(location))
    dict_for_df['ScenarioIndex'] = scenarioIndex
    start_time = time.time()

    st.write(f"Starting at location: {location}")

    forward_pressed = st.button("Move Forward")
    backward_pressed = st.button("Move Backward")

    if forward_pressed:
        location = move_screen(location, 10)  # Move closer by a fixed unit
        scale = max(0.5, min(2.0, scale + 0.1))  # Adjust scale closer
    elif backward_pressed:
        location = move_screen(location, -10)  # Move farther by a fixed unit
        scale = max(0.5, min(2.0, scale - 0.1))  # Adjust scale farther

    location_normalized = normalize_location(location)
    dict_for_df = update_movement_in_dict(dict_for_df, location_normalized)

    setup_door(params, reward, punishment, scale)

    # Simulate door opening logic
    door_open_chance = random.random()
    is_door_opening = door_open_chance <= (location / 100)
    dict_for_df["Door_opened"] = 1 if is_door_opening else 0
    dict_for_df["DoorStatus"] = 'opened' if is_door_opening else 'closed'

    st.write(f"Door Opening: {'Yes' if is_door_opening else 'No'}")

    if is_door_opening:
        reward_chance = random.random()
        if reward_chance >= 0.5:
            coins = reward
            dict_for_df["DidWin"] = 1
            dict_for_df["Door_outcome"] = "reward"
            dict_for_df["ScenarioIndex"] = scenarioIndex + 100
            st.success(f"You earned {coins} coins!")
            play_sound("reward")
        else:
            coins = -1 * punishment
            dict_for_df["DidWin"] = 0
            dict_for_df["Door_outcome"] = "punishment"
            dict_for_df["ScenarioIndex"] = scenarioIndex + 200
            st.error(f"You lost {-coins} coins!")
            play_sound("punishment")
        total_coins += coins
    else:
        st.warning("The door did not open.")
        play_sound("lock")
        dict_for_df["ScenarioIndex"] = scenarioIndex + 50

    dict_for_df['Total_coins'] = total_coins
    dict_for_df["CurrentTime"] = round(time.time() - dict_for_df['StartTime'], 2)

    # Total time and scenario tracking
    total_time = time.time() - start_time
    dict_for_df["DoorAction_RT"] = round(total_time * 1000, 2)

    # Door anticipation time logic
    door_wait_time = 3 + random.random()
    dict_for_df["Door_anticipation_time"] = door_wait_time * 1000
    time.sleep(door_wait_time)

    # ITI phase
    iti_time = random.uniform(params['ITIDurationMin'], params['ITIDurationMax'])
    inter_trial_interval(iti_time)

    if highValue:
        st.write("High value condition triggered!")

    return total_coins, dict_for_df, miniDf, summary_df

def final_summary(total_coins, language="EN"):
    if language == "HE":
        message = f"{MESSAGES['FINAL_SUMMARY_STR1_HE']}{total_coins}{MESSAGES['FINAL_SUMMARY_STR2_HE']}"
    else:
        message = f"{MESSAGES['FINAL_SUMMARY_STR1_EN']}{total_coins}{MESSAGES['FINAL_SUMMARY_STR2_EN']}"
    st.write(message)