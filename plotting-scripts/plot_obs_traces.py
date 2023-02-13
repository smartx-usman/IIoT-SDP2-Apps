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
    df = df[df['container_name'] == 'jaeger-agent']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    df['value'] = df['value'] / 1000000

    df2 = df.groupby('host')['value'].mean()
    print(df2)

    # plot lines
    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]
        print(f'[plot_memory_data] - Node: {node}, Records: {str(len(df))}')

        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, plt_title_labels=plt_title_labels,
                    axs_dim=axs_dim, y_lim=y_lim, set_legend=set_legend, set_x_label=set_x_label)


def cpu_usage(input_file, plt_title_labels, axs_dim, y_lim, set_legend, set_x_label):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file)
    df = df[df['container_name'] == 'jaeger-agent']
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)  # Covert value to Milliseconds
    # df['value'] = (df['value'] / 1000) # Covert value to Microseconds

    df2 = df.groupby('host')['value'].mean()
    print(df2)

    for node in ('worker1', 'worker2', 'observability1'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]
        print(f'[plot_cpu_data] - Node: {node}, Records: {str(len(df))}')
        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, plt_title_labels=plt_title_labels,
                    axs_dim=axs_dim, y_lim=y_lim, set_legend=set_legend, set_x_label=set_x_label)


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
    output_file = ['jaeger_resource_usage.png']
    input_file = ['jaeger_mem_result_50-pods.csv', 'jaeger_mem_result_100-pods.csv', 'jaeger_mem_result_200-pods.csv',
                  'jaeger_cpu_result_50-pods.csv', 'jaeger_cpu_result_100-pods.csv', 'jaeger_cpu_result_200-pods.csv']

    memory_usage(input_file=input_file[0], plt_title_labels=("50 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 0), y_lim=(0, 15), set_legend=False, set_x_label=False)
    memory_usage(input_file=input_file[1], plt_title_labels=("100 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 1), y_lim=(0, 15), set_legend=False, set_x_label=False)
    memory_usage(input_file=input_file[2], plt_title_labels=("200 Pods", "Timestamp", "Memory Usage (MiB)"),
                 axs_dim=(0, 2), y_lim=(0, 15), set_legend=True, set_x_label=False)

    cpu_usage(input_file=input_file[3], plt_title_labels=("50 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 0), y_lim=(0, 2), set_legend=False, set_x_label=False)
    cpu_usage(input_file=input_file[4], plt_title_labels=("100 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 1), y_lim=(0, 2), set_legend=False, set_x_label=True)
    cpu_usage(input_file=input_file[5], plt_title_labels=("200 Pods", "Timestamp", "CPU Usage (ms)"),
              axs_dim=(1, 2), y_lim=(0, 2), set_legend=False, set_x_label=False)

    fig.autofmt_xdate(rotation=50)
    fig.tight_layout()
    # plt.show()
    plt.savefig(output_file[0], dpi=800)


if __name__ == '__main__':
    main()
