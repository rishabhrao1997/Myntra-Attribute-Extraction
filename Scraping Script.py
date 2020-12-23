'''
Kindly run this script from some IDE.
'''
import pandas as pd
import time
import re
import os
from tqdm import tqdm
from selenium import webdriver
from colour import Color
import urllib.request
from datetime import datetime

def create_driver():

	return webdriver.Chrome('chromedriver.exe')

def scrape_links(driver, website, keyword, count = 10000, sleep_time = 5, verbose = True):
	'''
	Function to scrape links of products from keyword
	'''

	if verbose:
		start = datetime.now()
		print(f"Scraping {count} links for {keyword}...")

	#opening the webpage
	driver.get(website)
	#searching for keyword
	driver.find_element_by_class_name('desktop-searchBar').send_keys(keyword)
	driver.find_element_by_class_name('desktop-submit').click()

	product_links = []

	#getting the product urls from the search result
	while True:
		#end condition
		if len(product_links) >= count:
			break

        #wait time before each keyclick
		time.sleep(sleep_time)
	    #getting the url
		for product in driver.find_elements_by_class_name('product-base'):
			product_links.append(product.find_element_by_xpath('./a').get_attribute('href'))
		
		try:
	    	#seeing if next button is present on the page or not
			driver.find_element_by_class_name('pagination-next').click()
		except:
			pass

		if verbose:
			if len(product_links) % 500 == 0:
				print(f'{len(product_links)} scraped..')

	if verbose:
		print("Done.")
		print(f"Time elapsed = {datetime.now() - start}\n")

	return product_links[:count]

def check_color(color):
	'''
	Function to check if the given element is a valid color or not
	'''
	try:
		Color(color)
		return True
	except ValueError:
		return False

def extract_colors(text):
	'''
	Function to extract the colors from a text
	'''
	colors = list(set([c for c in text.split(' ') if check_color(c)]))

	return ', '.join(colors).lower()

def get_length(specs):
    '''
    Function to get the Length attribute from specification dictionary
    '''
    length = specs.get('Length')
    
    if not length:
    	if 'Top Length' in specs.keys():
    		length = specs.get('Top Length')
    
    return length

def download_image(url, path):
    '''
    Function to download the image using the given url
    '''
    urllib.request.urlretrieve(url, path) 

def generate_dataframe(driver, product_links, gender = 'men', sleep_time = 2, verbose = True):
	'''
	Function to generate the dataframe with scraped data
	'''

	if verbose:
		start = datetime.now()
		print(f"Scraping attributes for {gender}...")

	if not os.path.exists(f'imgs/{gender}'):
		if not os.path.exists('imgs'):
			os.mkdir('imgs')
		os.mkdir(f'imgs/{gender}')

    #creating a dataframe to store the results
	df = pd.DataFrame(columns = ['path', 'category', 'attribute_1', 'attribute_2'])
    
    try:
	    #going through each product
		for index, link in enumerate(product_links):
			#waiting between the requests
			time.sleep(sleep_time)
			#opening the product page
			driver.get(link)

		    #fetching the type of product
			category = driver.find_element_by_class_name('breadcrumbs-container').find_elements_by_xpath(
		                './a')[-3].get_attribute('innerHTML')
		    #extracting the description of product
			description = driver.find_element_by_class_name('pdp-product-description-content').get_attribute('innerHTML')
		    #getting specifications of the product
			specifications = dict()
			for specification in driver.find_element_by_class_name('index-tableContainer').find_elements_by_class_name('index-row'):
				k = specification.find_element_by_class_name('index-rowKey').get_attribute('innerHTML')
				v = specification.find_element_by_class_name('index-rowValue').get_attribute('innerHTML')    
				specifications[k] = v
	    	#getting the image container
			image_element = driver.find_element_by_class_name(
		                    'image-grid-container').find_element_by_class_name(
		                    'image-grid-image').get_attribute('style')

		    #extracting the important things from the text

			colors = extract_colors(description)
			img_url = image_element.split('url("')[1].replace('");', '')
			img_path = f'imgs/{gender}/{index}.jpg'
			download_image(img_url, img_path)
			length = get_length(specifications)

			df = df.append(pd.DataFrame({'path' : [img_path],
			                             'category' : [category],
			                             'attribute_1' : [colors],
			                             'attribute_2' : [length]}),
			              ignore_index = True)

			if verbose:
				if (index+1) % 500 == 0:
					print(f"{index+1} products fetched...")
	finally:
		if verbose:
			print("Done.")
			print(f"Time elapsed = {datetime.now() - start}")
		
		return df


def main(counts = 10000, men_keyword = 'men clothing', women_keyword = 'women clothing'):
	try:
		#creating the driver
		driver = create_driver()
		#scraping links for men wear
		men_products_links = scrape_links(driver, 'https://www.myntra.com', men_keyword, count = counts, verbose = False)
		#getting the dataframe for men
		products_df = generate_dataframe(driver, men_products_links, gender = 'men', verbose = False)
		#scraping links for women wear
		women_products_links = scrape_links(driver, 'https://www.myntra.com', women_keyword, count = counts, verbose = False)
		#appending to the original dataframe
		products_df = products_df.append(generate_dataframe(driver, women_products_links, gender = 'women', verbose = False))

	finally:
		#closing and quitting the driver
		driver.close()
		driver.quit()

		#saving the final dataframe to csv file
		products_df.to_csv('myntra.csv', index = False)

main(5000)