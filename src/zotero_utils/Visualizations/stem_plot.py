import plotly.graph_objects as go
import pandas as pd

def stem_plot(items: list, show_details: bool = False) -> go.Figure:
    """
    Create a stem plot visualization of total publications per year.
    
    Args:
        items (List[Dict]): List of dictionaries containing publication data.
            Each dictionary should have:
            - 'date_published': publication date
            - 'title': publication title
    
    Returns:
        go.Figure: Plotly figure object containing the stem plot
    """
    for item in items:
        item['year_published'] = str(item['date_published'].year)
        if show_details:
            item['creators'] = item.get('creators', ("None",))
            item['first_author'] = item['creators'][0] if len(item['creators'])>0 else "None"
    # Convert to DataFrame
    df = pd.DataFrame(items)
    if show_details:
        df['y'] = 0
    
    # Group by year to get total publications per year
    year_groups = df.groupby('year_published').size().reset_index(name='count')
    
    # Create the stem plot
    fig = go.Figure()
    
    # Create hover text with publication details
    hover_text = []
    if show_details:
        hover_text_detailed = []
    for year in year_groups['year_published']:
        matching_pubs = df[df['year_published'] == year]        
        hover_text.append(
            f"Year: {year}<br>"
            f"Total Publications: {len(matching_pubs)}<br>"
        )
    if show_details:
        df = df.sort_values(by='first_author')
        count_by_years_dict = {}
        for index, pub in df.iterrows():
            year = pub['year_published']
            if year not in count_by_years_dict:
                count_by_years_dict[year] = 0
            else:
                count_by_years_dict[year] += 1
            df.loc[index, 'y'] = count_by_years_dict[year] # Give this publication a y-value.
            hover_text_detailed.append(
                f"Year: {year}<br>"
                f"First Author: {pub['first_author']}<br>"
                f"Title: {pub['title']}"
            )
    
    # Add vertical lines (stems)
    for x, y in zip(year_groups['year_published'], year_groups['count']):
        fig.add_trace(go.Scatter(
            x=[x, x],
            y=[0, y],
            mode='lines',
            line=dict(color='rgba(0,0,0,0.3)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Add main scatter plot on top of stems
    fig.add_trace(go.Scatter(
        x=year_groups['year_published'],
        y=year_groups['count'],
        mode='markers+lines',
        name='Publications',
        text=hover_text,
        hoverinfo='text',
        line=dict(width=2),
        marker=dict(size=10, color='royalblue')
    ))

    if show_details:
        fig.add_trace(go.Scatter(
            x=df['year_published'],
            y=df['y'],
            mode='markers',
            name='Details',
            text=hover_text_detailed,
            hoverinfo='text',
            marker=dict(size=5, color='grey')
        ))
    
    # Update layout with improved styling
    fig.update_layout(
        title={
            'text': "Publications per Year in Zotero Library",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=24)
        },
        hoverlabel=dict(
            bgcolor='green'
        ),
        xaxis_title="Publication Year",
        yaxis_title="Number of Publications",
        hovermode="closest",
        showlegend=False,  # No legend needed for single trace
        template="plotly_white"
    )
    
    # Improve axis styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(rangemode="tozero")  # Ensure y-axis starts at 0
    
    fig.show()

def stem_plot_author_date(items: list):
    """
    Create a stem plot visualization of publications over time.
    
    Args:
        items (List[Dict]): List of dictionaries containing publication data.
            Each dictionary should have:
            - 'creators': tuple of strings (author names)
            - 'year_published': publication date
            - 'title': publication title
    
    Returns:
        go.Figure: Plotly figure object containing the stem plot
    """
    # Process items and handle missing creators
    processed_items = []
    for item in items:
        processed_item = item.copy()
        processed_item['creators'] = item.get('creators', ("None",))
        processed_item['first_author'] = processed_item['creators'][0] if len(processed_item['creators'])>0 else "None"
        processed_items.append(processed_item)

    # Convert to a DataFrame for easier manipulation
    df = pd.DataFrame(processed_items)

    # Extract unique authors
    unique_authors = df['first_author'].unique()

    # Prepare data for stem plot
    year_author_groups = df.groupby(['year_published', 'first_author']).size().reset_index(name='count')

    # Create the stem plot with Plotly
    fig = go.Figure()

    # Add traces for each author
    for author in unique_authors:
        author_data = year_author_groups[year_author_groups['first_author'] == author]
         # Create hover text with publication details
        hover_text = []
        for year in author_data['year_published']:
            matching_pubs = df[
                (df['year_published'] == year) & 
                (df['first_author'] == author)
            ]
            titles = '<br>'.join(matching_pubs['title'])
            hover_text.append(
                f"First Author: {author}<br>"
                f"Year: {year.date()}<br>"
                f"Titles:<br>{titles}"
            )

        # Add vertical lines (stems)
        for x, y in zip(author_data['year_published'], author_data['count']):
            fig.add_trace(go.Scatter(
                x=[x, x],
                y=[0, y],
                mode='lines',
                line=dict(color='rgba(0,0,0,0.3)', width=1),
                showlegend=False,
                hoverinfo='skip'
            ))

        # Add main scatter plot on top of stems
        fig.add_trace(go.Scatter(
            x=author_data['year_published'],
            y=author_data['count'],
            mode='markers',
            name=author,
            text=hover_text,
            hoverinfo='text',
            line=dict(width=1),
            marker=dict(size=8)
        ))

    # Update layout with improved styling
    fig.update_layout(
        title={
            'text': "Publication Timeline",
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=24)
        },
        xaxis_title="Publication Year",
        yaxis_title="Number of Publications",
        hovermode="closest",
        showlegend=True,
        legend_title="Authors",
        template="plotly_white"  # Clean, professional template        
    )

    # Improve axis styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')

    # Display the plot
    fig.show()
