import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

# plt.rcParams["figure.figsize"] = [7.50, 3.50]
plt.rcParams["figure.figsize"] = [7.0, 4.0]
plt.rcParams["figure.autolayout"] = True


def memory_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot Memory Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # df['value'] = df['value'] / 1000000
    df['value'] = (df['value'] / 1000000)  # / 16384) * 100

    print(df.head(5))
    print(len(df))
    # print(df.dtypes)

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod Memory Usage (MiB)')
    plt.ylim(0, 80)  # scale between these values

    # for node in ('worker1', 'worker2', 'observability1', 'master'):
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]
        print(df_final.head(5))

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3)

    # plt.legend()
    # plt.grid(True)
    axes = plt.gca()
    axes.yaxis.grid()

    # plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22), xytext=(30, 150),
    #             textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()
    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)

    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def cpu_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    # df['value'] = df['value'] / 1000000
    df['value'] = (df['value'] / 1000000)

    print(len(df))
    print(df.dtypes)

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (ms)')
    plt.ylim(0, 120)  # scale between these values

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        print(len(df_app))
        df_final = df_app[["time_stamp", "host", "value"]]
        print(df_final.head(5))

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3,
                      marker='o')

    # plt.legend()
    # plt.grid(True)
    axes = plt.gca()
    axes.yaxis.grid()

    # plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22), xytext=(30, 150),
    #             textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()

    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


def network_usage_normal(input_file_name, fault_timestamp, output_file_name):
    """Plot Network Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    # df['value'] = df['value'] / 1000000
    df['value'] = (df['value'] / 1000000)

    print(len(df))
    print(df.dtypes)

    # plot lines
    plt.xlabel('Timestamp')
    plt.ylabel('Pod CPU Usage (ms)')
    plt.ylim(0, 120)  # scale between these values

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        print(len(df_app))
        df_final = df_app[["time_stamp", "host", "value"]]
        print(df_final.head(5))

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=3,
                      marker='o')

    # plt.legend()
    # plt.grid(True)
    axes = plt.gca()
    axes.yaxis.grid()

    # plt.annotate(text='Fault', xy=(mdates.date2num(datetime.fromisoformat(fault_timestamp)), 22), xytext=(30, 150),
    #             textcoords='offset pixels', arrowprops=dict(arrowstyle='-|>'))

    plt.gcf().autofmt_xdate()

    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)
    # plt.show()
    plt.savefig(output_file_name, dpi=800)


memory_usage_normal(input_file_name='telegraf_mem_result_250ms.csv', fault_timestamp='2022-06-21 08:22:40',
                    output_file_name='telegraf_pod_memory_250ms.png')

# cpu_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')

# network_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')


# python3 prometheus_data_querier.py 10.105.52.80 kubernetes_pod_container_memory_usage_bytes 2022-11-10T16:36:00.000Z 2022-11-10T16:45:00.000Z 60s | grep -e timestamp -e measurement | grep -e timestamp -e telegraf-worker | grep -v edge-metrics-analyzer >> telegraf_mem_result.csv

# python3 prometheus_data_querier.py x.x.x.x:32099 kubernetes_pod_container_memory_usage_bytes 2022-12-22T11:00:00.000Z 2022-12-22T12:11:10.000Z 10s | grep -e 'name' -e 'measurement' | grep -v -e edge-metrics-analyzer -e promtail -e master>> telegraf_mem_result.csv
