import json

import requests
import streamlit as st

SENTIMENT_SERVER_URL = 'http://localhost:5000'

# Function to generate star ratings with half-star using CSS
def display_star_rating(rating):
    full_stars = int(rating)
    half_star = (rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)

    # Create full stars, half star, and empty stars
    star_html = '<span class="star full">★</span>' * full_stars
    if half_star:
        star_html += '<span class="star half">★</span>'
    star_html += '<span class="star empty">★</span>' * empty_stars

    # Return stars and decimal rating
    return f'<div class="star-container">{star_html}<span class="rating-text">({rating:.1f})</span></div>'

def display_result(result):
    # Display product name and "Insights" above the image
    st.markdown(f'<h2 style="text-align: center; animation: fadeIn 2s;">Insights: {result["product"]}</h2>',
                unsafe_allow_html=True)

    # Display product image with hover effect (with smaller size)
    st.markdown(f"""
        <div style="text-align: center;">
            <a href="{result["product_url"]}" target="_blank">
                <img src="{result["image_url"]}" alt="Product Image" style="width:300px;"/>
            </a>
        </div>
    """, unsafe_allow_html=True)

    # Display product price after the image
    st.markdown(f'<h3 style="text-align: center; animation: fadeIn 2s;">Price: {result["price"]}</h3>',
                unsafe_allow_html=True)

    # Display review with animation
    st.markdown('<h2 style="text-align: center; animation: fadeIn 2s;">Product Summary</h2>', unsafe_allow_html=True)
    st.write(f'<div style="animation: fadeInUp 2s;">{result["summary"]}</div>', unsafe_allow_html=True)

    # Display product rating as stars and decimal number
    st.markdown('<h3 style="text-align: center; animation: fadeIn 1.5s;">Product Rating</h3>', unsafe_allow_html=True)
    st.write(display_star_rating(result['avg_rating']), unsafe_allow_html=True)

    # Display Pros and Cons with styled columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<h3 style="animation: fadeInLeft 1s;">Pros ✅</h3>', unsafe_allow_html=True)
        st.write(
            f'<ul style="animation: fadeInLeft 1.5s;">{"".join([f"<li>{pro}</li>" for pro in result["pros"]])}</ul>',
            unsafe_allow_html=True)

    with col2:
        st.markdown('<h3 style="animation: fadeInRight 1s;">Cons ❌</h3>', unsafe_allow_html=True)
        st.write(
            f'<ul style="animation: fadeInRight 1.5s;">{"".join([f"<li>{con}</li>" for con in result["cons"]])}</ul>',
            unsafe_allow_html=True)

    del st.session_state['result']

try:
    rerun_flag
except NameError:
    rerun_flag = False

def sentiment_analyzer_form():
    global rerun_flag
    st.markdown('<h1 style="text-align: center; animation: fadeIn 1.5s;">🔍 Product Insights</h1>', unsafe_allow_html=True)
    st.write('<p style="text-align: center; animation: fadeInUp 1.5s;">Get detailed insights into any product instantly by entering the product URL below.</p>', unsafe_allow_html=True)

    # Input for product URL
    product_url = st.text_input("Enter Product URL", "", disabled=st.session_state.processing)

    if st.button("Get Insights", disabled=st.session_state.processing) or rerun_flag:
        if product_url or rerun_flag:
            if not rerun_flag:
                st.session_state.processing = True
                rerun_flag = True
                st.rerun()

            # Progress bar and status text
            if rerun_flag:
                st.session_state['progress'] = 0

                try:
                    # Stream progress from the server
                    with st.spinner('Fetching product details...'):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        with requests.post(f'{SENTIMENT_SERVER_URL}/analyze', json={'url': product_url}, stream=True) as response:
                            for line in response.iter_lines():
                                if line:
                                    progress_data = json.loads(line.decode('utf-8'))

                                    # Check if progress update or final result
                                    progress = progress_data.get("progress")

                                    if progress is not None:
                                        progress_bar.progress(progress)
                                        status_text.text(f"Loading... {progress}%")

                                    # If final result
                                    if "result" in progress_data:
                                        st.session_state.result = progress_data['result']
                                        st.session_state.result['product_url'] = product_url
                                        break  # Stop the loop once final result is received

                    if response.status_code == 200:
                        rerun_flag = False
                        st.session_state.processing = False
                        st.rerun()  # Re-run Streamlit to show the result
                    else:
                        st.error(f'Failed to get prediction: {response.status_code}')

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please enter a valid product URL.")

    # Display the result if it exists in session state
    if 'result' in st.session_state:
        display_result(st.session_state.result)

    st.session_state.is_running = False  # Re-enable the navigation once done