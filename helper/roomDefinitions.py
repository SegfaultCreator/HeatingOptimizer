def get_room_definitions(homeoffice : bool):
    room_definitions = []

    room_definitions.append(get_room_definition_living_room())
    room_definitions.append(get_room_definition_bathroom(homeoffice))
    room_definitions.append(get_room_definition_office(homeoffice))

    return room_definitions

def get_room_definition_office(homeoffice : bool):
    room_definition = {
        "name" : "Arbeitszimmer",
        "temp_baseline" : 17.5,
        "temp_cozy" : 20,
        "time_cozy" : [],
        "consumption_daily_16_deg" : 4.68,
        "power_of_heating" : 1.55,
        "input_number_var" : "input_number.preheating_office_time"
        }
        
    if homeoffice: # Only has cozy time when in homeoffice mode
        room_definition["time_cozy"].append(7)

    return room_definition

def get_room_definition_bathroom(homeoffice : bool):
    room_definition = {
        "name" : "Bad",
        "temp_baseline" : 18,
        "temp_cozy" : 20.5,
        "consumption_daily_16_deg" : 4.68,
        "power_of_heating" : 1.55,
        "input_number_var" : "input_number.preheating_bathroom_time"
        }
        
    if homeoffice:
        room_definition["time_cozy"] = [6]
    else:
        room_definition["time_cozy"] = [5]

    # TODO: Think of how to handle the two-stepped increase in evening
    room_definition["time_cozy"].append(18)

    return room_definition


def get_room_definition_living_room():
    return {
        "name" : "Wohnzimmer",
        "temp_baseline" : 18,
        "temp_cozy" : 20,
        "time_cozy" : [18],
        "consumption_daily_16_deg" : 11.05,
        "power_of_heating" : 3.05,
        "input_number_var" : "input_number.preheating_living_room_morning_time"
    }
