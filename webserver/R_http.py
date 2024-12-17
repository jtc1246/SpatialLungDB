from myHttp import http
import json
from mySecrets import toHex


R_BASE_URL = 'http://127.0.0.1:9020'


def fov_multi(slide: str, sample: str, fov: int, genes: str, file_name: str) -> None:
    '''
    All be in the final format passed into R, should be pre-processed before
    '''
    json_data = {
        'f': 1,
        "p1": slide,
        "p2": sample,
        "p3": fov,
        "p4": genes,
        "p6": file_name
    }
    json_data = json.dumps(json_data, ensure_ascii=False)
    json_data = toHex(json_data)
    url = R_BASE_URL + '/' + json_data
    response = http(url, Timeout=3600000, Decode=False)
    if (response['status'] < 0):
        return (False, b'')
    if (response['code'] == 200):
        return (True, b'')
    if (response['code'] == 500):
        return (False, response['text'])
    return (False, b'')


def gene_expression(genes: str, cell_types: str, file_name: str) -> None:
    '''
    All be in the final format passed into R, should be pre-processed before
    '''
    json_data = {
        'f': 2,
        "p1": genes,
        "p2": cell_types,
        "p6": file_name
    }
    json_data = json.dumps(json_data, ensure_ascii=False)
    json_data = toHex(json_data)
    url = R_BASE_URL + '/' + json_data
    response = http(url, Timeout=3600000, Decode=False)
    if (response['status'] < 0):
        return (False, b'')
    if (response['code'] == 200):
        return (True, b'')
    if (response['code'] == 500):
        return (False, response['text'])
    return (False, b'')



if __name__ == '__main__':
    r = fov_multi('S7280.4', 'H06', 24, 'INS,TOP2A', 'test01.pdf')
    print(r)
    r2 = gene_expression('INS', '4:Endo,11:Basal', 'test03.pdf')
    print(r2)
