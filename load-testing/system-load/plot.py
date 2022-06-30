from datetime import datetime

import pandas as pd
from matplotlib import pyplot as plt, dates as mdates

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.figsize"] = [7.0, 4.0]
plt.rcParams["figure.autolayout"] = True


# Plot Memory Usage
def memory_usage_normal(input_file_name, fault_timestamp, output_file_name):
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = df['value'] / 1000000

    print(df.head(5))
    print(len(df))

    # plt.show()
    x = [10, 20, 30, 40, 50]
    y = [30, 30, 30, 30, 30]

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod Memory Usage (Mbyte)')

    for app in range(1, 5):
        df_app = df[df['pod_name'] == f'app-{app}-pod']
        df_final = df_app[["time_stamp", "pod_name", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label="app-" + str(app) + "-pod", linestyle='-',
                      markersize=3)

    plt.legend()
    # plt.grid(True)
    axes = plt.gca()
    axes.yaxis.grid()

    plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22), xytext=(30, 150),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()
    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=4)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def memory_usage_abnormal(input_file_name, fault_timestamp, recovery_timestamp, output_file_name, filter_date):
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = df['value'] / 1000000

    print(df.head(5))
    print(len(df))

    if filter_date:
        df = df[df['time_stamp'] > '2022-06-22 10:53:00']
        df = df[df['time_stamp'] < '2022-06-22 10:59:00']
        print(len(df))

    plt.xlabel('Timestamp')
    plt.ylabel('Pod Memory Usage (Mbyte)')

    df_app_names = df['pod_name'].unique()

    for app in df_app_names:
        df_app = df[df['pod_name'] == app]
        # df_app = df.loc[df['pod_name'].str.contains(f'app-{app}-pod', case=False)]
        print(len(df_app))
        df_final = df_app[["time_stamp", "pod_name", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label="" + str(app)[:-14], linestyle='-', markersize=3)

    plt.legend()
    axes = plt.gca()
    axes.yaxis.grid()

    plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22),
                 xytext=(30, 150),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))
    plt.annotate(text='Recovery', xy=(mdates.date2num(datetime.fromisoformat(recovery_timestamp)), 22),
                 xytext=(30, 150),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=4)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


# Plot CPU Usage
def cpu_usage_normal(input_file_name, fault_timestamp, output_file_name):
    df = pd.read_csv(input_file_name)

    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')
    # df['value'] = df['value'] / 1000000

    print(len(df.head(5)))

    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (Nanocores)')

    for app in range(1, 5):
        df_app = df[df['pod_name'] == f'app-{app}-pod']
        df_final = df_app[["time_stamp", "pod_name", "value"]]
        print(df_final.head(10))

        plt.plot_date(df_final["time_stamp"], df_final["value"], label="app-" + str(app) + "-pod", linestyle='-',
                      markersize=3)

    plt.legend()
    axes = plt.gca()
    axes.yaxis.grid()

    plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22), xytext=(30, 150),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=4)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def cpu_usage_abnormal(input_file_name, fault_timestamp, recovery_timestamp, output_file_name, filter_date):
    df = pd.read_csv(input_file_name)

    print(df.head(5))
    print(len(df))

    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = df['value'] / 1000000

    if filter_date:
        df = df[df['time_stamp'] > '2022-06-22 10:53:00']
        df = df[df['time_stamp'] < '2022-06-22 10:59:00']
        print(len(df))

    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (Nanocores)')

    df_app_names = df['pod_name'].unique()

    for app in (df_app_names):
        df_app = df[df['pod_name'] == app]
        df_final = df_app[["time_stamp", "pod_name", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label="" + str(app)[:-14], linestyle='-', markersize=3)

    plt.legend()
    axes = plt.gca()
    axes.yaxis.grid()

    plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22),
                 xytext=(20, 190),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))
    plt.annotate(text='Recovery', xy=(mdates.date2num(datetime.fromisoformat(recovery_timestamp)), 22),
                 xytext=(40, 150),
                 textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=4)
    # plt.show()
    plt.savefig(output_file_name, dpi=1200)


# memory_usage_normal(input_file_name='pod_memory_1.csv', fault_timestamp='2022-06-21 08:22:40',
#                    output_file_name='monitoring_pod_memory_1.png')

# memory_usage_abnormal(input_file_name='pod_memory_2.csv', fault_timestamp='2022-06-22 10:54:40',
#                      recovery_timestamp='2022-06-22 10:55:40', output_file_name='monitoring_pod_memory_2.png',
#                      filter_date=True)

# cpu_usage_normal(input_file_name='pod_cpu_cores_1.csv', fault_timestamp='2022-06-21 08:22:50',
#                output_file_name='monitoring_pod_cpu_1.png')

cpu_usage_abnormal(input_file_name='pod_cpu_cores_2.csv', fault_timestamp='2022-06-22 10:55:00',
                   recovery_timestamp='2022-06-22 10:55:40', output_file_name='monitoring_pod_cpu_2.png',
                   filter_date=True)
