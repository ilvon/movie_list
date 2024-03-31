from lxml import etree
from datetime import date
import re

def update_Latest_Entry_header(idx, h4Tag):
    hyperlinked = h4Tag.find('.//a')
    header = h4Tag.find('.//a').text
    if header == '---':
        return h4Tag
    
    info = re.findall(r'#(\d+) (.*)', header)[0]   #(idx, name)
    if int(info[0]) > idx:
        hyperlinked.attrib['href'] = f'index.html#{int(info[0]) - 1}'
        hyperlinked.text = f'#{int(info[0]) - 1} {info[1]}'
    elif int(info[0]) == idx:
        hyperlinked.attrib['href'] = 'index.html'   
        hyperlinked.text = '---'
    
    return h4Tag


def remove_Entry(index: int):
    with open('./src/index.html', 'r', encoding='utf-8') as fsrc:
        rawhtml = fsrc.read()
        
    root = etree.HTML(rawhtml)
    tbody = root.xpath('.//tbody')[0] 

    remove_row = tbody.xpath(f'./tr[@id={index}]')[0]
    remove_row_name = remove_row.xpath("./td/a[not(./text()='TMDB')]/text()")[0]
    print(f"Removing #{index}: {remove_row_name}")
    tbody.remove(remove_row)
    
    div_info_text = root.xpath('./body/div[@class="container"]/h4')
    div_info_text[0].text = f"Last Update: {date.today().strftime('%d-%m-%Y')}"
    div_info_text[1] = update_Latest_Entry_header(index, div_info_text[1])
    div_info_text[2].text = f"Total Entries: {len(root.xpath('.//tbody/tr'))}"
    
    for i, row in enumerate(root.xpath('.//tbody/tr')[index:]):
        row.xpath('.//th')[0].text = str(i + index)
        row.attrib['id'] = str(i + index)
        
    with open('./src/index.html', 'wb') as fout:
        fout.write(etree.tostring(root, encoding='utf-8'))

    
if __name__ == '__main__':
    idx = int(input('Index of entry to be removed: '))
    remove_Entry(idx)