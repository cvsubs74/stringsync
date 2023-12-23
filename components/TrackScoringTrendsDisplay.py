import streamlit as st
import pandas as pd
import plotly.express as px


class TrackScoringTrendsDisplay:
    @staticmethod
    def show(recordings, timezone='America/Los_Angeles'):
        if not recordings:
            return

        st.write("**Score Trends**")
        # Convert recordings data to a DataFrame
        df = pd.DataFrame(recordings)
        df.sort_values(by='timestamp', inplace=True)

        # Use the DataFrame index as x-axis
        df.reset_index(inplace=True)

        # Plotting the line graph for score trend
        fig_line = px.line(
            df,
            x='index',
            y='score',
            title='',
            labels={'index': 'Recordings', 'score': 'Score'}
        )

        # Set the y-axis to start from 0
        fig_line.update_yaxes(range=[0, max(10, df['score'].max())])

        # Set the x-axis to only show integer values
        fig_line.update_xaxes(
            type='linear',
            tickmode='array',
            tickvals=list(range(df['index'].max() + 1))
        )

        # Adding the line graph to the Streamlit app
        st.plotly_chart(fig_line, use_container_width=True)
