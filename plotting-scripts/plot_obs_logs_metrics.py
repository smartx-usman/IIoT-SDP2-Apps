import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 4.0]
plt.rcParams["figure.autolayout"] = True

# fig, (axy1, axy2) = plt.subplots(1, 2, sharex='col', sharey='row')
fig, (axy1, axy2) = plt.subplots(1, 2, sharex='col', sharey=False)


def plot_logs_data(input_files, sensors_list, subgraph):
    """Process Logs Data"""
    df_init = pd.read_csv(input_files[0])
    sensor_count = 1
    for sensor in sensors_list:
        df = df_init[df_init['sensor'] == sensor].copy()

        df.timestamp = pd.to_datetime(df['timestamp'])
        df_final = df.groupby([pd.Grouper(key='timestamp', freq='1min'), 'sensor']).agg(
            total_logs=('status', 'count'))
        # df_final = df.groupby([pd.Grouper(key='timestamp', freq='1min')]).count()
        df_final = df_final.reset_index()

        print(f'plot_logs_data: {sensor} - ' + str(len(df_final)))
        print(df_final.head(2))

        create_plot(df=df_final, label='sensor-' + str(sensor_count), subgraph=subgraph)

        sensor_count = sensor_count + 1


def plot_metrics_data(input_file_name, sensors_list, subgraph):
    """Process CPU Usage Data"""
    df = pd.read_csv(input_file_name[0])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print('plot_metrics_data: ' + str(len(df)))
    sensor_count = 1

    for container in sensors_list:
        df_app = df[df['pod_name'] == container]
        df_final = df_app[["timestamp", "pod_name", "value"]]

        create_plot(df=df_final, label='sensor-' + str(sensor_count), subgraph=subgraph)

        sensor_count = sensor_count + 1


def create_plot(df, label, subgraph):
    """Create plots"""
    if subgraph == 'axy1':
        axy1.set_title('(a) Emitted logs per minute', y=-0.42)
        axy1.set_xlabel('Timestamp')
        axy1.set_ylabel('Number of logs')
        axy1.set_ylim(0, 5000)  # scale between these values
        axy1.plot_date(df["timestamp"], df["total_logs"], label=str(label), linestyle='-', markersize=1)
        axy1.yaxis.grid()
        axy1.legend(loc='center right')
    if subgraph == 'axy2':
        axy2.set_title('(b) Pod resource usage', y=-0.42)
        axy2.set_xlabel('Timestamp')
        axy2.set_ylabel('CPU Usage (ms)')
        axy2.set_ylim(0, 60)
        axy2.plot_date(df["timestamp"], df["value"], label=str(label), linestyle='-', markersize=1)
        axy2.yaxis.grid()
        axy2.legend(loc='center right')


output_file = ['logs_metrics_analysis.png']

logs_input_files = ['publisher-formatted.csv']
sensors = ['publisher-deployment-normal-64f9f9f5df-42wdl', 'publisher-deployment-normal-64f9f9f5df-4mvxm',
           'publisher-deployment-normal-64f9f9f5df-5fdzx', 'publisher-deployment-abnormal-6867c846f9-wfkbz',
           'publisher-deployment-mixed-6b84c5654c-28fbg']

plot_logs_data(input_files=logs_input_files, sensors_list=sensors, subgraph='axy1')

metrics_input_files = ['faulty_sensor_cpu_usage.csv']
plot_metrics_data(input_file_name=metrics_input_files, sensors_list=sensors, subgraph='axy2')

fig.autofmt_xdate(rotation=50)
fig.tight_layout()
# plt.show()
plt.savefig(output_file[0], dpi=800)
