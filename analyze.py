import storage
import data_mining

db = storage.get_db_instance()
df = data_mining.load_data_frame(db)

data_mining.plot_derivative_prediction(df, 'deaths', ['Belgium'])
# data_mining.plot_countries_stats(df, 'deaths percent', ['Japan', 'Ukraine'])