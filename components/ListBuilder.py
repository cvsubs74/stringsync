import streamlit as st


class ListBuilder:
    def __init__(self, column_widths):
        self.column_widths = column_widths

    def build_header(self, column_names):
        header_html = "<div style='background-color:#5CB5D2;padding:5px;border-radius:3px;border:1px solid black;'>"

        for column_name, width in zip(column_names, self.column_widths):
            header_html += f"<div style='display:inline-block;width:{width}%;text-align:left;box-sizing: border-box;'>"
            header_html += f"<p style='color:black;margin:0;font-size:15px;font-weight:bold;'>{column_name}</p>"
            header_html += "</div>"

        header_html += "</div>"
        st.markdown(header_html, unsafe_allow_html=True)

    def build_row(self, row_data, col0="", criteria_colors=()):
        # Initialize the background color as white (or any default color)
        bg_color = "#FDFEFE"

        # Apply each criteria-color pair
        for criteria, color in criteria_colors:
            if criteria(row_data):
                bg_color = color  # Update the background color if the criteria is met

        row_html = f"<div style='background-color:{bg_color};padding:5px;border-radius:3px;border:1px solid black;'>"
        row_html += col0
        for (column_name, value), width in zip(row_data.items(), self.column_widths):
            display_value = 'N/A' if value is None or value == "" else value
            row_html += f"<div style='display:inline-block;width:{width}%;text-align:left;box-sizing: border-box;'>"
            row_html += f"<p style='color:black;margin:0;font-size:14px;'>{display_value}</p>"
            row_html += "</div>"

        row_html += "</div>"
        st.markdown(row_html, unsafe_allow_html=True)



