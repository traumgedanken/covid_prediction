import datetime
import os

import bson
import matplotlib.pyplot as plt
import numpy as np
import pandas
from scipy.optimize import curve_fit
from bson.objectid import ObjectId
from pymongo.database import Database
from sklearn.cluster import AgglomerativeClustering

COLORS = {'death': 'black', 'recoveries': 'blue', 'active': 'red', 'total': 'orange'}


def load_data_frame(db: Database):
    cases_collection = db.get_collection('cases')

    countries = set([x['country'] for x in cases_collection.find()])
    df = None
    for index, country in enumerate(countries):
        os.system('clear')
        print(f'Loading data frame {100 * index // len(countries)}%...')

        population = _country_population(db, country)
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
                                       'total': total, 'population': [population] * len(total),
                                       'percent recoveries': _property_in_percent(recoveries, population),
                                       'percent deaths': _property_in_percent(deaths, population),
                                       'percent active': _property_in_percent(active, population),
                                       'percent total': _property_in_percent(total, population)})

        if df is None:
            df = country_df
        else:
            df = pandas.concat([df, country_df], ignore_index=True)

    return df.drop_duplicates(['country', 'date'])


def plot_countries_stats(df, prop, countries=(), exceptions=()):
    if not countries:
        countries = set(df['country'])

    for country in set(countries).difference(set(exceptions)):
        country_df = df[df['country'] == country]
        x = country_df['day']
        y = country_df[prop]
        plt.plot(x, y, color=np.random.rand(3,), label=country)
    plt.xlabel('days from first covid registration')
    plt.ylabel(f'{prop.replace("percent ", "")} cases, '
               f'{"10^-6 % from country population" if prop.startswith("percent") else "person"}')
    plt.legend(loc='upper left', fontsize=8)
    plt.grid(color='grey')
    plt.show()


def plot_prediction(df, prop, country, graphic_mode=True):
    country_siblings_df = df[df['country'].isin(_country_cluster_siblings(df, prop, country))]
    country_days = df[df['country'] == country]['day']
    country_props = df[df['country'] == country][prop]
    percent_prop = f'percent {prop}'
    country_percent_props = df[df['country'] == country][percent_prop]
    x = np.array(country_siblings_df['day'])
    y = np.array(country_siblings_df[percent_prop])

    population = df[df['country'] == country]['population'].iloc[0]
    x_pred, y_pred = _curve_regression(x, y, prop_regression_funcs[prop])
    x_pred, y_pred = _curve_regression(np.append(x_pred, country_days),
                                       np.append(y_pred, country_percent_props),
                                       prop_regression_funcs[prop])
    y_pred = _percent_property_in_counts(y_pred, population)
    y_pred = _scale_prediction(country_days.iloc[-1], country_props.iloc[-1], x_pred, y_pred)

    if graphic_mode:
        labels = _days_to_dates(x_pred, df[df['country'] == country]['date'].iloc[0])
        plt.xticks(x_pred, labels, fontsize=8, rotation=45)
        plt.plot(country_days, country_props, label='real values')
        plt.plot(x_pred, y_pred, color='red', label='predicted values')
        plt.grid(color='grey')
        plt.xlabel('date')
        plt.ylabel(f'{prop} cases in sum, person')
        plt.legend(loc='upper left')
        plt.show()
    return (country_days, country_props), (x_pred, y_pred)


def plot_derivative_prediction(df, prop, country):
    (x_real, y_real), (x_pred, y_pred) = plot_prediction(df, prop, country, graphic_mode=False)
    labels = _days_to_dates(x_pred, df[df['country'] == country]['date'].iloc[0])
    y_real_der = np.gradient(y_real, 1)
    y_pred_der = _scale_prediction(np.array(x_real)[-1], np.array(y_real_der)[-1],
                                   x_pred, np.gradient(y_pred, 1))

    plt.xticks(x_pred, labels, fontsize=8, rotation=45)
    plt.plot(x_real, y_real_der, label='real values')
    plt.plot(x_pred, y_pred_der, color='red', label='predicted values')
    plt.grid(color='grey')
    plt.xlabel('date')
    plt.ylabel(f'new {prop} cases for this day, person')
    plt.legend(loc='upper left')
    plt.show()


def _country_population(db, country):
    cases_collection = db.get_collection('cases')
    countries_collection = db.get_collection('countries')
    try:
        country_id = cases_collection.find_one({'country': country})['country_id']
        return countries_collection.find_one({'_id': ObjectId(country_id)})['population']
    except bson.errors.InvalidId:
        return None


def _property_in_percent(props, population):
    scale = 100 * 1_000_000 / population
    return np.array(props) * scale


def _percent_property_in_counts(props, population):
    scale = population / (100 * 1_000_000)
    return np.array(props) * scale


def _cluster_countries(df, prop):
    countries = set(df['country'])
    max_prop_values = np.array([max(df[df['country'] == c][prop]) for c in countries]).reshape(-1, 1)
    model = AgglomerativeClustering(n_clusters=5)

    clusters = dict()
    for country, cluster in zip(countries, model.fit_predict(max_prop_values, countries)):
        if not clusters.get(cluster, None):
            clusters[cluster] = []
        clusters[cluster].append(country)
    return clusters


def _country_cluster_siblings(df, prop, country):
    clusters = _cluster_countries(df, prop)
    for cluster, countries in clusters.items():
        if country in countries:
            return countries


def _curve_regression(x_data, y_data, func):
    popt, pcov = curve_fit(func, x_data, y_data, maxfev=800)
    x_pred = np.linspace(0, max(x_data), dtype=int, num=30)
    y_pred = func(x_pred, *popt)
    return x_pred, y_pred


prop_regression_funcs = {
    'total': lambda x, a, b, c, d: a * np.arctan(b * x + c) + d,
    'deaths': lambda x, a, b, c, d: a * np.arctan(b * x + c) + d,
    'recoveries': lambda x, a, b, c: a * x * x + b * x + c,
    'active': lambda x, a, b, c: a * x * x + b * x + c
}


def _days_to_dates(days, start_date_time):
    dates = [start_date_time + datetime.timedelta(days=int(day)) for day in days]
    return [' '.join(d.ctime().split()[1:3][::-1]) for d in dates]


def _scale_prediction(last_x_real, last_y_real, x_pred, y_pred):
    last_country_day_predicted_value = y_pred[x_pred >= last_x_real][0]
    return y_pred * (last_y_real / last_country_day_predicted_value)
