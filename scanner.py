import json
import os
import platform
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    # определяем метод `do_GET`
    def do_GET(self):
        # определяем длину запроса для функции чтения в переменную content. Без данной переменной функция чтения
        # будет выполнятся бесконечно
        length = int(self.headers['Content-Length'])
        # считываем в переменную content тело запроса
        content = self.rfile.read(length)
        # выводим код об успешном соединении
        self.send_response(200)
        # заголовок ответа, указываем тип контента html
        self.send_header('Content-type', 'text/html')
        # завершаем передачу заголовков и отправляем их для установления соединения
        self.end_headers()
        # в переменную path записываем адрес, введеный в запросе
        path = self.path
        # Проверяем есть ли в адресе запроса путь scan, если есть то проверяем доступные адреса в сети
        if path == "/scan":
            # оставляем нужную часть запроса. Очищаем запрос и разбиваем на подстроки по разделителю ','
            part = str(content).strip('b\'').replace('"', '').strip('{}').split(',')
            # выделяем адрес (target) из запроса
            ip_address = part[0].split(':')
            # выделяем количество хостов для проверки доступности (count)
            number_of_host = part[1].split(':')
            num_of_host = int(number_of_host[1])
            # выводим на экран информацию, данную по запросу
            message = "Сканируем в сети " + ip_address[1] + " данное количество хостов" + " --> " + number_of_host[1] + '\n'
            self.wfile.write(bytes(message, "utf8"))
            # проверяем доступность хостов в сети
            for host_num in range(num_of_host):
                scanned_ip = do_ping_sweep(ip_address[1], host_num)
                if scanned_ip is not None:
                    message = "Адрес: " + scanned_ip + " --> Доступен!"
                    self.wfile.write(bytes(message, "utf8"))
                else:
                    continue
        else:
            message = "Введен неправильный адрес. Для запроса GET нужно ввести /scan"
            self.wfile.write(bytes(message, "utf8"))

    # определяем метод `do_POST` 
    def do_POST(self):
        # определяем длину запроса для функции чтения в переменную content_lenght. Без данной переменной функция
        # чтения будет выполнятся бесконечно
        content_length = int(self.headers['Content-Length'])
        # считываем в переменную body тело запроса
        body = self.rfile.read(content_length)
        # выводим код об успешном соединении
        self.send_response(200)
        # заголовок ответа, указываем тип контента html
        self.send_header('Content-type', 'text/html')
        # завершаем передачу заголовков и отправляем их для установления соединения
        self.end_headers()
        # в переменную path записываем адрес, введеный в запросе
        path = self.path
        # Проверяем есть ли в адресе запроса путь sendhttp, если есть то выполняем запрос
        if path == "/sendhttp":
            # оставляем нужную часть запроса. Очищаем запрос и разбиваем на подстроки по разделителю ','
            part = str(body).strip('b\'').replace('"', '').replace(' ', '').strip('{}').split(',')
            # выделяем адрес (target) из запроса
            targets = part[2].split(':')
            target = "https://" + str(targets[1])
            # выделяем заголовки (header) из запроса
            header = part[0].split(':')
            # выделяем значение заголовка (header-value) из запроса
            header_value = part[1].split(':')
            method = part[3].split(':')
            # выполняем функцию с параметрами из тела запроса
            mes, code, head, text = sent_http_request(target, str(method[1]), str(header[1]), str(header_value[1]))
            # выводим пользователю HTTP ответ с результатами
            self.wfile.write(bytes(mes, "utf8"))
            self.wfile.write(bytes(code, "utf8"))
            self.wfile.write(bytes(head, "utf8"))
            self.wfile.write(bytes(text, "utf8"))
        else:
            message = "Введен неправильный адрес. Для запроса POST нужно ввести /sendhttp"
            self.wfile.write(bytes(message, "utf8"))


def do_ping_sweep(ip, num_of_host):  
    oper = platform.system()
    ip_parts = ip.split('.')
    # собираем подсеть адреса сканирования
    network_ip = ip_parts[0] + '.' + ip_parts[1] + '.' + ip_parts[2] + '.'
    # собираем адрес сканирования
    scanned_ip = network_ip + str(int(ip_parts[3]) + num_of_host)
    # блок проверки для операционной системы Windows
    if oper == "Windows":
         # отправка двух пингов до сканируемого адреса         
         response = os.popen(f'ping -n 2 {scanned_ip}')   
         res = response.readlines()
         # для корректной проверки в Windows нужна перекодировка вывода
         line = res[2].encode('cp1251').decode('cp866')  
         # проверяем, встречается ли в выводе слово TTL, если да, то хост доступен
         if line.count("TTL"):  
             return scanned_ip
    # блок проверки для операционной системы Linux
    elif oper == "Linux":  
         # отправка двух пингов до сканируемого адреса
         response = os.popen(f'ping -c 2 {scanned_ip}')   
         res = response.readlines()
         line = res[2]
         # проверяем, встречается ли в выводе слово ttl, если да, то хост доступен
         if line.count("ttl"):  
             return scanned_ip
    # блок проверки для остальных операционной системы
    else:  
         # отправка двух пингов до сканируемого адреса
         response = os.popen(f'ping -c 2 {scanned_ip}')  
         res = response.readlines()
         line = res[2]
         # проверяем, встречается ли в выводе слово ttl, если да, то хост доступен
         if line.count("ttl"):
             return scanned_ip


def sent_http_request(target, meth, head=None, head_value=None):  
    headers_dict = dict()
    # получаем словарь заголовков и значений для GET запроса
    headers_dict[head] = ':'.join(head_value)
    # проверка, если выбран метод GET отправляем запрос GET
    if meth == "GET":  
        response = requests.get(target, headers=headers_dict)
    # проверка если был введен метод POST, то отправляем запрос POST
    elif meth == "POST":
        response = requests.post(target, headers=headers_dict)
    # проверка ошибки ввода, если не был выбран метод GET или POST
    else:  
        message = "Выбран метод отличный от GET или POST. Программа завершена!"
        raise SystemExit(1)
    # разбираем результат запроса
    res_code = "Response status code:" + str(response.status_code) + "\n"
    res_head = "Response headers:" + str(json.dumps(dict(response.headers), indent=4, sort_keys=True)) + "\n"
    res_text = "Response content:\n" + str(response.text) + "\n"
    message = "Адрес запроса (URL):" + response.url + "\n"
    return message, res_code, res_head, res_text


httpd = HTTPServer(('0.0.0.0', 3000), SimpleHTTPRequestHandler)
httpd.serve_forever()
