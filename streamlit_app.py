# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import requests

# Write directly to the app
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write(
    """
    Choose the fruits you want in your custom Smoothie!
    """
)

name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# --- KEY CHANGE 1: Fetch both columns and convert to a Pandas DataFrame ---
# We now select both FRUIT_NAME for display and SEARCH_ON for the API call.
# .to_pandas() makes it easy to look up values.
cnx = st.connection("snowflake")
session = cnx.session()
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON')).to_pandas()

# The multiselect will now show the user the nice FRUIT_NAMEs from the first column.
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    my_dataframe,  # Pass the entire dataframe here
    max_selections=5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        # --- KEY CHANGE 2: Look up the search term before the API call ---
        # Find the row in our dataframe that matches the fruit the user chose.
        search_on_row = my_dataframe.loc[my_dataframe['FRUIT_NAME'] == fruit_chosen]
        
        # From that row, get the value in the SEARCH_ON column.
        # .iloc[0] gets the first (and only) matching row's value.
        search_on_value = search_on_row['SEARCH_ON'].iloc[0]

        st.subheader(fruit_chosen + ' Nutrition Information')
        # Make the API call using the correct search_on_value
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on_value)
        sf_df = st.dataframe(data=fruityvice_response.json(), use_container_width=True)

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                         values ('""" + ingredients_string + """', '""" + name_on_order + """')"""

    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f'Your Smoothie is ordered! {name_on_order}', icon="✅")
