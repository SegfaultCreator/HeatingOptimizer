import appdaemon.plugins.hass.hassapi as hass
import datetime
import json

from helpers.heatingHelpers import *
from helpers.roomDefinitions import *

class HeizungsOptimierung(hass.Hass):
    def initialize(self):
        #self.run_daily(self.vorheizen_berechnen, datetime.time(19, 0, 0))
        self.vorheizen_berechnen(kwargs = {})

    def vorheizen_berechnen(self, kwargs):
        costs_entity = "sensor.tibber_prices"
        costs = self.get_costs(costs_entity)

        if not costs:
            self.log("No cost data available, skipping optimization.")
            return

        homeoffice = False # Only for testing purposes
        self.log("Homeoffice is not handled properly right now!", level="WARNING")

        room_definitions = get_room_definitions(homeoffice)

        for room_definition in room_definitions:
            self.calculate_optimal_room_settings(room_definition, costs)

    def get_costs(self, entity_id):
        """
        Fetch cost data list from a HA sensor.
        """
        state = self.get_state(entity_id, attribute="all")

        if not state:
            self.log(f"Entity {entity_id} not found!", level="ERROR")
            return []

        tomorrow_prices = state["attributes"]["tomorrow"]

        if not tomorrow_prices:
            self.log(f"Tomorrow costs not found in price list", level="Warning")
            return []
        
        costs = [entry["total"] for entry in tomorrow_prices]

        if not costs:
            self.log(f"No 'costs' attribute found for {entity_id}", level="WARNING")
            return []

        self.log(f"Tomorrow prices: {costs}")

        return costs

    def calculate_optimal_room_settings(self, room_definition, costs):
        self.log(f"Setting optimal heating config for {room_definition["name"]}")

        if len(room_definition["time_cozy"]) > 0:
            self.calculate_optimal_preheating_for_cozy_room(room_definition, costs)
        else:
            self.calculate_optimal_preheating_for_absence(room_definition, costs)

    def calculate_optimal_preheating_for_cozy_room(self, room_definition, costs):
        best_preheatings = calc_best_preheating_strategy(costs = costs, room_definition = room_definition)

        preheat_times = []
        for best_preheating_strategy in best_preheatings:
            if best_preheating_strategy["balance"] > 0:
                self.log(f"Found preheating strategy for {room_definition["name"]} at {best_preheating_strategy["time_cozy"]}")

                preheat_times.append(best_preheating_strategy["time"])

                self.create_user_notification_preheating(costs, room_definition["name"], best_preheating_strategy["time_cozy"], best_preheating_strategy["time"])


            else:        
                self.log(f"Preheating not recommended for {room_definition["name"]} at {best_preheating_strategy["time_cozy"]}")

                self.create_user_notification_no_preheating(costs, room_definition["name"], best_preheating_strategy["time_cozy"], best_preheating_strategy["time"])
        
        self.log("Preheating not correctly converted into json!!", level = "WARNING")

        # TODO: Convert into json and set variable
        #self.set_input_text_variable(
        #    entity_id = room_definition["input_text_var"],
        #    heating_config = heating_config
        #)


    def calculate_optimal_preheating_for_absence(self, room_definition, costs):
        absence_heating_strategy = calc_best_absence_strategy(costs = costs)

        if "optimal_time" in absence_heating_strategy:
            self.log(f"Found absence heating shift strategy for {room_definition["name"]}")

            self.set_input_number_variable(
                entity_id = room_definition["input_number_var"],
                value = absence_heating_strategy["optimal_time"])

            self.create_user_notification_absence_heating(room_definition["name"], absence_heating_strategy)
        else:
            self.log(f"Absence heating shift not recommended for {room_definition["name"]}")

            self.set_input_number_variable(
                entity_id = room_definition["input_number_var"],
                value = -1)

            self.create_user_notification_absence_no_heating(room_definition["name"], absence_heating_strategy)

    # Preheating_Notifications
    def create_user_notification_preheating(self, costs, room_name, time_cozy, best_preheating_time):
        title = f"AppDaemon {room_name}: Vorheizen um {best_preheating_time} Uhr für {time_cozy}"

        message = self.create_message_for_preheating_notification(costs[best_preheating_time], costs[time_cozy])

        self.call_service(
            "persistent_notification/create",
            title = title,
            message = message
            )    

    def create_user_notification_no_preheating(self, costs, room_name, time_cozy, best_preheating_time):
        title = f"AppDaemon {room_name}: Kein Vorheizen für {time_cozy} Uhr"

        message = self.create_message_for_preheating_notification(costs[best_preheating_time], costs[time_cozy])

        self.call_service(
            "persistent_notification/create",
            title = title,
            message = message
            )    

    def create_message_for_preheating_notification(self, costs_at_best_preheating_time, costs_at_cozy_time):
        return "Kosten zur Vorheizzeit: " + str(round(costs_at_best_preheating_time, 3)) + " später " + str(round(costs_at_cozy_time, 3))

    # Absence Heating Notifications
    def create_user_notification_absence_heating(self, room_name, absence_heating_strategy):
        title = f"AppDaemon {room_name}: Heizoptimum um {absence_heating_strategy["optimal_time"]} Uhr"

        message = self.create_message_for_absence_notification(costs_at_best_time = absence_heating_strategy["min_cost"], average_cost = absence_heating_strategy["average_cost"])

        self.call_service(
            "persistent_notification/create",
            title = title,
            message = message
            )    

    def create_user_notification_absence_no_heating(self, room_name, absence_heating_strategy):
        title = f"AppDaemon {room_name}: Kein Heizoptimum während Abwesenheit"

        message = self.create_message_for_absence_notification(costs_at_best_time = absence_heating_strategy["min_cost"], average_cost = absence_heating_strategy["average_cost"])

        self.call_service(
            "persistent_notification/create",
            title = title,
            message = message
            )    

    def create_message_for_absence_notification(self, costs_at_best_time, average_cost):
        return "Kosten zur Bestzeit: " + str(round(costs_at_best_time, 3)) + " Durchschnitt " + str(round(average_cost, 3))

    # Setting Time (soon deprecated)
    def set_input_number_variable(self, entity_id, value):
        self.call_service(
            "input_number/set_value",
            entity_id = entity_id,
            value = value
        )

    # Setting Time
    def set_input_text_variable(self, entity_id, heating_config):
        self.call_service(
            "input_text/set_value",
            entity_id = entity_id,
            value = heating_config
        )

