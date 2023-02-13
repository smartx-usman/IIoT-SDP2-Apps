import sys

import pandas as pd
from matplotlib import pyplot as plt

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

plt.rcParams["figure.figsize"] = [7.0, 6.0]
plt.rcParams["figure.autolayout"] = True

fig, axs = plt.subplots(2, 3, sharex='col', sharey='row')


def memory_usage(input_file, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end, legend_set,
                 set_x_label):
    """Plot Memory Usage"""
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df['value'] = (df['value'] / 1000000)  # / 16384) * 100

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]

        print(df_final.head(2))
        print(len(df_final))

        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, axs_row=axs_row, axs_col=axs_col,
                    title=title, x_label=x_label, y_label=y_label,
                    y_lim_start=y_lim_start, y_lim_end=y_lim_end, legend_set=legend_set, set_x_label=set_x_label)


def cpu_usage(input_file, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end, legend_set, set_x_label):
    """Plot CPU Usage"""
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', origin='unix')
    df['value'] = (df['value'] / 1000000)

    print(df.dtypes)

    for node in ('worker1', 'worker2', 'observability1', 'master'):
        df_app = df[df['host'] == node]
        df_final = df_app[["timestamp", "host", "value"]]

        print(df_final.head(2))
        print(len(df_app))

        create_plot(df=df_final, x_col="timestamp", y_col="value", label=node, axs_row=axs_row, axs_col=axs_col,
                    title=title, x_label=x_label, y_label=y_label,
                    y_lim_start=y_lim_start, y_lim_end=y_lim_end, legend_set=legend_set, set_x_label=set_x_label)


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


def create_plot(df, x_col, y_col, label, axs_row, axs_col, title, x_label, y_label, y_lim_start, y_lim_end, legend_set,
                set_x_label):
    """Create plots"""
    axs[axs_row, axs_col].set_title(title)
    if set_x_label:
        axs[axs_row, axs_col].set_xlabel(x_label)
    axs[axs_row, axs_col].set_ylabel(y_label)
    axs[axs_row, axs_col].set_ylim(y_lim_start, y_lim_end)  # scale between these values
    axs[axs_row, axs_col].plot_date(df[x_col], df[y_col], label=label, linestyle='-', markersize=1)
    axs[axs_row, axs_col].yaxis.grid('gray')

    if legend_set:
        axs[axs_row, axs_col].legend(loc='lower right')


def main():
    """Main function"""
    output_file = ['telegraf_resource_usage.png']
    input_file = ['telegraf_mem_result_250ms.csv', 'telegraf_mem_result_1s.csv', 'telegraf_mem_result_10s-master.csv',
                  'telegraf_cpu_result_250ms.csv', 'telegraf_cpu_result_1s.csv', 'telegraf_cpu_result_10s-master.csv']

    memory_usage(input_file=input_file[0], axs_row=0, axs_col=0, title="250ms",
                 x_label="Timestamp", y_label="Memory Usage (MiB)", y_lim_start=0, y_lim_end=80, legend_set=False,
                 set_x_label=False)
    memory_usage(input_file=input_file[1], axs_row=0, axs_col=1, title="1s",
                 x_label="Timestamp", y_label="Memory Usage (MiB)", y_lim_start=0, y_lim_end=80, legend_set=False,
                 set_x_label=False)
    memory_usage(input_file=input_file[2], axs_row=0, axs_col=2, title="10s",
                 x_label="Timestamp", y_label="Memory Usage (MiB)", y_lim_start=0, y_lim_end=80, legend_set=True,
                 set_x_label=False)

    cpu_usage(input_file=input_file[3], axs_row=1, axs_col=0, title="250ms",
              x_label="Timestamp", y_label="CPU Usage (ms)", y_lim_start=0, y_lim_end=100, legend_set=False,
              set_x_label=False)
    cpu_usage(input_file=input_file[4], axs_row=1, axs_col=1, title="1s",
              x_label="Timestamp", y_label="CPU Usage (ms)", y_lim_start=0, y_lim_end=100, legend_set=False,
              set_x_label=True)
    cpu_usage(input_file=input_file[5], axs_row=1, axs_col=2, title="10s",
              x_label="Timestamp", y_label="CPU Usage (ms)", y_lim_start=0, y_lim_end=100, legend_set=False,
              set_x_label=False)

    fig.autofmt_xdate(rotation=50)
    fig.tight_layout()
    # plt.show()
    plt.savefig(output_file[0], dpi=800)


if __name__ == '__main__':
    main()
