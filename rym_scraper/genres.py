from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException

import itertools
from time import sleep


CSV_FILE_PATH = "genres.csv"


class Genre:
    __id_incrementer = itertools.count()

    @classmethod
    def restart_count(cls, restart_from:"int"):
        cls.__id_incrementer = itertools.count(restart_from)

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


class Scraper:
    def __init__(self) -> None:
        # initialise webdriver
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)
        

        # initialise exporter
        self.output_file = open(CSV_FILE_PATH,'w')

    @classmethod
    def get_all_subgenres_from_hierarchy_list(self, subgenre_hierarchy_list, parent_genre:"Genre"=None) -> "list[Genre]":
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
                recur_parsed_subgenres = self.get_all_subgenres_from_hierarchy_list(hierarchy_list, subgenre)
                parsed_subgenres.extend(recur_parsed_subgenres)
        
        return parsed_subgenres

    def create_main_genre(self, main_genre_elem:"WebElement") -> Genre:
        expand_subgenre_button = main_genre_elem.find_element(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_expand.ui_button.button_expand")
        onclick_script = expand_subgenre_button.get_attribute("onclick")
        self.driver.execute_script(onclick_script)

        ## get main genre desc
        ### main genre desc is in subgenre hierarchy
        subgenres_elem = main_genre_elem.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_expanded")
        genre_desc_p = subgenres_elem.find_element(By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item_description_expanded")
        genre_desc = genre_desc_p.text
        
        ## get main genre name
        genre_name_h2 = main_genre_elem.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_main_inner").find_element(by=By.TAG_NAME, value="h2")
        genre_name = genre_name_h2.text

        main_genre = Genre(genre_name,genre_desc)
        self.output_file.write(main_genre.serialize())
        return main_genre

    def create_subgenres(self, main_genre_elem:"WebElement", main_genre_obj:"Genre"):
        ## get subgenres
        subgenres_elem = main_genre_elem.find_element(by=By.CSS_SELECTOR, value = ".page_genre_index_hierarchy_item_expanded")
        wait = WebDriverWait(self.driver, timeout=5)
        wait.until(lambda x: any(subgenres_elem.find_elements(by=By.CSS_SELECTOR, value = ".hierarchy_list")) )

        subgenre_hierarchy_lists = subgenres_elem.find_elements(by=By.CSS_SELECTOR, value = ".hierarchy_list")
        for subgenre_hierarchy_list in subgenre_hierarchy_lists:
            list_subgenres = self.get_all_subgenres_from_hierarchy_list(subgenre_hierarchy_list, main_genre_obj)
            for subgenre in list_subgenres:
                self.output_file.write(subgenre.serialize())
    
    def parse_categorized_genres(self, current_main_genre_elem_id = None, current_main_genre_id = None):
        genre_list = self.driver.find_element(by=By.CLASS_NAME, value="page_genre_index_hierarchy")
        main_genre_elems = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item:not(.parentless_non_top_level).anchor")

        if current_main_genre_elem_id:
            # remove all before current_main_genre_elem_id from main_genre_elems
            #TODO: implement
            # get index of `current_main_genre_elem_id` from `main_genre_elems`
            for i,main_genre_elem in enumerate(main_genre_elems):
                if main_genre_elem.get_attribute("id") == current_main_genre_elem_id:
                    main_genre_elems = main_genre_elems[i:]
                    break
        # refresh and rerun when timeout
        try:
            for main_genre_elem in main_genre_elems:
                main_genre_parsed = False
                current_main_genre_elem_id = main_genre_elem.get_attribute("id")
                
                main_genre_obj = self.create_main_genre(main_genre_elem)
                current_main_genre_id = main_genre_obj._id
                main_genre_parsed = True
                self.create_subgenres(main_genre_elem, main_genre_obj)
        except:
            print(f"error occurred. refreshing...")
            self.driver.get(self.driver.current_url)
            sleep(5)
            self.driver.refresh()
            if main_genre_parsed:
                print(f"starting from Genre id: {current_main_genre_id}")
                Genre.restart_count(current_main_genre_id)
            
            print(f"starting from Genre element id: {current_main_genre_elem_id}")
            self.parse_categorized_genres(current_main_genre_elem_id, current_main_genre_id)

    def scrape(self):
        self.driver.get("https://rateyourmusic.com/genres/")
        self.parse_categorized_genres()

        # uncategorized_genres = genre_list.find_elements(by=By.CSS_SELECTOR, value=".page_genre_index_hierarchy_item.parentless_non_top_level.anchor")
        self.driver.quit()

def main():
    rym_scraper = Scraper()
    rym_scraper.scrape()

if __name__ == "__main__":
    main()