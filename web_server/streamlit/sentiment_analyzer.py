import requests
import streamlit as st
from streamlit import rerun, session_state

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

    # # Display product image with hover effect (with smaller size)
    # st.image(result['image_url'], caption="Product Image", use_column_width=False, width=300)

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
    # Title and page setup
    st.markdown('<h1 style="text-align: center; animation: fadeIn 1.5s;">🔍 Product Insights</h1>', unsafe_allow_html=True)
    st.write('<p style="text-align: center; animation: fadeInUp 1.5s;">Get detailed insights into any product instantly by entering the product URL below.</p>', unsafe_allow_html=True)

    # Input for product URL
    product_url = st.text_input("Enter Product URL", "")

    # Button to trigger the analysis
    if st.button("Get Insights") or rerun_flag:
        if product_url or rerun_flag:
            if not rerun_flag:
                st.session_state.processing = True
                rerun_flag = True
                print('rerun flag: ', rerun_flag)
                st.rerun()
            # Progress bar with percentage
            # with st.spinner('Fetching product details...'):
            #     progress_bar = st.progress(0)
            #     status_text = st.empty()
                # for percent_complete in range(100):
                #     time.sleep(0.02)
                #     progress_bar.progress(percent_complete + 1)
                #     status_text.text(f"Loading... {percent_complete + 1}%")

            # Fetch product details (replace this with real logic to scrape/analyze product)
            if rerun_flag:
                response = requests.post(f'{SENTIMENT_SERVER_URL}/analyze', json={
                    'url': product_url,
                })

                if response.status_code == 200:
                    st.session_state.result = response.json()  # Store the result in session state

                    # Format star rating
                    full_stars = int(st.session_state.result['avg_rating'])
                    half_star = (st.session_state.result['avg_rating'] - full_stars) >= 0.5
                    empty_stars = 5 - full_stars - (1 if half_star else 0)

                    star_html = '★' * full_stars
                    if half_star:
                        star_html += '½'
                    star_html += '☆' * empty_stars

                    # st.session_state.result['image_url'] = st.session_state.result.get('image_url', '/static/placeholder.jpg')

                    st.session_state.processing = False
                    rerun_flag = False
                    print('rerun flag: ', rerun_flag)
                    st.rerun()  # Rerun to display result in a new function
                else:
                    st.error(f'response status: {response.status_code}')
                    st.error(f'response: {response}')
                    st.error("Failed to get prediction")
        else:
            st.error("Please enter a valid product URL.")

    # Display the result if it exists in session state
    if 'result' in st.session_state:
        display_result(st.session_state.result)  # Call the display function

    st.session_state.is_running = False  # Re-enable the navigation once done