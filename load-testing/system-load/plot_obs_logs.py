import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 4.0]
plt.rcParams["figure.autolayout"] = True


def memory_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot Memory Usage"""
    df = pd.read_csv(input_file_name)
    df = df[df['container_name'] == 'promtail']
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df['value'] = df['value'] / 1000000
    # df['value'] = (df['value'] / 1000000) / 16384) * 100 # convert to percentage

    print(df.head(2))
    print(len(df))
    print(df.dtypes)

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod Memory Usage (MiB)')
    plt.ylim(0, 100)  # scale between these values

    # for node in ('worker1', 'worker2', 'observability1', 'master'):
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3)

    axes = plt.gca()
    axes.yaxis.grid()
    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)

    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def cpu_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file_name)
    df = df[df['container_name'] == 'promtail']
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print(len(df))

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (ms)')
    plt.ylim(0, 100)  # scale between these values

    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3,
                      marker='o')

    axes = plt.gca()
    axes.yaxis.grid()
    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def network_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot Network Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print(len(df))
    print(df.dtypes)

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (ms)')
    plt.ylim(0, 120)  # scale between these values

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3,
                      marker='o')

    axes = plt.gca()
    axes.yaxis.grid()
    plt.gcf().autofmt_xdate()
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


memory_usage_normal(input_file_name='loki_memory_result_50-pods.csv', fault_timestamp='2022-06-21 08:22:40',
                    output_file_name='loki_memory_result_50-pods.png')

#cpu_usage_normal(input_file_name='loki_cpu_result_50-pods.csv', fault_timestamp='2022-06-21 08:22:50',
#                 output_file_name='loki_cpu_result_50-pods.png')

# network_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')
