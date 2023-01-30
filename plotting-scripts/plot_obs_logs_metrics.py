import sys

import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 6.0]
plt.rcParams["figure.autolayout"] = True

# fig, ((ax1y1, ax1y2, ax1y3), (ax2y1, ax2y2, ax2y3)) = plt.subplots(2, 3, sharex='col', sharey='row')
fig, axs = plt.subplots(2, 3, sharex='col', sharey='row')


def plot_logs_data(input_files, sensor, label, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end,
                   legend_set, set_x_label, color, alpha):
    """Process Logs Data"""
    df_init = pd.read_csv(input_files[0])
    # sensor_count = 1
    # for sensor in sensors_list:
    df = df_init[df_init['sensor'] == sensor].copy()

    df.timestamp = pd.to_datetime(df['timestamp'])
    df_final = df.groupby([pd.Grouper(key='timestamp', freq='1min'), 'sensor']).agg(
        total_logs=('status', 'count'))
    # df_final = df.groupby([pd.Grouper(key='timestamp', freq='1min')]).count()
    df_final = df_final.reset_index()

    print(f'[plot_logs_data] - Pod: {sensor} Records: {str(len(df))}')

    create_plot(df=df_final, x_col="timestamp", y_col="total_logs", label=label, axs_row=axs_row, axs_col=axs_col,
                title=title,
                x_label=x_label, y_label=y_label,
                y_lim_start=y_lim_start, y_lim_end=y_lim_end,
                legend_set=legend_set, set_x_label=set_x_label,
                color=color, alpha=alpha)
    #    sensor_count = sensor_count + 1


def plot_metrics_data(input_files, sensor, label, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end,
                      legend_set, set_x_label, color, alpha):
    """Process CPU Usage Data"""
    df = pd.read_csv(input_files[0])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print(f'[plot_metrics_data] - Pod: {sensor} Records: {str(len(df))}')

    df_app = df[df['pod_name'] == sensor]
    df_final = df_app[["timestamp", "pod_name", "value"]]

    create_plot(df=df_final, x_col="timestamp", y_col="value", label=label, axs_row=axs_row, axs_col=axs_col,
                title=title,
                x_label=x_label, y_label=y_label,
                y_lim_start=y_lim_start, y_lim_end=y_lim_end,
                legend_set=legend_set, set_x_label=set_x_label,
                color=color, alpha=alpha)


def create_plot(df, x_col, y_col, label, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end, legend_set,
                set_x_label, color, alpha):
    """Create plots"""
    axs[axs_row, axs_col].set_title(title)
    if set_x_label:
        axs[axs_row, axs_col].set_xlabel(x_label)
    axs[axs_row, axs_col].set_ylabel(y_label)
    axs[axs_row, axs_col].set_ylim(y_lim_start, y_lim_end)  # scale between these values
    axs[axs_row, axs_col].plot(df[x_col], df[y_col], color, lw=1, label=str(label))
    axs[axs_row, axs_col].fill_between(df[x_col], df[y_col], 0, facecolor=color, alpha=alpha)
    axs[axs_row, axs_col].yaxis.grid()

    if legend_set:
        axs[axs_row, axs_col].legend(loc='center right')


def main():
    """Main function"""
    output_file = ['logs_metrics_analysis.png']

    logs_input_files = ['publisher-formatted.csv']
    sensors = ['publisher-deployment-normal-64f9f9f5df-42wdl', 'publisher-deployment-normal-64f9f9f5df-4mvxm',
               'publisher-deployment-normal-64f9f9f5df-5fdzx', 'publisher-deployment-abnormal-6867c846f9-wfkbz',
               'publisher-deployment-mixed-6b84c5654c-28fbg']

    for sensor in (0, 1, 2):
        plot_logs_data(input_files=logs_input_files, sensor=sensors[sensor], label='Sensor-' + str(sensor + 1),
                       axs_row=0,
                       axs_col=0,
                       title="Normal Pods",
                       x_label="Timestamp", y_label="Number of logs",
                       y_lim_start=0, y_lim_end=5000, legend_set=True, set_x_label=False, color='C' + str(sensor),
                       alpha=0.2)
    plot_logs_data(input_files=logs_input_files, sensor=sensors[3], label='Sensor-4', axs_row=0, axs_col=1,
                   title="Abnormal Pods",
                   x_label="Timestamp", y_label="Number of logs",
                   y_lim_start=0, y_lim_end=5000, legend_set=True, set_x_label=False, color='C3',
                   alpha=0.2)
    plot_logs_data(input_files=logs_input_files, sensor=sensors[4], label='Sensor-5', axs_row=0, axs_col=2,
                   title="Mixed Pods",
                   x_label="Timestamp", y_label="Number of logs",
                   y_lim_start=0, y_lim_end=5000, legend_set=True, set_x_label=False, color='C4',
                   alpha=0.2)

    metrics_input_files = ['faulty_sensor_cpu_usage.csv']
    for sensor in (0, 1, 2):
        plot_metrics_data(input_files=metrics_input_files, sensor=sensors[sensor], label='Sensor-' + str(sensor + 1),
                          axs_row=1, axs_col=0,
                          title="Normal Pods",
                          x_label="Timestamp", y_label="CPU Usage (ms)",
                          y_lim_start=0, y_lim_end=60, legend_set=True, set_x_label=False, color='C' + str(sensor),
                          alpha=0.2)
    plot_metrics_data(input_files=metrics_input_files, sensor=sensors[3], label='Sensor-4',
                      axs_row=1, axs_col=1,
                      title="Normal Pods",
                      x_label="Timestamp", y_label="CPU Usage (ms)",
                      y_lim_start=0, y_lim_end=60, legend_set=True, set_x_label=True,
                      color='C3', alpha=0.2)
    plot_metrics_data(input_files=metrics_input_files, sensor=sensors[4], label='Sensor-5', axs_row=1, axs_col=2,
                      title="Normal Pods",
                      x_label="Timestamp", y_label="CPU Usage (ms)",
                      y_lim_start=0, y_lim_end=60, legend_set=True, set_x_label=False,
                      color='C4', alpha=0.2)

    fig.autofmt_xdate(rotation=50)
    fig.tight_layout()
    # plt.show()
    plt.savefig(output_file[0], dpi=800)


if __name__ == '__main__':
    main()
