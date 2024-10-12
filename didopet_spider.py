import scrapy
import pandas as pd
import numpy as np
import re
import os
from bs4 import BeautifulSoup as bs 
from datetime import datetime
import json

def get_currnency(pro_soup):
    """extracting currency value"""
    
    
    try:
        curr_script = json.loads([script for script in pro_soup.select("script[type='application/ld+json']") if "priceCurrency" in script.text][0].text)
    except:
        curr_script = None
        
    try:
        mpn_script = json.loads([script for script in pro_soup.select("script[type='application/ld+json']") if "mpn" in script.text][0].text)
    except:
        mpn_script = None
        
    try:
        brand = curr_script["@graph"][-1]["brand"]["name"]
    except:
        brand = None
        
    try:
        currency_str = curr_script["@graph"][-1]["offers"][-1]["priceCurrency"]
    except:
        currency_str = None
        
    try:
        currency_sym = pro_soup.select("span.woocommerce-Price-currencySymbol")[0].text
    except:
        currency_sym = None
        
    try:
        mpn = mpn_script["mpn"]
    except:
        mpn = None
        
    return currency_str , currency_sym , mpn , brand
    


def extract_form_data(form):
    """extracting data for variants for the same product using forms """
    
    try:
        availability = "InStock" if form["is_in_stock"] else "OutOfStock"
    except:
        availability = None
        
    try:
        sku = form["sku"]
    except:
        sku = None
        
    try:
        title = bs(form["variation_description"], "lxml").text.strip()
    except:
        title = None
        
    try: 
        offer_price = form["display_price"]
    except:
        offer_price = None
        
    try:
        orig_price= form["display_regular_price"] / 1000
    except:
        orig_price = None
        
    try:
        internal_id = form["variation_id"]
    except:
        internal_id = None
        
    try:
        size = list(form["attributes"].values())[0] #form["weight_html"]
        # if "n/d" in size.lower() :
        #     size = list(form["attributes"].values())[0]
    except:
        size = None
    
    
    data_dict = {'sku' : sku,
                'internal_id' : internal_id,
                'availability' : availability,
                'title' : title,
                'size' : size,
                'offer_price' : offer_price,
                'orig_price' : orig_price}
    
    return data_dict



def get_data_form_alternative(pro_soup):
    """ if there is only one variant for the product , no form data, we will get data from here"""
    
    try:
        new_form = json.loads(pro_soup.select("div[data-widget_type='wd_single_product_add_to_cart.default']")[0].select("input[name='gtm4wp_product_data']")[0].get("value"))
    except:
        new_form = None
        
    try:
        sku = new_form["sku"]

    except:
        try:
            sku = pro_soup.select("span[class='sku']")[0].text 
        except:
            sku = None
        
    try:
        internal_id = new_form["internal_id"]
    except:
        internal_id = None
        
    try:
        title = new_form["item_name"]
    except:
        try:
            title = pro_soup.select("h1.product_title.entry-title.wd-entities-title")[0].text
        except:
            title = None
        
    try:
        availability = "InStock" if "instock" in new_form["stockstatus"] else "OutOfStock"
    except:
        availability = None
        
    try:
        orig_price = new_form["price"] / 1000
    except:
        try:
            orig_price = pro_soup.select("p.price > span.woocommerce-Price-amount.amount")[0].select("bdi")[0].text.strip().replace("\xa0" , "")
        except:
            orig_price = None
    
    try:
        offer_price = orig_price
    except:
        offer_price = None
        
    try:
        size = pro_soup.select("div[data-id='pa_kilo-gramos']")[0].text
    except:
        try:
            size = pro_soup.select("tr.woocommerce-product-attributes-item.woocommerce-product-attributes-item--weight")[0].select("td.woocommerce-product-attributes-item__value")[0].text.strip("\n\t ")
        except:
            size = None
        
        
    data_dict = {'sku' : sku,
                'internal_id' : internal_id,
                'availability' : availability,
                'title' : title,
                'size' : size,
                'offer_price' : offer_price,
                'orig_price' : orig_price}
    
    return data_dict



def get_variants_data(pro_soup):
    """ get data from forms or not """
    
    try:
        forms = [json.loads(f.get("data-product_variations")) for f in pro_soup.select("div[data-widget_type='wd_single_product_add_to_cart.default'] > div > form[class*='variations_form']")][0]
        forms_data_list = [extract_form_data(form ) for form in forms]
        
    except:
        forms_data_list = [get_data_form_alternative(pro_soup)]
        
        
    return forms_data_list


def get_current_time():
    now_local = datetime.now()
    formatted_datetime = now_local.strftime('%Y-%m-%dT%H:%M:%SZ')

    return formatted_datetime

def get_products_parsed(pro_res):
    """parsing all the items and variations for this product """
    
    pro_soup = bs(pro_res.text , "lxml")
    
    
    try:
        brand_css = "tr.woocommerce-product-attributes-item.woocommerce-product-attributes-item--attribute_pa_brands > td.woocommerce-product-attributes-item__value > span.wd-attr-term > p"
        brand_name_out = pro_soup.select(brand_css)[0].text
    except:
        brand_name_out = None
    
        
    currency_str , currency_sym , mpn , brand_name_script = get_currnency(pro_soup)
    
    if  brand_name_out != None:
        brand_name = brand_name_out
    else:
        brand_name = brand_name_script
        
    # ft
    try:
        bread_links = [{"url" : b.get("href") , "name" : b.text.strip(" \n\t") } for b in pro_soup.select("nav.woocommerce-breadcrumb > a")] + [{"name" : pro_soup.select("nav.woocommerce-breadcrumb > span")[-1].text.strip(" \n\t") }]
        breadcrumbs = str(bread_links).strip("[]")
    except:
        breadcrumbs = None
        
    
    # sometimes is not available
    try:
        short_desc = pro_soup.select("div.woocommerce-product-details__short-description")[0]
    except:
        short_desc = None
        
    try:
        long_desc = "\n".join([str(p) for p in pro_soup.select("div#tab-description > p")])
    except:
        long_desc = None 
    
    try:
        desc_text = bs(long_desc , "lxml")
    except:
        desc_text = None
        
    try:
        features = "\n".join([l.text for l in pro_soup.select("div.woocommerce-product-details__short-description > ul > li")])
    except:
        features = None
    
    
    try:
        all_images_raw = [{"url" : im} for im in list(set([im.get("src") for im in pro_soup.select("div[data-widget_type='wd_single_product_gallery.default']")[0].select("img")]))]
        all_images = str(all_images_raw).strip("[]")
    except:
        all_images = []
        
        
    try:
        main_image = pro_soup.select("img.zoomImg")[0].get("src")
    except:
        try:
            main_image = all_images_raw[0]
        except:
            main_image = ""
            
    try:
        short_desc_text = bs(short_desc.text , "lxml").text.replace("\xa0" , "").strip()
    except:
        short_desc_text = None

    forms_data_list = get_variants_data(pro_soup)
    variants = str([{"size" : item["size"] } for item in forms_data_list ]).strip("[]")
    
    needed_keys = ['key', 'additionalProperties', 'availability', 'brand', 'breadcrumbs', 'canonicalUrl', 'color', 'currency', 'currencyRaw', 'description', 'descriptionHtml', 'features', 'images', 'mainImage', 'metadata', 'mpn', 'name', 'price', 'regularPrice', 'size', 'sku', 'url', 'variants']
    
    products_list = []
    
    
    for item_data in forms_data_list:
        
        product = { k : "" for k in needed_keys}
        
        product['key'] = item_data["internal_id"]
        product['additionalProperties'] = str([{"name":"brands","value": brand_name },{"name":"sku","value": item_data["sku"].strip("\n\t ")}]).strip("[]") 
        product['availability'] = item_data["availability"]
        product['brand'] = brand_name
        product['breadcrumbs'] = breadcrumbs
        product['canonicalUrl'] = pro_res.url
        product['color'] = None
        product['currency'] = currency_str 
        product['currencyRaw'] = currency_sym
        product['description'] = short_desc_text
        product['descriptionHtml'] = str(short_desc)
        product['features'] = features
        product['images'] = all_images
        product['mainImage'] = main_image
        product['metadata'] = {"dateDownloaded" : get_current_time() }
        product['mpn'] = mpn
        product['name'] = item_data["title"]
        product['price'] = item_data["offer_price"]
        product['regularPrice'] = item_data["orig_price"]
        product['size'] = item_data["size"].strip("\n\t ")
        product['sku'] = item_data["sku"].strip("\n\t ")
        product['url'] = pro_res.url
        product['variants'] = variants
        
        products_list.append(product)
        
        
    return products_list

    # if not from form data
    # sku = pro_soup.select("span.sku_wrapper > span.sku")[0].text.strip()
    # available = "InStock" if "disponible" in pro_soup.select("p.stock.in-stock.wd-style-default")[0].text else "OutOfStock"
    # title = pro_soup.select("h1.product_title.entry-title.wd-entities-title")[0].text.strip()
    # orig_price = pro_soup.select("p.price > span.woocommerce-Price-amount.amount")[0].select("bdi")[0].text.strip().replace("\xa0" , "")
    # offer_proce = orig_price
    
    


class DidopetSpiderSpider(scrapy.Spider):
    name = 'didopet_spider'
    allowed_domains = ['www.didopet.com']
    # start_urls = ["https://didopet.com/categoria-producto/gato/comida-para-gato/page/1/?_pjax=.main-page-wrapper",
    #                 "https://didopet.com/categoria-producto/perro/comida-para-perro/page/1/?_pjax=.main-page-wrapper"]

    page_headers = {
        'accept': 'text/html, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'dnt': '1',
        'priority': 'u=1, i',
        # 'referer': 'https://didopet.com/categoria-producto/perro/comida-para-perro/',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'x-pjax': 'true',
        'x-pjax-container': '.main-page-wrapper',
        'x-requested-with': 'XMLHttpRequest',
    }

    pro_headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        main_urls = ["https://didopet.com/categoria-producto/gato/comida-para-gato/page/1/?_pjax=.main-page-wrapper",
                    "https://didopet.com/categoria-producto/perro/comida-para-perro/page/1/?_pjax=.main-page-wrapper"]

        
        for main_url in main_urls:
            print("&&&&&&&&&&&&&&&&&&&&&&")
            print(main_url)
            yield scrapy.Request(main_url , headers = self.page_headers , callback = self.parse)


    def parse(self, response):
        
        last_page_link = response.css("li > a[class='page-numbers']::attr('href')").getall()[-1]
        pages_count = int(last_page_link.strip("/").split("/")[-1])
        print(f"pages count = {pages_count}")

        for page_num in range(1 , pages_count + 1):
            page_link = response.url.replace("/?_pjax=.main-page-wrapper" , f"/page/{page_num}/?_pjax=.main-page-wrapper") 
            print(page_link)
            yield scrapy.Request( page_link , headers = self.page_headers , callback = self.scrape_page , dont_filter = True)


    def scrape_page(self , response):
        """getting the main page data response """
        print("hello page here ")
        pro_urls = response.css("a.product-image-link::attr('href')").getall()
        print("*********************************************")
        print(pro_urls)
        print("*********************************************")
        
        for pro_url in pro_urls:
            yield scrapy.Request(pro_url , headers = self.pro_headers ,callback = self.scrape_product , dont_filter = True)

    def scrape_product(self , response):
        """ getting the data of product """

        products = get_products_parsed(response)
        for product in products:
            yield product 




# scrapy crawl didopet_spider -o data_0.csv

        


