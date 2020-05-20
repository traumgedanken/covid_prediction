from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.validation import Validator, ValidationError
from consolemenu import SelectionMenu

import storage
import data_mining

df = data_mining.load_data_frame(storage.get_db_instance())
all_countries = set(df['country'])


def prompt(msg, choices, empty_allowed=True):
    class FooValidator(Validator):
        def validate(self, document):
            if not empty_allowed and document.text not in choices:
                raise ValidationError(
                    message='Invalid input',
                    cursor_position=len(document.text))

    history = InMemoryHistory()
    for country in choices:
        history.append_string(country)
    session = PromptSession(
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=True,
        validator=FooValidator()
    )
    return session.prompt(f'{msg}:  ')


def main_menu():
    menu = SelectionMenu([
        'Plot countries statistic',
        'Plot prediction',
        'Plot derivative prediction'
    ], title="Select a task to do")
    menu.show()

    if menu.is_selected_item_exit():
        return

    next_steps = [stats, prediction, derivative_prediction]
    next_steps[menu.selected_option]()


def stats():
    prop = prompt('Select property to analise', ['deaths', 'recoveries', 'active', 'total',
                                                 'percent deaths', 'percent recoveries',
                                                 'percent active', 'percent total'],
                  empty_allowed=False)
    countries = []
    while country := prompt('Select a country to plot data', all_countries):
        countries.append(country)
    exceptions = []
    while not countries and (country := prompt('Select a country for exceptions', all_countries)):
        exceptions.append(country)
    data_mining.plot_countries_stats(df, prop, countries, exceptions)
    main_menu()


def prediction():
    prop = prompt('Select property to predict', ['deaths', 'recoveries', 'active', 'total'], empty_allowed=False)
    country = prompt('Select country', all_countries, empty_allowed=False)
    data_mining.plot_prediction(df, prop, country)
    main_menu()


def derivative_prediction():
    prop = prompt('Select property to predict', ['deaths', 'recoveries', 'active', 'total'], empty_allowed=False)
    country = prompt('Select country', all_countries, empty_allowed=False)
    data_mining.plot_derivative_prediction(df, prop, country)
    main_menu()


if __name__ == '__main__':
    main_menu()
