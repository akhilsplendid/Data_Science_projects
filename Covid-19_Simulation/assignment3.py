import pandas as pd
from datetime import datetime, timedelta
import random
from helper import create_plot


from sim_parameters import TRASITION_PROBS, HOLDING_TIMES


def read_countries_data(countries_csv_name):
    return pd.read_csv(countries_csv_name)


def create_sample_population(df, countries, sample_ratio):
    samples = []
    for country in countries:
        coun = df[df["country"] == country]
        print(coun)
        country_data = df[df["country"] == country].iloc[0]
        print('--------------------------------')
        print(country_data)
        population = country_data["population"]
        total_samples = int(round(population / sample_ratio))
        print(total_samples)
        for age_group in ["less_5", "5_to_14", "15_to_24", "25_to_64", "over_65"]:
            age_group_percentage = country_data[age_group]
            age_group_samples = int(round(total_samples * (age_group_percentage / 100)))
            print(age_group_samples)
            print(age_group_percentage)
            for _ in range(age_group_samples):
                samples.append((country, age_group))
    
    print(samples)
    return samples


def simulate_individual(sample, start_date, end_date, transition_probs, holding_times):
    current_state = "H"
    current_date = start_date
    holding_time = 0
    individual_timeline = {}
    while current_date <= end_date:
        if holding_time == 0:
            probabilities = transition_probs[sample[1]][current_state]
            next_state = random.choices(
                list(probabilities.keys()), weights=probabilities.values(), k=1
            )[0]
            current_state = next_state
            holding_time = holding_times[sample[1]][current_state]
            if holding_time == 0:
                holding_time = 1
        individual_timeline[current_date] = current_state
        current_date += timedelta(days=1)
        holding_time -= 1

    # print(individual_timeline)
    return individual_timeline


def summarize_data(simulated_df):
    summary = (
        simulated_df.groupby(["date", "country", "state"]).size().unstack(fill_value=0)
    )
    return summary.reset_index()


def export_to_csv(data, filename):
    data.to_csv(filename, index=False)


def run(countries_csv_name, countries, start_date, end_date, sample_ratio):
    df = read_countries_data(countries_csv_name)
    samples = create_sample_population(df, countries, sample_ratio)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    print(df)
    simulated_data = []
    # print("----------------------------------------------------------------")
    # print(samples)
    for sample in samples:
        individual_timeline = simulate_individual(
            sample, start, end, TRASITION_PROBS, HOLDING_TIMES
        )
        prev_state = "H"  # Initial previous state
        staying_days = 0
        for date, state in individual_timeline.items():
            if state == prev_state:
                staying_days += 1
            else:
                staying_days = 1  # Reset staying days if state changes

            simulated_data.append(
                {
                    "person_id": samples.index(sample),
                    "age_group_name": sample[1],
                    "country": sample[0],
                    "date": date.strftime("%Y-%m-%d"),
                    "state": state,
                    "staying_days": staying_days,
                    "prev_state": prev_state,
                }
            )
            prev_state = state  # Update previous state for next iteration

    time_series_data = pd.DataFrame(simulated_data)
    export_to_csv(time_series_data, "a3-covid-simulated-timeseries.csv")

    summary_data = summarize_data(time_series_data)
    export_to_csv(summary_data, "a3-covid-summary-timeseries.csv")

    summary_csv_path = "a3-covid-summary-timeseries.csv"

    create_plot(summary_csv_path, countries)
