import matplotlib.pyplot as plt

def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{v:d}'.format(v=val)
    return my_format

def pie_chart(counts_dict: dict, num_groups: int = 20, sort_by: str = "values", title_str: str = ""):
    """Visualize a pie chart given a counts dictionary.
    Can sort the pie chart slices by either values or labels"""
    
    if sort_by not in ("values", "labels"):
        raise ValueError("Invalid 'sort_by' parameter. Valid parameters are 'values' or 'labels'.")

    labels = list(counts_dict.keys())
    # labels = [str(label) for label in labels]
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
    
    fig, ax = plt.subplots()
    ax.pie(sorted_values, labels=sorted_labels, autopct=autopct_format(sorted_values))
    plt.title(title_str)
    plt.show()