import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 6.0]
plt.rcParams["figure.autolayout"] = True

fig, ((ax1y1, ax1y2, ax1y3), (ax2y1, ax2y2, ax2y3)) = plt.subplots(2, 3, sharex='col', sharey='row')


def memory_usage(input_file_name, subgraph):
    """Plot Memory Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df['value'] = (df['value'] / 1000000)  # / 16384) * 100

    print(df.head(5))
    print(len(df))

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]
        print(df_final.head(5))

        if subgraph == 'ax1y1':
            ax1y1.set_title('250ms')
            ax1y1.set_xlabel('Timestamp')
            ax1y1.set_ylabel('Memory Usage (MiB)')
            ax1y1.set_ylim(0, 80)  # scale between these values
            ax1y1.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y1.yaxis.grid()
        elif subgraph == 'ax1y2':
            ax1y2.set_title('1s')
            ax1y2.set_xlabel('Timestamp')
            ax1y2.set_ylabel('Memory Usage (MiB)')
            ax1y2.set_ylim(0, 80)  # scale between these values
            ax1y2.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y2.yaxis.grid()
        else:
            ax1y3.set_title('10s')
            ax1y3.set_xlabel('Timestamp')
            ax1y3.set_ylabel('Memory Usage (MiB)')
            ax1y3.set_ylim(0, 80)  # scale between these values
            ax1y3.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y3.yaxis.grid()
            ax1y3.legend(loc='lower right')


def cpu_usage(input_file_name, subgraph):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file_name)
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print(df.dtypes)

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        print(len(df_app))
        df_final = df_app[["time_stamp", "host", "value"]]
        print(df_final.head(5))

        if subgraph == 'ax2y1':
            ax2y1.set_title('250ms')
            ax2y1.set_xlabel('Timestamp')
            ax2y1.set_ylabel('CPU Usage (ms)')
            ax2y1.set_ylim(0, 100)  # scale between these values
            ax2y1.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y1.yaxis.grid()
        elif subgraph == 'ax2y2':
            ax2y2.set_title('1s')
            ax2y2.set_xlabel('Timestamp')
            ax2y2.set_ylabel('CPU Usage (ms)')
            ax2y2.set_ylim(0, 100)  # scale between these values
            ax2y2.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y2.yaxis.grid()
        else:
            ax2y3.set_title('10s')
            ax2y3.set_xlabel('Timestamp')
            ax2y3.set_ylabel('CPU Usage (ms)')
            ax2y3.set_ylim(0, 100)  # scale between these values
            ax2y3.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y3.yaxis.grid()


def network_usage(input_file_name, fault_timestamp, output_file_name):
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


output_file = ['telegraf_resource_usage.png']
input_file = ['telegraf_mem_result_250ms.csv', 'telegraf_mem_result_1s.csv', 'telegraf_mem_result_10s-master.csv',
              'telegraf_cpu_result_250ms.csv', 'telegraf_cpu_result_1s.csv', 'telegraf_cpu_result_10s-master.csv']

memory_usage(input_file_name=input_file[0], subgraph='ax1y1')
memory_usage(input_file_name=input_file[1], subgraph='ax1y2')
memory_usage(input_file_name=input_file[2], subgraph='ax1y3')

cpu_usage(input_file_name=input_file[3], subgraph='ax2y1')
cpu_usage(input_file_name=input_file[4], subgraph='ax2y2')
cpu_usage(input_file_name=input_file[5], subgraph='ax2y3')

# cpu_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')

# network_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')

fig.autofmt_xdate(rotation=50)
fig.tight_layout()
# plt.show()
plt.savefig(output_file[0], dpi=800)

# python3 prometheus_data_querier.py 10.105.52.80 kubernetes_pod_container_memory_usage_bytes 2022-11-10T16:36:00.000Z 2022-11-10T16:45:00.000Z 60s | grep -e timestamp -e measurement | grep -e timestamp -e telegraf-worker | grep -v edge-metrics-analyzer >> telegraf_mem_result.csv
# python3 prometheus_data_querier.py x.x.x.x:32099 kubernetes_pod_container_memory_usage_bytes 2022-12-22T11:00:00.000Z 2022-12-22T12:11:10.000Z 10s | grep -e 'name' -e 'measurement' | grep -v -e edge-metrics-analyzer -e promtail -e master>> telegraf_mem_result.csv
