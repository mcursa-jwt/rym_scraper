from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException

import itertools

CSV_FILE_PATH = "/home/marcu/projs/rym_scraper/genres.csv"

class Genre:
    __id_incrementer = itertools.count()
    _id = 0

    @classmethod
    def __next_id(cls):
        return next(cls.__id_incrementer)

    def __init__(self, name:"str", desc:"str", parent_id:"int"=None) -> None:
        self._name = name.replace('\n', ' ')
        self._desc = desc.replace('\n', ' ')
        self._id = self.__next_id()
        
        if parent_id:
            assert parent_id != self._id, "parent_id cannot be own id"
            self._parent_id = parent_id

    def __repr__(self) -> str:
        return f"{self._id}: {self._name}"
    
    def serialize(self):
        data = [self._name, self._desc, str(self._id),]
        try:
            data.append(str(self._parent_id))
        except AttributeError:
            data.append("")
        return "\t".join(data) + "\n"

def get_all_subgenres(subgenre_hierarchy_list,parent_genre:"Genre"=None) -> "list[Genre]":
    parsed_subgenres = []
    
    hierarchy_list_item = subgenre_hierarchy_list.find_element(by=By.CSS_SELECTOR, value = ".hierarchy_list_item")

    # save subgenre
    hierarchy_list_item_details = hierarchy_list_item.find_element(by=By.CSS_SELECTOR, value = ".hierarchy_list_item_details")
    subgenre_name = hierarchy_list_item_details.find_element(by=By.TAG_NAME, value="a").text
    subgenre_desc = hierarchy_list_item_details.find_element(by=By.TAG_NAME, value="p").text
    
    if parent_genre:
        subgenre = Genre(subgenre_name, subgenre_desc, parent_genre._id)
    else:
        subgenre = Genre(subgenre_name, subgenre_desc)
    parsed_subgenres.append(subgenre)

    # get the rest of `hierarchy_list`s
    hierarchy_lists = hierarchy_list_item.find_elements(by=By.CSS_SELECTOR, value = ".hierarchy_list")
    if hierarchy_lists:
        for hierarchy_list in hierarchy_lists:
            recur_parsed_subgenres = get_all_subgenres(hierarchy_list, subgenre)
            parsed_subgenres.extend(recur_parsed_subgenres)
    
    return parsed_subgenres

def main():
    # initialise webdriver
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)
    driver.get("https://rateyourmusic.com/genres/")

    # initialise exporter
    output_file = open(CSV_FILE_PATH,'w')

    # get main genres
    genre_list = driver.find_element(by=By.CLASS_NAME, value="page_genre_index_hierarchy")
    categorized_genres = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item:not(.parentless_non_top_level).anchor")

    for genre in categorized_genres:
        ## expand subgenres
        expand_subgenre_button = genre.find_element(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_expand.ui_button.button_expand")
        onclick_script = expand_subgenre_button.get_attribute("onclick")
        driver.execute_script(onclick_script)

        ## get main genre desc
        subgenres = genre.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_expanded")
        ### main genre desc is in subgenre hierarchy
        genre_desc_p = subgenres.find_element(By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_description_expanded")
        genre_desc = genre_desc_p.text
        
        ## get main genre name
        genre_name_h2 = genre.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_main_inner").find_element(by=By.TAG_NAME, value="h2")
        genre_name = genre_name_h2.text

        main_genre = Genre(genre_name,genre_desc)
        output_file.write(main_genre.serialize())

        ## get subgenres
        wait = WebDriverWait(driver, timeout=2)
        wait.until(lambda x: any(subgenres.find_elements(by=By.CSS_SELECTOR, value = ".hierarchy_list")) )

        subgenre_hierarchy_lists = subgenres.find_elements(by=By.CSS_SELECTOR, value = ".hierarchy_list")
        for subgenre_hierarchy_list in subgenre_hierarchy_lists:
            list_subgenres = get_all_subgenres(subgenre_hierarchy_list, main_genre)
            for subgenre in list_subgenres:
                output_file.write(subgenre.serialize())
        
    # uncategorized_genres = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item.parentless_non_top_level.anchor")

    # get subgenres
    driver.quit()


if __name__ == "__main__":
    main()