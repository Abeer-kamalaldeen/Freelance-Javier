import scrapy
import re
import os
import pandas as pd 
import json 
from datetime import datetime
from bs4 import BeautifulSoup as bs

def parse_item(item , brand):
    """parsing each item variation in the items provided for this product"""
    
    all_sub_dicts_data = []
        
    try:
        images = [im["imageUrl"] for im in item["images"]]
        images_str = str([{"url" : im} for im in images]).strip("[]")
    except:
        images = []
        images_str = ""
        
    try:
        main_image = {"url" : images[0]}
    except:
        main_image = ""
        
        
    try:
        ean_code = item["ean"]
    except:
        ean_code = ""
        
    try:
        item_id = item["itemId"]
    except:
        item_id = ""
        
    try:
        pro_id = item["referenceId"][0]["Value"]
    except:
        pro_id = ""
        
        
    try:
        name = item["nameComplete"]
    except:
        name = ""
        
    try:
        size = item["name"]
    except:
        size = ""
        
        
    for seller in item["sellers"]:
    
        try:
            availability = "InStock" if item["sellers"][0]["commertialOffer"]["IsAvailable"] else "OutOfStock"
        except:
            availability = ""
            
            
            
        try:
            orig_price = seller["commertialOffer"]['ListPrice'] / 1000
        except:
            orig_price = ""
            
        try:
            offer_price = seller["commertialOffer"]['Price'] / 1000
        except:
            offer_price = ""
            # if the offer priceis not there 
            offer_price = orig_price

        
        sub_data_dict = {"images" : images_str,
                        "mainImage" : main_image,
                        "mpn" : ean_code,
                        "key" : item_id,
                        "sku" : pro_id,
                        "name" : name,
                        "size" : size,
                        "availability" : availability,
                        "regularPrice" : orig_price,
                        "price" : offer_price,
                         "metadata" : {"dateDownloaded" : get_current_time() },
                        "additionalProperties" : str([{"name":"brands","value": brand },{"name":"sku","value": pro_id}]).strip("[]") }
        
        
        all_sub_dicts_data.append(sub_data_dict)
    
# dict_keys(['key', 'additionalProperties', 'availability', 'brand', 'breadcrumbs', 'canonicalUrl', 'color', 'currency', 'currencyRaw', 'description', 'descriptionHtml', 'features', 'images', 'mainImage', 'metadata', 'mpn', 'name', 'price', 'regularPrice', 'size', 'sku', 'url', 'variants'])
    
    return all_sub_dicts_data



def get_currency(main_res):
    
    try:
        currency_dict = json.loads([script for script in main_res.css("script[type='text/javascript']::text").get_all() if "urrency" in script][0].text.split("var localeInfo = ")[-1].strip(";"))["CurrencyLocale"]
        print("#############################")
        currency_sym = currency_dict["CurrencySymbol"]
        currency_str = currency_dict["ISOCurrencySymbol"]
    except:
        currency_sym = "$"
        currency_str = "COP"
        
    return currency_sym , currency_str


def get_current_time():
    now_local = datetime.now()
    formatted_datetime = now_local.strftime('%Y-%m-%dT%H:%M:%SZ')

    return formatted_datetime


def get_product_full_data(pro_soup , currency_sym , currency_str):
    
#     read the product API response as json file
    j_data = json.loads(pro_soup.text)
    d = j_data[0]

    product_final_data = []
    
    product = {}
    product = { k : "" for k in ['key', 'additionalProperties', 'availability', 'brand', 'breadcrumbs', 'canonicalUrl', 'color', 'currency', 'currencyRaw', 'description', 'descriptionHtml', 'features', 'images', 'mainImage', 'metadata', 'mpn', 'name', 'price', 'regularPrice', 'size', 'sku', 'url', 'variants']}
    
    
    try:
        product["key"] = d["productId"]
    except:
        product["key"] = ""
        
        
    try:
        brand = d["brand"]
    except:
        None
    
        
    try:
        product["features"] = d["metaTagDescription"]
    except:
        None
        
    
        
    try:
        product["availability"] = "InStock" if sum([s["commertialOffer"]["IsAvailable"] for s in d["items"][0]["sellers"]]) > 0 else "OutOfStock"
    except:
        None
    
    try:
        product["brand"] = {"name": d["brand"]}
    except:
        None
        
        
    try:
        product["canonicalUrl"] = d["link"]
        product["url"] =  d["link"]
    except:
        None
    
        
    try:
        product["name"] = d["productName"]
    except:
        None
        
    pro_title = product["name"]
    base_link = "https://www.puppis.com.co"
    try:
        breadcrumbs = str([{"name" : c.strip("/").split("/")[-1] , "url" : base_link + c}  for c in d["categories"]][::-1] + [{"name": pro_title}]).strip("[]")
        product["breadcrumbs"] = breadcrumbs
        print("&&&&&&&&&&&&")
        print(breadcrumbs)
    except:
        None
        
    try:
        product["variants"] = str([{"size" : item["name"] } for item in d["items"]]).strip("[]")
    except:
        product["variants"] = ""
        
    try:
        product["color"] = None
    except:
        None
        
        
    try:
        desc_html = "\n".join([d for d in d['Descripción']])
    except:
        desc_html = ""
        
    desc = bs(desc_html , "lxml").text
    
    product["currencyRaw"] = currency_sym
    product["currency"] =currency_str
    
    product["description"] = desc
    product["descriptionHtml"] = desc_html
    
    items = d["items"]
    
    for item in items:
        
        items_data = parse_item(item , brand) 
        
        for item_seller_data in items_data:
            item_seller_final_data = product | item_seller_data
            product_final_data.append(item_seller_final_data)
    
    return product_final_data



class PuppisSpiderSpider(scrapy.Spider):
    name = 'puppis_spider'
    allowed_domains = ['www.puppis.com.co']
    base_link = "https://www.puppis.com.co"

    headers = {
        'accept': 'text/html, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=1, i',
        'referer': 'https://www.puppis.com.co/perros/alimentos',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    currency_sym , currency_str = "" , ""

    def start_requests(self):
        """ scraping the main page to get pagination API link and number of products"""
        main_url = "https://www.puppis.com.co/perros/alimentos"

        yield scrapy.Request(main_url , headers = self.headers , callback = self.scrape_main_request)

    def scrape_main_request(self , response):
        """extracting the pages links and pages counts"""

        self.currency_sym , self.currency_str = get_currency(response)


        paging_link_text = response.css("div.vitrine.resultItemsWrapper > script[type='text/javascript']::text").get()
        paging_link = self.base_link + [t for t in re.findall(".load\('(.*?)'" , paging_link_text ) if "PageNumber=" in t][0]


        pro_count = int(response.css('span.resultado-busca-numero > span.value::text').get())
        pages_count = ( pro_count // 24 ) + 1

        pages_links = [paging_link + str(i+ 1) for i in range(pages_count )]

        for page_link in pages_links:
            print("------------------------------")
            print(page_link)

            yield scrapy.Request(page_link , headers = self.headers , callback = self.scrape_page , dont_filter = True)



    def scrape_page(self , response):
        """scraping the pages of products to get products API links"""

        pro_urls = response.css("div.productListInfo > a.productName::attr(href)").getall()
        print("++++++++++++++++++++++++++++++=")
        print(pro_urls)
        print("++++++++++++++++++++++++++++++=")


        API_pro_urls  = [p.replace("https://www.puppis.com.co" , "https://www.puppis.com.co/api/catalog_system/pub/products/search") for p in pro_urls]

        for pro_url in API_pro_urls:
            yield scrapy.Request(pro_url , headers = self.headers , callback = self.scrape_product, dont_filter = True)

        # print(pro_urls)

    def scrape_product(self , response):
        """scraping and parsing all products data"""

        products_data_list = get_product_full_data(response , self.currency_sym , self.currency_str)

        for item in products_data_list:
            yield  item

        
# scrapy crawl puppis_spider --nolog -o data_1.csv