import os

import numpy as np
import pandas
import matplotlib.pyplot as plt
from pymongo.database import Database
from bson.objectid import ObjectId


COLORS = {'death': 'black', 'recoveries': 'blue', 'active': 'red', 'total': 'orange'}


def load_data_frame(db: Database):
    cases_collection = db.get_collection('cases')
    countries_collection = db.get_collection('countries')

    countries = set([x['country'] for x in cases_collection.find()])
    df = None
    for index, country in enumerate(countries):
        os.system('clear')
        print(f'Loading data frame {100 * index // len(countries)}%...')

        country_id = cases_collection.find_one({'country': country})['country_id']
        population = countries_collection.find_one({'_id': ObjectId(country_id)})['population']
        cases = cases_collection.find({'country': country}).sort('date', 1)
        case = next(cases)
        dates, deaths = [case['date']], [case['deaths']]
        recoveries, active, days = [case['recoveries']], [case['active']], [1]
        for case in cases:
            dates.append(case['date'])
            deaths.append(case['deaths'])
            recoveries.append(case['recoveries'])
            active.append(case['active'])
            days.append((case['date'] - dates[0]).days + 1)

        total = np.add(deaths, np.add(recoveries, active))
        country_df = pandas.DataFrame({'country': [country] * len(dates), 'date': dates, 'day': days,
                                       'recoveries': recoveries, 'deaths': deaths, 'active': active,
                                       'total': total,
                                       'recoveries percent': _property_in_percent(recoveries, population),
                                       'deaths percent': _property_in_percent(deaths, population),
                                       'active percent': _property_in_percent(active, population),
                                       'total percent': _property_in_percent(total, population)})

        if df is None:
            df = country_df
        else:
            df = pandas.concat([df, country_df], ignore_index=True)

    return df.drop_duplicates(['country', 'date'])


def _property_in_percent(props, population):
    return np.multiply([100 * 1_000_000 / population] * len(props), props)


def plot_countries_stats(df, prop, countries=None):
    if not countries:
        countries = set(df['country'])

    for country in countries:
        country_df = df[df['country'] == country]
        x = country_df['day']
        y = country_df[prop]
        plt.plot(x, y, color=np.random.rand(3,), label=country)
    plt.xlabel('days from first covid registration')
    plt.ylabel(f'{prop} cases')
    plt.legend(loc='upper left')
    plt.show()


