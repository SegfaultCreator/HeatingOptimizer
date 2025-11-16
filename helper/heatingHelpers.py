# helpers.py

import math

def calc_hourly_extra_consumption(temp_baseline, temp_cozy, consumption_daily_16_deg):
    consumption_hourly_16 = consumption_daily_16_deg / 24

    consumption_hourly_baseline = consumption_hourly_16 * math.pow(1.07, temp_baseline - 16)
    consumption_hourly_cozy = consumption_hourly_16 * math.pow(1.07, temp_cozy - 16)

    extra_consumption = consumption_hourly_cozy - consumption_hourly_baseline

    return extra_consumption

def calc_best_preheating_strategy(costs, room_definition):
    # Calc extra consumption per hour
    extra_consumption_hourly = calc_hourly_extra_consumption(temp_baseline = room_definition["temp_baseline"], temp_cozy = room_definition["temp_cozy"], consumption_daily_16_deg = room_definition["consumption_daily_16_deg"])

    best_preheatings = []
    
    for time_cozy in room_definition["time_cozy"]:
        best_preheating = {}
        best_preheating["time_cozy"] = time_cozy
        best_preheating["time"] = 0
        best_preheating["balance"] = -100

        for preheat_hour in range(0, time_cozy):
            additional_warm_period = time_cozy - preheat_hour
            extra_consumption_for_preheating = extra_consumption_hourly * additional_warm_period

            # Shifted Consumption Through earlier heating 
            shifted_consumption = room_definition["power_of_heating"] * 1 # Assuming heating is running full-time
            cost_reduction_shift = shifted_consumption * (costs[time_cozy] - costs[preheat_hour])

            # Calc balance
            preheating_cost = extra_consumption_for_preheating * costs[preheat_hour]
            total_balance = cost_reduction_shift - preheating_cost

            if(total_balance > best_preheating["balance"]):
                best_preheating["balance"]  = total_balance
                best_preheating["time"]  = preheat_hour
                best_preheating["extra_consumption_kwh"] = extra_consumption_for_preheating
                best_preheating["cost_through_extra"] = preheating_cost
                best_preheating["cost_reduction_through_shift"] = cost_reduction_shift

        best_preheatings.append(best_preheating)

    return best_preheatings

# If one time is much lower than the average -> Select that time for heating
def calc_best_absence_strategy(costs):
    min_cost = min(costs)
    min_idx = costs.index(min_cost)

    avg_cost = sum(costs) / len(costs)

    cost_difference = avg_cost - min_cost

    absence_heating_strategy = {}
    absence_heating_strategy["min_cost"] = min_cost
    absence_heating_strategy["average_cost"] = avg_cost

    if cost_difference > 0.02 :
        absence_heating_strategy["optimal_time"]  = min_idx
    
    return absence_heating_strategy

    
