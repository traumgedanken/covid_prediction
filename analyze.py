import storage
import data_mining

db = storage.get_db_instance()
df = data_mining.load_data_frame(db)

data_mining.plot_prediction(df, 'recoveries', 'Ukraine')
# data_mining.plot_countries_stats(df, 'deaths percent', ['Japan', 'Ukraine'])