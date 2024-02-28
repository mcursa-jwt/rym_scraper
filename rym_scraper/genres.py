from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

def main():
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get("https://rateyourmusic.com/genres/")

    # get main genres
    genre_list = driver.find_element(by=By.CLASS_NAME, value="page_genre_index_hierarchy")
    categorized_genres = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item:not(.parentless_non_top_level).anchor")

    for genre in categorized_genres:
        # expand subgenres
        expand_subgenre_button = genre.find_element(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_expand.ui_button.button_expand")
        onclick_script = expand_subgenre_button.get_attribute("onclick")
        driver.execute_script(onclick_script)

        # get main genre desc
        subgenres = genre.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_expanded")
        desc_p = subgenres.find_element(By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_description_expanded")
        print(desc_p.text)
        

        


    uncategorized_genres = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item.parentless_non_top_level.anchor")

    # get subgenres
    driver.quit()


if __name__ == "__main__":
    main()