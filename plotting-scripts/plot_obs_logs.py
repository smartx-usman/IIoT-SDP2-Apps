import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 6.0]
plt.rcParams["figure.autolayout"] = True

fig, axs = plt.subplots(2, 3, sharex='col', sharey='row')


def memory_usage(input_file, plt_title_labels, axs_dim, y_lim, set_legend, set_x_label):
    """Plot Memory Usage"""
    df = pd.read_csv(input_file)
    df = df[df['container_name'] == 'promtail']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df['value'] = df['value'] / 1000000
    # df['value'] = (df['value'] / 1000000) / 16384) * 100 # convert to percentage

    # Process nodes data
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]
        print(f'[plot_memory_data] - Node: {node}, Records: {str(len(df))}')

        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, plt_title_labels=plt_title_labels,
                    axs_dim=axs_dim, y_lim=y_lim, set_legend=set_legend, set_x_label=set_x_label)


def cpu_usage(input_file, plt_title_labels, axs_dim, y_lim, set_legend, set_x_label):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file)
    df = df[df['container_name'] == 'promtail']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    # Process nodes data
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]
        print(f'[plot_cpu_data] - Node: {node}, Records: {str(len(df))}')
        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, plt_title_labels=plt_title_labels,
                    axs_dim=axs_dim, y_lim=y_lim, set_legend=set_legend, set_x_label=set_x_label)


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


def create_plot(df, x_col, y_col, label, plt_title_labels, axs_dim, y_lim, set_legend, set_x_label):
    """Create plots"""
    axs[axs_dim[0], axs_dim[1]].set_title(plt_title_labels[0])

    if set_x_label:
        axs[axs_dim[0], axs_dim[1]].set_xlabel(plt_title_labels[1])

    axs[axs_dim[0], axs_dim[1]].set_ylabel(plt_title_labels[2])
    axs[axs_dim[0], axs_dim[1]].set_ylim(y_lim[0], y_lim[1])  # scale between these values
    axs[axs_dim[0], axs_dim[1]].plot_date(df[x_col], df[y_col], label=label, linestyle='-', markersize=1)
    axs[axs_dim[0], axs_dim[1]].yaxis.grid('gray')

    if set_legend:
        axs[axs_dim[0], axs_dim[1]].legend(loc='lower right')


def main():
    """Main function"""
    output_file = ['loki_resource_usage.png']
    input_file = ['loki_mem_result_50-pods.csv', 'loki_mem_result_80-pods.csv', 'loki_mem_result_110-pods.csv',
                  'loki_cpu_result_50-pods.csv', 'loki_cpu_result_80-pods.csv', 'loki_cpu_result_110-pods.csv']

    memory_usage(input_file=input_file[0], plt_title_labels=("50 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 0), y_lim=(0, 80), set_legend=False, set_x_label=False)
    memory_usage(input_file=input_file[1], plt_title_labels=("80 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 1), y_lim=(0, 80), set_legend=False, set_x_label=False)
    memory_usage(input_file=input_file[2], plt_title_labels=("110 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 2), y_lim=(0, 80), set_legend=True, set_x_label=True)

    cpu_usage(input_file=input_file[3], plt_title_labels=("50 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 0), y_lim=(0, 150), set_legend=False, set_x_label=False)
    cpu_usage(input_file=input_file[4], plt_title_labels=("80 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 1), y_lim=(0, 150), set_legend=False, set_x_label=True)
    cpu_usage(input_file=input_file[5], plt_title_labels=("110 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 2), y_lim=(0, 150), set_legend=False, set_x_label=False)

    fig.autofmt_xdate(rotation=50)
    fig.tight_layout()
    # plt.gcf().autofmt_xdate()
    # plt.legend(loc='lower left', bbox_to_anchor=(0, 1.02, 1, 0.2), mode="expand", borderaxespad=0, ncol=3)
    # plt.show()
    plt.savefig(output_file[0], dpi=800)


if __name__ == '__main__':
    main()
