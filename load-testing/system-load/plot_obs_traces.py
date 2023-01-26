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
    df = df[df['container_name'] == 'jaeger-agent']
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df['value'] = df['value'] / 1000000
    # df['value'] = (df['value'] / 1000000) / 16384) * 100 # convert to percentage

    # print(df.head(2))
    print(len(df))
    # print(df.dtypes)

    df2 = df.groupby('host')['value'].mean()
    print(df2)

    # plot lines
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]

        if subgraph == 'ax1y1':
            ax1y1.set_title('50 Pods')
            ax1y1.set_xlabel('Timestamp')
            ax1y1.set_ylabel('Memory Usage (MiB)')
            ax1y1.set_ylim(0, 15)  # scale between these values
            ax1y1.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y1.yaxis.grid()
        elif subgraph == 'ax1y2':
            ax1y2.set_title('100 Pods')
            ax1y2.set_xlabel('Timestamp')
            ax1y2.set_ylabel('Memory Usage (MiB)')
            ax1y2.set_ylim(0, 15)  # scale between these values
            ax1y2.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y2.yaxis.grid()
        else:
            ax1y3.set_title('200 Pods')
            ax1y3.set_xlabel('Timestamp')
            ax1y3.set_ylabel('Memory Usage (MiB)')
            ax1y3.set_ylim(0, 15)  # scale between these values
            ax1y3.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax1y3.yaxis.grid()
            ax1y3.legend(loc='lower right')


def cpu_usage(input_file_name, subgraph):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file_name)
    df = df[df['container_name'] == 'jaeger-agent']
    df['time_stamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)  # Covert value to Milliseconds
    # df['value'] = (df['value'] / 1000) # Covert value to Microseconds

    print(len(df))

    df2 = df.groupby('host')['value'].mean()
    print(df2)

    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["time_stamp", "host", "value"]]

        if subgraph == 'ax2y1':
            ax2y1.set_title('50 Pods')
            ax2y1.set_xlabel('Timestamp')
            ax2y1.set_ylabel('CPU Usage (ms)')
            ax2y1.set_ylim(0, 2)  # scale between these values
            ax2y1.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y1.yaxis.grid()
        elif subgraph == 'ax2y2':
            ax2y2.set_title('100 Pods')
            ax2y2.set_xlabel('Timestamp')
            ax2y2.set_ylabel('CPU Usage (ms)')
            ax2y2.set_ylim(0, 2)  # scale between these values
            ax2y2.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y2.yaxis.grid()
        else:
            ax2y3.set_title('200 Pods')
            ax2y3.set_xlabel('Timestamp')
            ax2y3.set_ylabel('CPU Usage (ms)')
            ax2y3.set_ylim(0, 2)  # scale between these values
            ax2y3.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=1)
            ax2y3.yaxis.grid()


def network_usage(input_file_name, output_file_name):
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

        plt.plot_date(df_final["time_stamp"], df_final["value"], label=str(node), linestyle='-', markersize=2)


output_file = ['jaeger_resource_usage.png']
input_file = ['jaeger_mem_result_50-pods.csv', 'jaeger_mem_result_100-pods.csv', 'jaeger_mem_result_200-pods.csv',
              'jaeger_cpu_result_50-pods.csv', 'jaeger_cpu_result_100-pods.csv', 'jaeger_cpu_result_200-pods.csv']

memory_usage(input_file_name=input_file[0], subgraph='ax1y1')
memory_usage(input_file_name=input_file[1], subgraph='ax1y2')
memory_usage(input_file_name=input_file[2], subgraph='ax1y3')

cpu_usage(input_file_name=input_file[3], subgraph='ax2y1')
cpu_usage(input_file_name=input_file[4], subgraph='ax2y2')
cpu_usage(input_file_name=input_file[5], subgraph='ax2y3')

# cpu_usage_normal(input_file_name='loki_cpu_result_200-pods.csv', fault_timestamp='2022-06-21 08:22:50',
#                 output_file_name='loki_cpu_result_200-pods.png')

# network_usage_normal(input_file_name='telegraf_cpu_result_10s-master.csv', fault_timestamp='2022-06-21 08:22:50',
#                    output_file_name='telegraf_pod_cpu_10s-master.png')


fig.autofmt_xdate(rotation=50)
fig.tight_layout()
# plt.gcf().autofmt_xdate()
# plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)


# plt.show()
plt.savefig(output_file[0], dpi=800)
