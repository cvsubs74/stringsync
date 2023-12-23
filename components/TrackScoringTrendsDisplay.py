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

        # Sort by timestamp in ascending order
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.sort_values(by='timestamp', inplace=True)

        # After sorting, reset the index to use it as x-axis and start from 1
        df.reset_index(drop=True, inplace=True)
        df.index += 1

        # Plotting the line graph for score trend
        fig_line = px.line(
            df,
            x=df.index,
            y='score',
            title='',
            labels={'index': 'Recordings', 'score': 'Score'}
        )

        # Set the y-axis to start from 0
        fig_line.update_yaxes(range=[0, max(10, df['score'].max())])

        # Set the x-axis to only show integer values starting from 1
        fig_line.update_xaxes(
            type='linear',
            tickmode='array',
            tickvals=list(range(1, df.shape[0] + 1))
        )

        # Adding the line graph to the Streamlit app
        st.plotly_chart(fig_line, use_container_width=True)

