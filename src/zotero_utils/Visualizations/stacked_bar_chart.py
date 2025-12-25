import matplotlib.pyplot as plt
import typer

def stacked_bar_chart(counts_dict: dict, num_groups: int = 20, sort_by: str = "values", title_str: str = ""):
    """Visualize a stacked bar chart given a counts dictionary.
    Can sort the bars by either values or labels."""

    if isinstance(num_groups, typer.models.OptionInfo):
        num_groups = num_groups.default

    if sort_by not in ("values", "labels"):
        raise ValueError("Invalid 'sort_by' parameter. Valid parameters are 'values' or 'labels'.")

    labels = list(counts_dict.keys())
    values = list(counts_dict.values())

    # Sort the labels and values together based on the chosen criterion
    if sort_by == "values":
        sorted_pairs = sorted(zip(values, labels), reverse=True)
        sorted_values, sorted_labels = zip(*sorted_pairs)
    elif sort_by == "labels":
        sorted_pairs = sorted(zip(labels, values))
        sorted_labels, sorted_values = zip(*sorted_pairs)

    # Limit to the top `num_groups`
    sorted_labels = sorted_labels[:num_groups]
    sorted_values = sorted_values[:num_groups]

    # Plot a stacked bar chart
    fig, ax = plt.subplots()

    # Create a single stacked bar
    x = [0]  # Single bar for stacking
    bottom = 0  # Start stacking from the bottom

    for label, value in zip(sorted_labels, sorted_values):
        ax.bar(x, [value], bottom=bottom, label=f"{label}: {value}")

        # Place the count value at the center of the segment
        # ax.text(
        #     x[0],  # x-coordinate of the text
        #     bottom + value / 2,  # y-coordinate: center of the segment
        #     f"{label}: {value}",  # Text to display
        #     ha="center",  # Horizontal alignment
        #     va="center",  # Vertical alignment
        #     fontsize=10,  # Font size
        #     color="white" if value > 10 else "black",  # Contrast color
        #     weight="bold"  # Bold text
        # )

        bottom += value  # Increment the bottom for the next segment

    # Add title and legend
    ax.set_title(title_str, fontsize=14)
    legend_handles, legend_labels = plt.gca().get_legend_handles_labels()
    ax.legend(legend_handles[::-1], legend_labels[::-1], loc='upper left', bbox_to_anchor=(1, 1))
    ax.set_xticks([])  # Remove x-axis labels as it's a single stacked bar
    ax.set_ylabel("Count")

    plt.tight_layout()
    plt.show()